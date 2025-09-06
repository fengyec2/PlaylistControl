# main.py
import asyncio
import json
import os
import sys
import argparse
import signal
import threading
import time
import subprocess
from datetime import datetime
from config_manager import config
from database import db
from media_monitor import monitor
from display_utils import display
from logger import logger

def get_executable_dir():
    """获取可执行文件所在目录"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的可执行文件
        return os.path.dirname(sys.executable)
    else:
        # 普通 Python 脚本
        return os.path.dirname(os.path.abspath(__file__))

def get_pid_file_path(pid_file: str = None) -> str:
    """获取 PID 文件的完整路径"""
    if pid_file is None:
        pid_file = "media_tracker.pid"
    
    # 如果已经是绝对路径，直接返回
    if os.path.isabs(pid_file):
        return pid_file
    
    # 否则放在可执行文件目录下
    return os.path.join(get_executable_dir(), pid_file)

def check_and_install_dependencies() -> bool:
    """检查并安装依赖"""
    try:
        import winsdk.windows.media.control as wmc
        return True
    except ImportError:
        print("❌ 缺少必要的 winsdk 库")
        print("🔧 正在尝试自动安装...")
        
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "winsdk"])
            print("✅ winsdk 安装成功!")
            print("🔄 请重新运行程序")
            return False
        except Exception as e:
            print(f"❌ 自动安装失败: {e}")
            print("🛠️ 请手动执行: pip install winsdk")
            return False

def setup_signal_handlers():
    """设置信号处理器，用于优雅退出"""
    def signal_handler(signum, frame):
        print(f"\n接收到退出信号 ({signum})，正在优雅退出...")
        monitor.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def background_monitor(interval: int = None, silent: bool = False):
    """后台监控模式"""
    if interval is None:
        interval = config.get_monitoring_interval()
    
    if not silent:
        print(f"🎧 后台监控已启动，监控间隔: {interval}秒")
        print("💡 程序将在后台运行，按 Ctrl+C 停止")
        
    logger.info(f"后台监控启动，间隔: {interval}秒")
    
    try:
        await monitor.monitor_media(interval, silent_mode=silent)
    except KeyboardInterrupt:
        if not silent:
            print("\n后台监控已停止")
    except Exception as e:
        logger.error(f"后台监控异常: {e}")
        if not silent:
            print(f"❌ 监控过程中出错: {e}")

def _is_process_running(pid: int) -> bool:
    """检查进程是否正在运行"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return str(pid) in result.stdout
        else:
            # Unix-like系统
            os.kill(pid, 0)  # 发送信号0检查进程是否存在
            return True
    except (OSError, subprocess.SubprocessError):
        return False

def _terminate_process(pid: int) -> bool:
    """终止指定PID的进程"""
    try:
        if sys.platform == "win32":
            # 首先尝试正常终止
            result = subprocess.run(
                ['taskkill', '/PID', str(pid)],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                return True
            
            # 如果正常终止失败，尝试强制终止
            result = subprocess.run(
                ['taskkill', '/PID', str(pid), '/F'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        else:
            # Unix-like系统
            os.kill(pid, signal.SIGTERM)
            # 等待一下，如果进程还在运行就强制杀死
            time.sleep(2)
            try:
                os.kill(pid, 0)  # 检查进程是否还在
                os.kill(pid, signal.SIGKILL)  # 强制杀死
            except OSError:
                pass  # 进程已经停止
            return True
    except Exception as e:
        logger.error(f"终止进程失败: {e}")
        return False

def run_daemon_mode(interval: int = None, pid_file: str = None):
    """守护进程模式"""
    if interval is None:
        interval = config.get_monitoring_interval()
    
    # 获取完整的PID文件路径
    pid_file_path = get_pid_file_path(pid_file)
    
    # 检查是否已有实例在运行
    if os.path.exists(pid_file_path):
        try:
            with open(pid_file_path, 'r') as f:
                existing_pid = int(f.read().strip())
            if _is_process_running(existing_pid):
                print(f"❌ 已有实例在运行 (PID: {existing_pid})")
                print("💡 使用 --stop 参数停止现有实例")
                return
            else:
                # 清理无效的PID文件
                os.remove(pid_file_path)
        except Exception:
            # 如果读取失败，删除PID文件
            try:
                os.remove(pid_file_path)
            except:
                pass
    
    # 写入PID文件
    try:
        with open(pid_file_path, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"PID文件已创建: {pid_file_path}")
        print(f"🚀 守护进程已启动 (PID: {os.getpid()})")
        print(f"💡 PID文件位置: {pid_file_path}")
        if getattr(sys, 'frozen', False):
            print(f"💡 使用 'MediaTracker.exe --stop' 停止程序")
        else:
            print(f"💡 使用 'python main.py --stop' 停止程序")
    except Exception as e:
        logger.error(f"创建PID文件失败: {e}")
        print(f"❌ 创建PID文件失败: {e}")
        return
    
    logger.info("守护进程模式启动")
    
    try:
        # 在守护进程模式下运行监控
        asyncio.run(background_monitor(interval, silent=True))
    except KeyboardInterrupt:
        logger.info("守护进程收到中断信号")
    except Exception as e:
        logger.error(f"守护进程异常: {e}")
    finally:
        # 清理PID文件
        if os.path.exists(pid_file_path):
            try:
                os.remove(pid_file_path)
                logger.info(f"PID文件已删除: {pid_file_path}")
            except Exception as e:
                logger.error(f"删除PID文件失败: {e}")

def export_history() -> None:
    """导出播放历史"""
    default_filename = config.get("export.default_filename", "media_history.json")
    filename = input(f"💾 导出文件名 (默认{default_filename}): ").strip() or default_filename
    
    try:
        export_data = db.export_data()
        
        if not export_data:
            print("❌ 没有数据可导出")
            return
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        use_emoji = config.should_use_emoji()
        success_prefix = "✅ " if use_emoji else ""
        stats_prefix = "📊 " if use_emoji else ""
        
        print(f"{success_prefix}播放历史已导出到 {filename}")
        print(f"{stats_prefix}包含 {export_data['export_info']['total_tracks']} 条播放记录和 {export_data['export_info']['total_sessions']} 个播放会话")
        
        logger.info(f"导出播放历史到 {filename}")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        logger.error(f"导出失败: {e}")

def show_config_editor() -> None:
    """显示配置编辑器"""
    while True:
        print("\n⚙️ 配置编辑器:")
        print("1. 📊 显示当前配置")
        print("2. ⏱️ 修改监控间隔")
        print("3. 🎨 切换emoji显示")
        print("4. 📱 管理忽略的应用")
        print("5. 💾 保存配置")
        print("6. 🔙 返回主菜单")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == '1':
            print("\n当前配置:")
            print(json.dumps(config.config, ensure_ascii=False, indent=2))
            
        elif choice == '2':
            current = config.get("monitoring.default_interval", 5)
            new_interval = input(f"新的监控间隔 (当前: {current}秒): ").strip()
            try:
                interval = int(new_interval)
                if 1 <= interval <= 60:
                    config.set("monitoring.default_interval", interval)
                    print(f"✅ 监控间隔已设置为 {interval}秒")
                else:
                    print("❌ 间隔必须在1-60秒之间")
            except ValueError:
                print("❌ 请输入有效的数字")
                
        elif choice == '3':
            current = config.get("display.use_emoji", True)
            config.set("display.use_emoji", not current)
            status = "启用" if not current else "禁用"
            print(f"✅ Emoji显示已{status}")
            
        elif choice == '4':
            ignored_apps = config.get("apps.ignored_apps", [])
            print(f"\n当前忽略的应用: {ignored_apps}")
            
            action = input("添加(a)/删除(d)/清空(c)忽略列表: ").strip().lower()
            if action == 'a':
                app = input("输入要忽略的应用ID: ").strip()
                if app and app not in ignored_apps:
                    ignored_apps.append(app)
                    config.set("apps.ignored_apps", ignored_apps)
                    print(f"✅ 已添加 {app} 到忽略列表")
                    
            elif action == 'd':
                if ignored_apps:
                    app = input("输入要移除的应用ID: ").strip()
                    if app in ignored_apps:
                        ignored_apps.remove(app)
                        config.set("apps.ignored_apps", ignored_apps)
                        print(f"✅ 已从忽略列表移除 {app}")
                    else:
                        print("❌ 应用不在忽略列表中")
                else:
                    print("忽略列表为空")
                    
            elif action == 'c':
                config.set("apps.ignored_apps", [])
                print("✅ 忽略列表已清空")
                
        elif choice == '5':
            config.save_config()
            
        elif choice == '6':
            break
            
        else:
            print("❌ 无效的选择，请重试")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Windows 媒体播放记录器 v4.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python main.py                    # 交互模式
  python main.py -b                 # 后台监控模式
  python main.py -b -i 10           # 后台监控，10秒间隔
  python main.py -d                 # 守护进程模式
  python main.py -r 20              # 显示最近20首歌
  python main.py -s                 # 显示统计信息
  python main.py -e output.json     # 导出到指定文件
  python main.py --stop             # 停止后台运行的程序
        '''
    )
    
    # 运行模式参数
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-b', '--background', action='store_true',
                           help='后台监控模式')
    mode_group.add_argument('-d', '--daemon', action='store_true',
                           help='守护进程模式(静默后台运行)')
    mode_group.add_argument('-r', '--recent', type=int, metavar='N',
                           help='显示最近N首播放的歌曲')
    mode_group.add_argument('-s', '--stats', action='store_true',
                           help='显示播放统计信息')
    mode_group.add_argument('-e', '--export', type=str, metavar='FILE',
                           help='导出播放历史到指定文件')
    mode_group.add_argument('--stop', action='store_true',
                           help='停止后台运行的程序（自动查找PID文件）')
    
    # 监控参数
    parser.add_argument('-i', '--interval', type=int, metavar='SECONDS',
                       help='监控间隔(秒), 默认从配置文件读取')
    parser.add_argument('--pid-file', type=str, metavar='FILE',
                       help='PID文件路径(仅守护进程模式)')
    
    # 显示参数
    parser.add_argument('--no-emoji', action='store_true',
                       help='禁用emoji显示')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='静默模式，减少输出')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出模式')
    
    return parser.parse_args()

def stop_background_process(pid_file: str = None):
    """停止后台运行的程序"""
    # 获取可执行文件目录
    exe_dir = get_executable_dir()
    
    # 如果没有指定PID文件，尝试查找可能的PID文件
    if pid_file is None:
        possible_files = [
            "media_tracker.pid", 
            "media_monitor.pid", 
            "media_player_tracker.pid",
            "MediaTracker.pid"  # 添加可执行文件名对应的PID文件
        ]
        
        # 在可执行文件目录中查找
        found_file = None
        for file in possible_files:
            full_path = os.path.join(exe_dir, file)
            if os.path.exists(full_path):
                found_file = full_path
                break
        
        if found_file is None:
            print("❌ 未找到运行中的后台程序")
            print("💡 可能的原因：")
            print("   - 程序未在后台运行")
            print("   - PID文件被意外删除")
            print("   - 使用了不同的PID文件路径")
            print(f"💡 查找目录: {exe_dir}")
            print(f"💡 查找的文件: {', '.join(possible_files)}")
            
            # 显示当前目录的所有 .pid 文件
            try:
                pid_files = [f for f in os.listdir(exe_dir) if f.endswith('.pid')]
                if pid_files:
                    print(f"💡 发现的PID文件: {', '.join(pid_files)}")
                else:
                    print("💡 当前目录没有发现任何 .pid 文件")
            except Exception as e:
                print(f"💡 无法读取目录: {e}")
            
            # 尝试查找并终止所有MediaTracker进程
            if getattr(sys, 'frozen', False):
                print("💡 尝试查找MediaTracker进程...")
                try:
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq MediaTracker.exe'],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if 'MediaTracker.exe' in result.stdout:
                        print("💡 发现MediaTracker进程，尝试强制终止...")
                        subprocess.run(
                            ['taskkill', '/IM', 'MediaTracker.exe', '/F'],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        print("✅ 已强制终止所有MediaTracker进程")
                        return True
                    else:
                        print("💡 未发现MediaTracker进程")
                except Exception as e:
                    print(f"💡 查找进程时出错: {e}")
            
            return False
        
        pid_file_path = found_file
    else:
        pid_file_path = get_pid_file_path(pid_file)
    
    if not os.path.exists(pid_file_path):
        print(f"❌ PID文件不存在: {pid_file_path}")
        return False
    
    try:
        with open(pid_file_path, 'r') as f:
            pid_str = f.read().strip()
            
        if not pid_str:
            print("❌ PID文件为空")
            os.remove(pid_file_path)  # 清理空文件
            return False
            
        pid = int(pid_str)
        print(f"🔍 找到进程 PID: {pid}")
        
        # 检查进程是否存在
        if not _is_process_running(pid):
            print(f"❌ 进程 {pid} 已不存在，清理PID文件")
            os.remove(pid_file_path)
            return False
        
        print(f"🎯 正在终止进程 {pid}...")
        
        # 尝试终止进程
        success = _terminate_process(pid)
        
        if success:
            # 等待一下确保进程完全停止
            time.sleep(2)
            
            # 再次检查进程是否已停止
            if _is_process_running(pid):
                print(f"⚠️ 进程 {pid} 仍在运行，尝试强制终止...")
                if sys.platform == "win32":
                    subprocess.run(
                        ['taskkill', '/PID', str(pid), '/F', '/T'],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                time.sleep(1)
            
            # 删除PID文件
            if os.path.exists(pid_file_path):
                os.remove(pid_file_path)
            
            print(f"✅ 后台程序已停止 (PID: {pid})")
            logger.info(f"后台程序已停止: PID {pid}")
            return True
        else:
            print(f"❌ 无法停止进程 {pid}")
            return False
            
    except ValueError:
        print("❌ PID文件内容无效")
        return False
    except PermissionError:
        print("❌ 权限不足，无法停止进程")
        print("💡 请以管理员身份运行")
        return False
    except Exception as e:
        print(f"❌ 停止后台程序失败: {e}")
        logger.error(f"停止后台程序失败: {e}")
        return False

def main():
    args = parse_arguments()
    
    # 处理停止命令
    if args.stop:
        stop_background_process(args.pid_file)
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
    
    use_emoji = config.should_use_emoji()
    
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
        try:
            export_data = db.export_data()
            if not export_data:
                print("❌ 没有数据可导出")
                return
                
            with open(args.export, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            success_prefix = "✅ " if use_emoji else ""
            stats_prefix = "📊 " if use_emoji else ""
            
            print(f"{success_prefix}播放历史已导出到 {args.export}")
            print(f"{stats_prefix}包含 {export_data['export_info']['total_tracks']} 条播放记录")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
        return
    
    if args.daemon:
        # 守护进程模式
        setup_signal_handlers()
        run_daemon_mode(args.interval, args.pid_file)
        return
    
    if args.background:
        # 后台监控模式
        setup_signal_handlers()
        try:
            asyncio.run(background_monitor(args.interval, args.quiet))
        except KeyboardInterrupt:
            print("\n后台监控已停止")
        return
    
    # 交互模式
    title_prefix = "🎵 " if use_emoji else ""
    print(f"{title_prefix}Windows 媒体播放记录器 v4.0")
    print("=" * 50)
    
    feature_prefix = "🚀 " if use_emoji else ""
    support_prefix = "📱 " if use_emoji else ""
    save_prefix = "💾 " if use_emoji else ""
    
    print(f"{feature_prefix}使用 Windows Media Transport Controls API")
    print(f"{support_prefix}支持所有兼容的媒体应用")
    print(f"{save_prefix}自动保存播放历史和统计信息")
    
    logger.info("程序启动 - 交互模式")
    
    # 检查自动启动
    if config.get("monitoring.auto_start", False):
        print("\n🚀 自动启动监控...")
        try:
            asyncio.run(monitor.monitor_media())
        except Exception as e:
            logger.error(f"自动监控失败: {e}")
    
    while True:
        target_prefix = "🎯 " if use_emoji else ""
        print(f"\n{target_prefix}选择操作:")
        
        headphone_prefix = "🎧 " if use_emoji else ""
        list_prefix = "📋 " if use_emoji else ""
        chart_prefix = "📊 " if use_emoji else ""
        disk_prefix = "💾 " if use_emoji else ""
        gear_prefix = "⚙️ " if use_emoji else ""
        cross_prefix = "❌ " if use_emoji else ""
        
        print(f"1. {headphone_prefix}开始监控媒体播放")
        print(f"2. {list_prefix}查看最近播放记录")
        print(f"3. {chart_prefix}查看播放统计")
        print(f"4. {disk_prefix}导出播放历史")
        print(f"5. {gear_prefix}配置设置")
        print(f"6. {cross_prefix}退出")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == '1':
            try:
                current_interval = config.get_monitoring_interval()
                interval_input = input(f"⏱️ 监控间隔 (秒，当前默认{current_interval}): ").strip()
                
                if interval_input:
                    interval = int(interval_input)
                    min_interval = config.get("monitoring.min_interval", 1)
                    max_interval = config.get("monitoring.max_interval", 60)
                    
                    if interval < min_interval or interval > max_interval:
                        print(f"⚠️ 间隔必须在{min_interval}-{max_interval}秒之间，使用默认值{current_interval}秒")
                        interval = current_interval
                else:
                    interval = current_interval
                    
                asyncio.run(monitor.monitor_media(interval))
                
            except ValueError:
                print(f"⚠️ 无效的间隔时间，使用默认值{config.get_monitoring_interval()}秒")
                asyncio.run(monitor.monitor_media())
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                logger.error(f"监控出错: {e}")
                
        elif choice == '2':
            try:
                default_limit = config.get("display.default_recent_limit", 10)
                limit_input = input(f"📋 显示最近多少首歌 (默认{default_limit}): ").strip()
                
                if limit_input:
                    limit = int(limit_input)
                    if limit < 1:
                        limit = default_limit
                else:
                    limit = default_limit
                    
                display.show_recent_tracks(limit)
                
            except ValueError:
                display.show_recent_tracks()
                
        elif choice == '3':
            display.show_statistics()
            
        elif choice == '4':
            export_history()
            
        elif choice == '5':
            show_config_editor()
            
        elif choice == '6':
            wave_prefix = "👋 " if use_emoji else ""
            print(f"{wave_prefix}再见!")
            logger.info("程序退出")
            break
            
        else:
            print("❌ 无效的选择，请重试")

if __name__ == "__main__":
    main()
