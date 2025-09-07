import os
import sys
import signal
import subprocess
import time
from logger import logger
from safe_print import safe_print

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
        safe_print("❌ 缺少必要的 winsdk 库")
        safe_print("🔧 正在尝试自动安装...")
        
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "winsdk"])
            safe_print("✅ winsdk 安装成功!")
            safe_print("🔄 请重新运行程序")
            return False
        except Exception as e:
            safe_print(f"❌ 自动安装失败: {e}")
            safe_print("🛠️ 请手动执行: pip install winsdk")
            return False

def setup_signal_handlers(monitor):
    """设置信号处理器，用于优雅退出"""
    def signal_handler(signum, frame):
        safe_print(f"\n接收到退出信号 ({signum})，正在优雅退出...")
        monitor.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def is_process_running(pid: int) -> bool:
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

def terminate_process(pid: int) -> bool:
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
