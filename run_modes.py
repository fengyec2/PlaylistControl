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
        
        safe_print(f"🔧 调试：当前工作目录: {os.getcwd()}")
        safe_print(f"🔧 调试：PID文件路径: {pid_file_path}")

        # 检查是否已有实例在运行
        if os.path.exists(pid_file_path):
            try:
                with open(pid_file_path, 'r') as f:
                    existing_pid = int(f.read().strip())
                if is_process_running(existing_pid):
                    safe_print(f"❌ 已有实例在运行 (PID: {existing_pid})")
                    sys.exit(1)
                else:
                    os.remove(pid_file_path)
                    safe_print(f"🔧 调试：删除了旧的PID文件")
            except Exception as e:
                safe_print(f"🔧 调试：处理旧PID文件时出错: {e}")
                try:
                    os.remove(pid_file_path)
                except:
                    pass

        # 构建启动命令
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable]
            # 确保工作目录
            work_dir = Path(sys.executable).parent
            safe_print(f"🔧 调试：打包模式，exe: {sys.executable}")
            safe_print(f"🔧 调试：工作目录将设为: {work_dir}")
        else:
            main_script = Path(__file__).parent / 'main.py'
            python_exe = sys.executable
            if sys.platform == 'win32' and python_exe.endswith('python.exe'):
                pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                if os.path.exists(pythonw_exe):
                    python_exe = pythonw_exe
                    safe_print(f"🔧 调试：使用pythonw.exe避免显示终端")
            
            cmd = [python_exe, str(main_script)]
            work_dir = Path(__file__).parent
            safe_print(f"🔧 调试：脚本模式，Python: {python_exe}")
            safe_print(f"🔧 调试：工作目录将设为: {work_dir}")
        
        cmd.extend(['-i', str(interval)])
        
        if pid_file:
            cmd.extend(['--pid-file', pid_file])
        
        safe_print(f"🔧 启动命令: {' '.join(cmd)}")

        # 设置环境变量
        env = os.environ.copy()
        env['MEDIA_TRACKER_DAEMON_WORKER'] = '1'
        env['MEDIA_TRACKER_PID_FILE'] = pid_file_path
        
        safe_print(f"🔧 调试：设置环境变量 MEDIA_TRACKER_DAEMON_WORKER=1")
        safe_print(f"🔧 调试：设置环境变量 MEDIA_TRACKER_PID_FILE={pid_file_path}")

        # 创建调试日志文件
        debug_log = work_dir / 'daemon_debug.log'
        
        try:
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                with open(debug_log, 'w', encoding='utf-8', errors='replace') as debug_file:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=debug_file,
                        stderr=debug_file,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                        env=env,
                        cwd=str(work_dir)  # 重要：设置工作目录
                    )
            else:
                with open(debug_log, 'w', encoding='utf-8', errors='replace') as debug_file:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=debug_file,
                        stderr=debug_file,
                        preexec_fn=os.setsid,
                        env=env,
                        cwd=str(work_dir)  # 重要：设置工作目录
                    )
            
            safe_print(f"🔧 调试：进程已启动，PID: {process.pid}")
            safe_print(f"🔧 调试：工作目录: {work_dir}")
            safe_print(f"🔧 调试：调试日志文件: {debug_log}")
            
            # 等待检查进程状态
            time.sleep(3)
            return_code = process.poll()
            
            if return_code is not None:
                safe_print(f"❌ 守护进程启动失败，退出码: {return_code}")
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
                
                sys.exit(1)
            else:
                safe_print(f"🚀 守护进程已启动 (PID: {process.pid})")
                safe_print(f"💡 PID文件位置: {pid_file_path}")
                safe_print(f"💡 配置和数据文件将保存在: {work_dir}")
                safe_print(f"💡 使用 'python main.py --stop' 停止守护进程")
                
                # 写入PID文件
                with open(pid_file_path, 'w') as f:
                    f.write(str(process.pid))
                
                safe_print("✅ 守护进程启动成功，主进程即将退出")
                
                # Windows特殊处理：强制关闭当前控制台窗口
                if sys.platform == 'win32':
                    try:
                        import ctypes
                        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                        if hwnd != 0:
                            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
                    except:
                        pass
                
                sys.exit(0)
                    
        except Exception as e:
            safe_print(f"❌ 启动守护进程失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)



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
