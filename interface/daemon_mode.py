# interface/daemon_mode.py (整合 run_modes.py 的守护进程逻辑)
import os
import sys
import subprocess
import time
from pathlib import Path
from utils.system_utils import get_pid_file_path, is_process_running
from utils.safe_print import safe_print
from utils.logger import logger
from config.config_manager import config

class DaemonMode:
    def __init__(self, monitor):
        self.monitor = monitor
        self.verbose = False
    
    def set_verbose(self, verbose):
        self.verbose = verbose
    
    def debug_print(self, message):
        if self.verbose:
            safe_print(message)
    
    def run_daemon(self, interval=None, pid_file=None):
        """守护进程模式（主进程启动逻辑）- 整合自 run_modes.py"""
        if interval is None:
            interval = config.get_monitoring_interval()

        pid_file_path = get_pid_file_path(pid_file)
        
        self.debug_print(f"🔧 调试：当前工作目录: {os.getcwd()}")
        self.debug_print(f"🔧 调试：PID文件路径: {pid_file_path}")

        # 检查是否已有实例在运行
        self._check_existing_instance(pid_file_path)
        
        # 构建启动命令
        cmd, work_dir = self._build_command(interval, pid_file)
        
        # 启动守护进程
        self._start_daemon_process(cmd, work_dir, pid_file_path)
    
    def run_daemon_worker(self, interval, pid_file_path):
        """守护进程工作模式（子进程）- 整合自 run_modes.py"""
        try:
            self.debug_print(f"🔧 守护进程工作开始，PID: {os.getpid()}")
            
            # 确保PID文件存在且正确
            with open(pid_file_path, 'w') as f:
                f.write(str(os.getpid()))
            
            self.debug_print(f"🔧 PID文件已写入: {pid_file_path}")
            logger.info(f"守护进程工作模式启动，PID: {os.getpid()}")
            
            # 使用 BackgroundMode 来执行实际的监控工作
            from interface.background_mode import BackgroundMode
            background_mode = BackgroundMode(self.monitor)
            
            self.debug_print(f"🔧 准备启动后台监控，间隔: {interval}秒")
            import asyncio
            asyncio.run(background_mode.run(interval, quiet=True))
            
        except Exception as e:
            safe_print(f"❌ 守护进程工作异常: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"守护进程工作异常: {e}")
            sys.exit(1)
        finally:
            self._cleanup(pid_file_path)
    
    def _check_existing_instance(self, pid_file_path):
        """检查是否已有实例在运行"""
        if os.path.exists(pid_file_path):
            try:
                with open(pid_file_path, 'r') as f:
                    existing_pid = int(f.read().strip())
                if is_process_running(existing_pid):
                    safe_print(f"❌ 已有实例在运行 (PID: {existing_pid})")
                    sys.exit(1)
                else:
                    os.remove(pid_file_path)
                    self.debug_print(f"🔧 调试：删除了旧的PID文件")
            except Exception as e:
                self.debug_print(f"🔧 调试：处理旧PID文件时出错: {e}")
                try:
                    os.remove(pid_file_path)
                except:
                    pass
    
    def _build_command(self, interval, pid_file):
        """构建启动命令"""
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable]
            work_dir = Path(sys.executable).parent
            self.debug_print(f"🔧 调试：打包模式，exe: {sys.executable}")
        else:
            main_script = Path(__file__).parent.parent / 'main.py'  # 调整路径
            python_exe = sys.executable
            if sys.platform == 'win32' and python_exe.endswith('python.exe'):
                pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                if os.path.exists(pythonw_exe):
                    python_exe = pythonw_exe
                    self.debug_print(f"🔧 调试：使用pythonw.exe避免显示终端")
            
            cmd = [python_exe, str(main_script)]
            work_dir = Path(__file__).parent.parent  # 调整路径
            self.debug_print(f"🔧 调试：脚本模式，Python: {python_exe}")
        
        cmd.extend(['-i', str(interval)])
        
        if self.verbose:
            cmd.append('-v')
        
        if pid_file:
            cmd.extend(['--pid-file', pid_file])
        
        self.debug_print(f"🔧 启动命令: {' '.join(cmd)}")
        self.debug_print(f"🔧 调试：工作目录将设为: {work_dir}")
        
        return cmd, work_dir
    
    def _start_daemon_process(self, cmd, work_dir, pid_file_path):
        """启动守护进程"""
        # 设置环境变量
        env = os.environ.copy()
        env['MEDIA_TRACKER_DAEMON_WORKER'] = '1'
        env['MEDIA_TRACKER_PID_FILE'] = pid_file_path
        
        self.debug_print(f"🔧 调试：设置环境变量 MEDIA_TRACKER_DAEMON_WORKER=1")
        self.debug_print(f"🔧 调试：设置环境变量 MEDIA_TRACKER_PID_FILE={pid_file_path}")

        # 创建调试日志文件
        debug_log = work_dir / 'daemon_debug.log'
        
        try:
            if sys.platform == 'win32':
                process = self._start_windows_process(cmd, env, work_dir, debug_log)
            else:
                process = self._start_unix_process(cmd, env, work_dir, debug_log)
            
            self._wait_and_check_process(process, debug_log, pid_file_path)
                    
        except Exception as e:
            safe_print(f"❌ 启动守护进程失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _start_windows_process(self, cmd, env, work_dir, debug_log):
        """Windows平台启动进程"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        with open(debug_log, 'w', encoding='utf-8', errors='replace') as debug_file:
            return subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=debug_file,
                stderr=debug_file,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                env=env,
                cwd=str(work_dir)
            )
    
    def _start_unix_process(self, cmd, env, work_dir, debug_log):
        """Unix平台启动进程"""
        with open(debug_log, 'w', encoding='utf-8', errors='replace') as debug_file:
            return subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=debug_file,
                stderr=debug_file,
                preexec_fn=os.setsid,
                env=env,
                cwd=str(work_dir)
            )
    
    def _wait_and_check_process(self, process, debug_log, pid_file_path):
        """等待并检查进程状态"""
        self.debug_print(f"🔧 调试：进程已启动，PID: {process.pid}")
        
        # 等待检查进程状态
        time.sleep(3)
        return_code = process.poll()
        
        if return_code is not None:
            self._handle_startup_failure(return_code, debug_log)
        else:
            self._handle_startup_success(process, pid_file_path)
    
    def _handle_startup_failure(self, return_code, debug_log):
        """处理启动失败"""
        safe_print(f"❌ 守护进程启动失败，退出码: {return_code}")
        try:
            debug_content = self._read_debug_log(debug_log)
            if debug_content and debug_content.strip():
                safe_print(f"📋 调试信息:\n{debug_content}")
            else:
                safe_print("📋 调试日志为空或无法读取")
        except Exception as e:
            safe_print(f"🔧 无法读取调试日志: {e}")
        sys.exit(1)
    
    def _handle_startup_success(self, process, pid_file_path):
        """处理启动成功"""
        work_dir = Path(pid_file_path).parent
        safe_print(f"🚀 守护进程已启动 (PID: {process.pid})")
        safe_print(f"💡 PID文件位置: {pid_file_path}")
        safe_print(f"💡 配置和数据文件将保存在: {work_dir}")
        safe_print(f"💡 使用 'python main.py --stop' 停止守护进程")
        
        # 写入PID文件
        with open(pid_file_path, 'w') as f:
            f.write(str(process.pid))
        
        safe_print("✅ 守护进程启动成功，主进程即将退出")
        
        # Windows特殊处理
        if sys.platform == 'win32':
            self._close_console_window()
        
        sys.exit(0)
    
    def _read_debug_log(self, debug_log):
        """读取调试日志"""
        for encoding in ['utf-8', 'gbk', 'cp1252', 'latin1']:
            try:
                with open(debug_log, 'r', encoding=encoding, errors='replace') as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    
    def _close_console_window(self):
        """Windows平台关闭控制台窗口"""
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
        except:
            pass
    
    def _cleanup(self, pid_file_path):
        """清理PID文件"""
        self.debug_print(f"🔧 守护进程工作结束，清理PID文件")
        try:
            if os.path.exists(pid_file_path):
                os.remove(pid_file_path)
        except Exception as e:
            self.debug_print(f"🔧 清理PID文件失败: {e}")
