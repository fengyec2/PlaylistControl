import sys
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

def main():
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
        # 守护进程模式
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
            print("\n后台监控已停止")
        return
    
    # 交互模式
    interactive = InteractiveMode(monitor)
    interactive.run()

if __name__ == "__main__":
    main()
