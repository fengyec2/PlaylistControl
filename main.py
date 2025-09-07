import sys
import os
from safe_print import safe_print, init_console_encoding
from pathlib import Path

# 在最开始初始化编码
init_console_encoding()

from cli_parser import parse_arguments
from system_utils import check_and_install_dependencies, setup_signal_handlers
from process_manager import ProcessManager
from run_modes import RunModes
from export_manager import ExportManager
from interactive_mode import InteractiveMode
from config_manager import config
from media_monitor import monitor
from display_utils import display
from logger import logger

# 确保工作目录正确
if getattr(sys, 'frozen', False):
    # 打包后的exe，切换到exe所在目录
    exe_dir = Path(sys.executable).parent
    os.chdir(exe_dir)
    safe_print(f"🔧 调试：已切换工作目录到: {exe_dir}")
else:
    # 开发模式，切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    safe_print(f"🔧 调试：已切换工作目录到: {script_dir}")

safe_print(f"🔧 调试：当前工作目录: {os.getcwd()}")

def main():
    try:
        # 检查是否是守护进程工作模式（通过环境变量判断）
        if os.environ.get('MEDIA_TRACKER_DAEMON_WORKER') == '1':
            safe_print(f"🔧 检测到守护进程工作模式，PID: {os.getpid()}")
            
            # 这是子进程，运行守护进程工作模式
            if not check_and_install_dependencies():
                safe_print("❌ 依赖检查失败")
                sys.exit(1)
            
            safe_print(f"🔧 依赖检查通过")
            
            # 解析参数（可能没有 -d 参数）
            args = parse_arguments()
            
            # 设置显示选项
            if hasattr(args, 'no_emoji') and args.no_emoji:
                config.set("display.use_emoji", False)
            
            # 守护进程默认使用静默模式
            config.set("logging.level", "INFO")  # 暂时改为INFO以便调试
            
            interval = getattr(args, 'interval', None) or config.get_monitoring_interval()
            pid_file_path = os.environ.get('MEDIA_TRACKER_PID_FILE')
            
            safe_print(f"🔧 间隔={interval}, PID文件={pid_file_path}")
            
            if not pid_file_path:
                safe_print("❌ 守护进程工作模式：缺少PID文件路径")
                logger.error("守护进程工作模式：缺少PID文件路径")
                sys.exit(1)
            
            safe_print(f"🔧 创建RunModes实例")
            # 创建运行模式管理器并启动守护进程工作
            run_modes = RunModes(monitor)
            
            safe_print(f"🔧 调用daemon_worker")
            run_modes.daemon_worker(interval, pid_file_path)
            return
        
        # 正常的主进程流程
        args = parse_arguments()
        
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
        
        # 创建运行模式管理器
        run_modes = RunModes(monitor)
        
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
            safe_print(f"🔧 主进程准备启动守护进程")
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
