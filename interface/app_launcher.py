# interface/app_launcher.py
import sys
import os
from pathlib import Path
from utils.safe_print import safe_print
from interface.cli_parser import parse_arguments
from utils.system_utils import check_and_install_dependencies, setup_signal_handlers
from core.process_manager import ProcessManager
from utils.export_manager import ExportManager
from interface.interactive_mode import InteractiveMode
from interface.background_mode import BackgroundMode
from interface.daemon_mode import DaemonMode
from config.config_manager import config
from core.media_monitor import monitor
from utils.display_utils import display
from utils.logger import logger


class AppLauncher:
    def __init__(self):
        self.args = None
        self.verbose = False
    
    def debug_print(self, message):
        """只在 verbose 模式下打印调试信息"""
        if self.verbose:
            safe_print(message)
    
    def setup_environment(self):
        """环境初始化和配置设置"""
        # 解析命令行参数
        self.args = parse_arguments()
        self.verbose = getattr(self.args, 'verbose', False)
        
        # 设置所有模块的 verbose 模式
        from utils.system_utils import set_verbose_mode as set_system_verbose
        from config.config_manager import set_verbose_mode as set_config_verbose
        set_system_verbose(self.verbose)
        set_config_verbose(self.verbose)
        
        # 设置工作目录
        self._setup_working_directory()
        
        # 设置显示和日志选项
        self._setup_display_and_logging()
    
    def _setup_working_directory(self):
        """设置正确的工作目录"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe，切换到exe所在目录
            exe_dir = Path(sys.executable).parent
            os.chdir(exe_dir)
            self.debug_print(f"🔧 调试：已切换工作目录到: {exe_dir}")
        else:
            # 开发模式，切换到脚本所在目录
            script_dir = Path(__file__).parent.parent  # 回到项目根目录
            os.chdir(script_dir)
            self.debug_print(f"🔧 调试：已切换工作目录到: {script_dir}")
        
        self.debug_print(f"🔧 调试：当前工作目录: {os.getcwd()}")
    
    def _setup_display_and_logging(self):
        """设置显示选项和日志级别"""
        # 设置显示选项
        if hasattr(self.args, 'no_emoji') and self.args.no_emoji:
            config.set("display.use_emoji", False)
        
        # 设置日志级别
        if self.verbose:
            config.set("logging.level", "DEBUG")
        elif hasattr(self.args, 'quiet') and self.args.quiet:
            config.set("logging.level", "WARNING")
    
    def _setup_environment_for_daemon(self):
        """为守护进程工作模式设置简化的环境"""
        # 设置工作目录
        self._setup_working_directory()
        
        # 设置verbose模式到各个模块
        from utils.system_utils import set_verbose_mode as set_system_verbose
        from config.config_manager import set_verbose_mode as set_config_verbose
        set_system_verbose(self.verbose)
        set_config_verbose(self.verbose)
        
        # 设置日志级别
        if self.verbose:
            config.set("logging.level", "DEBUG")
    
    def is_daemon_worker_mode(self):
        """检查是否是守护进程工作模式"""
        return os.environ.get('MEDIA_TRACKER_DAEMON_WORKER') == '1'
    
    def handle_daemon_worker_mode(self):
        """处理守护进程工作模式"""
        # 先解析参数以获取 verbose 设置
        self.args = parse_arguments()
        self.verbose = getattr(self.args, 'verbose', False)
        
        # 设置环境（复用现有逻辑）
        self._setup_environment_for_daemon()
        
        # 获取运行参数
        interval = getattr(self.args, 'interval', None) or config.get_monitoring_interval()
        pid_file_path = os.environ.get('MEDIA_TRACKER_PID_FILE')
        
        if not pid_file_path:
            safe_print("❌ 守护进程工作模式：缺少PID文件路径")
            logger.error("守护进程工作模式：缺少PID文件路径")
            sys.exit(1)
        
        # 创建并运行守护进程工作模式
        daemon_mode = DaemonMode(monitor)
        daemon_mode.set_verbose(self.verbose)
        daemon_mode.run_daemon_worker(interval, pid_file_path)
    
    def handle_commands(self):
        """处理各种命令，返回True表示命令已处理并应该退出"""
        # 处理停止命令
        if self.args.stop:
            ProcessManager.stop_background_process(self.args.pid_file)
            return True
        
        # 检查依赖（对于需要monitor的命令）
        if not check_and_install_dependencies():
            return True
        
        # 显示最近播放
        if self.args.recent is not None:
            display.show_recent_tracks(self.args.recent)
            return True
        
        # 显示统计信息
        if self.args.stats:
            display.show_statistics()
            return True
        
        # 导出历史记录
        if self.args.export:
            ExportManager.export_to_file(self.args.export)
            return True
        
        return False
    
    def launch_mode(self):
        """启动对应的运行模式"""
        # 守护进程模式
        if self.args.daemon:
            daemon_mode = DaemonMode(monitor)
            daemon_mode.set_verbose(self.verbose)
            setup_signal_handlers(monitor)
            daemon_mode.run_daemon(self.args.interval, self.args.pid_file)
            return
        
        # 后台监控模式
        if self.args.background:
            background_mode = BackgroundMode(monitor)
            setup_signal_handlers(monitor)
            try:
                import asyncio
                asyncio.run(background_mode.run(self.args.interval, self.args.quiet))
            except KeyboardInterrupt:
                safe_print("\n后台监控已停止")
            return
        
        # 默认交互模式
        interactive = InteractiveMode(monitor)
        interactive.run()
    
    def handle_error(self, error):
        """统一错误处理"""
        safe_print(f"❌ 应用启动异常: {error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
