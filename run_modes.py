import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from system_utils import get_pid_file_path, is_process_running
from process_manager import ProcessManager
from config_manager import config
from logger import logger
from safe_print import safe_print

class RunModes:
    def __init__(self, monitor):
        self.monitor = monitor

    async def background_monitor(self, interval: int = None, silent: bool = False):
        """后台监控模式"""
        if interval is None:
            interval = config.get_monitoring_interval()
        
        if not silent:
            safe_print(f"🎧 后台监控已启动，监控间隔: {interval}秒")
            safe_print("💡 程序将在后台运行，按 Ctrl+C 停止")
            
        logger.info(f"后台监控启动，间隔: {interval}秒")
        
        try:
            await self.monitor.monitor_media(interval, silent_mode=silent)
        except KeyboardInterrupt:
            if not silent:
                safe_print("\n后台监控已停止")
        except Exception as e:
            logger.error(f"后台监控异常: {e}")
            if not silent:
                safe_print(f"❌ 监控过程中出错: {e}")

    def run_daemon_mode(self, interval: int = None, pid_file: str = None):
        """守护进程模式"""
        if interval is None:
            interval = config.get_monitoring_interval()
    
        pid_file_path = get_pid_file_path(pid_file)
        
        safe_print(f"🔧 调试：PID文件路径: {pid_file_path}")
    
        # 检查是否已有实例在运行
        if os.path.exists(pid_file_path):
            try:
                with open(pid_file_path, 'r') as f:
                    existing_pid = int(f.read().strip())
                if is_process_running(existing_pid):
                    safe_print(f"❌ 已有实例在运行 (PID: {existing_pid})")
                    return
                else:
                    os.remove(pid_file_path)
                    safe_print(f"🔧 调试：删除了旧的PID文件")
            except Exception as e:
                safe_print(f"🔧 调试：处理旧PID文件时出错: {e}")
                try:
                    os.remove(pid_file_path)
                except:
                    pass
    
        # 构建启动命令 - 不再传递 -d 参数给子进程！
        if getattr(sys, 'frozen', False):
            # 打包后的exe文件
            cmd = [sys.executable]
            safe_print(f"🔧 调试：打包模式，可执行文件: {sys.executable}")
        else:
            # Python脚本
            main_script = Path(__file__).parent / 'main.py'
            cmd = [sys.executable, str(main_script)]
            safe_print(f"🔧 调试：脚本模式，Python: {sys.executable}, 脚本: {main_script}")
        
        # 注意：不添加 -d 参数，因为子进程通过环境变量识别
        # 只添加间隔参数
        cmd.extend(['-i', str(interval)])
        
        # 如果有自定义PID文件路径
        if pid_file:
            cmd.extend(['--pid-file', pid_file])
        
        safe_print(f"🔧 启动命令: {' '.join(cmd)}")
    
        # 设置环境变量标识这是子进程
        env = os.environ.copy()
        env['MEDIA_TRACKER_DAEMON_WORKER'] = '1'
        env['MEDIA_TRACKER_PID_FILE'] = pid_file_path
        
        safe_print(f"🔧 调试：设置环境变量 MEDIA_TRACKER_DAEMON_WORKER=1")
        safe_print(f"🔧 调试：设置环境变量 MEDIA_TRACKER_PID_FILE={pid_file_path}")
    
        # 创建临时日志文件用于调试
        debug_log = os.path.join(os.path.dirname(pid_file_path), 'daemon_debug.log')
        
        try:
            if sys.platform == 'win32':
                # Windows下启动无窗口进程
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # 为了调试，暂时将stderr重定向到文件，使用正确的编码
                with open(debug_log, 'w', encoding='utf-8', errors='replace') as debug_file:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=debug_file,
                        stderr=debug_file,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                        env=env
                    )
            else:
                # Linux/Mac下的守护进程
                with open(debug_log, 'w', encoding='utf-8', errors='replace') as debug_file:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=debug_file,
                        stderr=debug_file,
                        preexec_fn=os.setsid,
                        env=env
                    )
            
            safe_print(f"🔧 调试：进程已启动，PID: {process.pid}")
            safe_print(f"🔧 调试：调试日志文件: {debug_log}")
            
            # 等待更长时间检查进程状态
            time.sleep(3)
            return_code = process.poll()
            
            if return_code is not None:
                safe_print(f"❌ 守护进程启动失败，退出码: {return_code}")
                # 读取调试日志，使用多种编码尝试
                try:
                    debug_content = None
                    for encoding in ['utf-8', 'gbk', 'cp1252', 'latin1']:
                        try:
                            with open(debug_log, 'r', encoding=encoding, errors='replace') as f:
                                debug_content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if debug_content and debug_content.strip():
                        safe_print(f"📋 调试信息:\n{debug_content}")
                    else:
                        safe_print("📋 调试日志为空或无法读取")
                        
                except Exception as e:
                    safe_print(f"🔧 无法读取调试日志: {e}")
                return
            else:
                safe_print(f"🚀 守护进程已启动 (PID: {process.pid})")
                safe_print(f"💡 PID文件位置: {pid_file_path}")
                safe_print(f"💡 调试日志: {debug_log}")
                
                # 写入PID文件
                with open(pid_file_path, 'w') as f:
                    f.write(str(process.pid))
                    
        except Exception as e:
            safe_print(f"❌ 启动守护进程失败: {e}")
            import traceback
            traceback.print_exc()
            return

    def daemon_worker(self, interval: int, pid_file_path: str):
        """守护进程工作函数"""
        try:
            safe_print(f"🔧 守护进程工作开始，PID: {os.getpid()}")
            
            # 确保PID文件存在且正确
            with open(pid_file_path, 'w') as f:
                f.write(str(os.getpid()))
            
            safe_print(f"🔧 PID文件已写入: {pid_file_path}")
            
            logger.info(f"守护进程工作模式启动，PID: {os.getpid()}")
            
            safe_print(f"🔧 准备启动后台监控，间隔: {interval}秒")
            asyncio.run(self.background_monitor(interval, silent=True))
            
        except Exception as e:
            safe_print(f"❌ 守护进程工作异常: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"守护进程工作异常: {e}")
            sys.exit(1)
        finally:
            safe_print(f"🔧 守护进程工作结束，清理PID文件")
            # 清理PID文件
            try:
                if os.path.exists(pid_file_path):
                    os.remove(pid_file_path)
            except Exception as e:
                safe_print(f"🔧 清理PID文件失败: {e}")
