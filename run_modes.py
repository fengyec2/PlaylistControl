import asyncio
import os
import sys
import time
from system_utils import get_pid_file_path, is_process_running
from process_manager import ProcessManager
from config_manager import config
from logger import logger

class RunModes:
    def __init__(self, monitor):
        self.monitor = monitor

    async def background_monitor(self, interval: int = None, silent: bool = False):
        """后台监控模式"""
        if interval is None:
            interval = config.get_monitoring_interval()
        
        if not silent:
            print(f"🎧 后台监控已启动，监控间隔: {interval}秒")
            print("💡 程序将在后台运行，按 Ctrl+C 停止")
            
        logger.info(f"后台监控启动，间隔: {interval}秒")
        
        try:
            await self.monitor.monitor_media(interval, silent_mode=silent)
        except KeyboardInterrupt:
            if not silent:
                print("\n后台监控已停止")
        except Exception as e:
            logger.error(f"后台监控异常: {e}")
            if not silent:
                print(f"❌ 监控过程中出错: {e}")

    def run_daemon_mode(self, interval: int = None, pid_file: str = None):
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
                if is_process_running(existing_pid):
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
        
        # 创建PID文件
        if not ProcessManager.create_pid_file(pid_file_path):
            print(f"❌ 创建PID文件失败: {pid_file_path}")
            return
        
        print(f"🚀 守护进程已启动 (PID: {os.getpid()})")
        print(f"💡 PID文件位置: {pid_file_path}")
        if getattr(sys, 'frozen', False):
            print(f"💡 使用 'MediaTracker.exe --stop' 停止程序")
        else:
            print(f"💡 使用 'python main.py --stop' 停止程序")
        
        logger.info("守护进程模式启动")
        
        try:
            # 在守护进程模式下运行监控
            asyncio.run(self.background_monitor(interval, silent=True))
        except KeyboardInterrupt:
            logger.info("守护进程收到中断信号")
        except Exception as e:
            logger.error(f"守护进程异常: {e}")
        finally:
            # 清理PID文件
            ProcessManager.cleanup_pid_file(pid_file_path)
