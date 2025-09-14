import sys
import os
from utils.safe_print import safe_print, init_console_encoding
from pathlib import Path

# 在最开始初始化编码
init_console_encoding()

from interface.cli_parser import parse_arguments
from utils.system_utils import check_and_install_dependencies, setup_signal_handlers
from core.process_manager import ProcessManager
from interface.run_modes import RunModes
from utils.export_manager import ExportManager
from interface.interactive_mode import InteractiveMode
from config.config_manager import config
from core.media_monitor import monitor
from utils.display_utils import display
from utils.logger import logger

def debug_print(message, verbose=False):
    """只在 verbose 模式下打印调试信息"""
    if verbose:
        safe_print(message)

def main():
    try:
        # 检查是否是守护进程工作模式（通过环境变量判断）
        if os.environ.get('MEDIA_TRACKER_DAEMON_WORKER') == '1':
            # 先解析参数以获取 verbose 设置
            args = parse_arguments()
            verbose = getattr(args, 'verbose', False)

            # 设置所有模块的 verbose 模式
            from utils.system_utils import set_verbose_mode as set_system_verbose
            from config.config_manager import set_verbose_mode as set_config_verbose
            set_system_verbose(verbose)
            set_config_verbose(verbose)
            
            debug_print(f"🔧 检测到守护进程工作模式，PID: {os.getpid()}", verbose)
            
            # 确保工作目录正确
            if getattr(sys, 'frozen', False):
                # 打包后的exe，切换到exe所在目录
                exe_dir = Path(sys.executable).parent
                os.chdir(exe_dir)
                debug_print(f"🔧 调试：已切换工作目录到: {exe_dir}", verbose)
            else:
                # 开发模式，切换到脚本所在目录
                script_dir = Path(__file__).parent
                os.chdir(script_dir)
                debug_print(f"🔧 调试：已切换工作目录到: {script_dir}", verbose)

            debug_print(f"🔧 调试：当前工作目录: {os.getcwd()}", verbose)
            
            # 这是子进程，运行守护进程工作模式
            if not check_and_install_dependencies():
                safe_print("❌ 依赖检查失败")
                sys.exit(1)
            
            debug_print(f"🔧 依赖检查通过", verbose)
            
            # 设置显示选项
            if hasattr(args, 'no_emoji') and args.no_emoji:
                config.set("display.use_emoji", False)
            
            # 设置日志级别
            if verbose:
                config.set("logging.level", "DEBUG")
            else:
                config.set("logging.level", "INFO")
            
            interval = getattr(args, 'interval', None) or config.get_monitoring_interval()
            pid_file_path = os.environ.get('MEDIA_TRACKER_PID_FILE')
            
            debug_print(f"🔧 间隔={interval}, PID文件={pid_file_path}", verbose)
            
            if not pid_file_path:
                safe_print("❌ 守护进程工作模式：缺少PID文件路径")
                logger.error("守护进程工作模式：缺少PID文件路径")
                sys.exit(1)
            
            debug_print(f"🔧 创建RunModes实例", verbose)
            # 创建运行模式管理器并启动守护进程工作
            run_modes = RunModes(monitor, verbose=verbose)
            
            debug_print(f"🔧 调用daemon_worker", verbose)
            run_modes.daemon_worker(interval, pid_file_path)
            return
        
        # 正常的主进程流程
        args = parse_arguments()
        verbose = getattr(args, 'verbose', False)

        # 设置所有模块的 verbose 模式
        from utils.system_utils import set_verbose_mode as set_system_verbose
        from config.config_manager import set_verbose_mode as set_config_verbose
        set_system_verbose(verbose)
        set_config_verbose(verbose)
        
        # 确保工作目录正确
        if getattr(sys, 'frozen', False):
            # 打包后的exe，切换到exe所在目录
            exe_dir = Path(sys.executable).parent
            os.chdir(exe_dir)
            debug_print(f"🔧 调试：已切换工作目录到: {exe_dir}", verbose)
        else:
            # 开发模式，切换到脚本所在目录
            script_dir = Path(__file__).parent
            os.chdir(script_dir)
            debug_print(f"🔧 调试：已切换工作目录到: {script_dir}", verbose)

        debug_print(f"🔧 调试：当前工作目录: {os.getcwd()}", verbose)
        
        # 处理停止命令
        if args.stop:
            ProcessManager.stop_background_process(args.pid_file)
            return
        
        if not check_and_install_dependencies():
            return
        
        # 设置显示选项
        if args.no_emoji:
            config.set("display.use_emoji", False)
        
        # 设置日志级别
        if args.verbose:
            config.set("logging.level", "DEBUG")
        elif args.quiet:
            config.set("logging.level", "WARNING")
        
        # 创建运行模式管理器（传递 verbose 参数）
        run_modes = RunModes(monitor, verbose=verbose)
        
        # 处理不同的运行模式
        if args.recent is not None:
            # 显示最近播放
            display.show_recent_tracks(args.recent)
            return
        
        if args.stats:
            # 显示统计信息
            display.show_statistics()
            return
        
        if args.export:
            # 导出历史记录
            ExportManager.export_to_file(args.export)
            return
        
        if args.daemon:
            # 守护进程模式 - 这是主进程，启动守护进程
            debug_print(f"🔧 主进程准备启动守护进程", verbose)
            setup_signal_handlers(monitor)
            run_modes.run_daemon_mode(args.interval, args.pid_file)
            return
        
        if args.background:
            # 后台监控模式
            setup_signal_handlers(monitor)
            try:
                import asyncio
                asyncio.run(run_modes.background_monitor(args.interval, args.quiet))
            except KeyboardInterrupt:
                safe_print("\n后台监控已停止")
            return
        
        # 交互模式
        interactive = InteractiveMode(monitor)
        interactive.run()
        
    except Exception as e:
        safe_print(f"❌ main函数异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()