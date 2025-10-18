import sys
import os
from utils.safe_print import safe_print, init_console_encoding

# 设置环境变量强制使用UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 重新配置标准输入输出流
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 在最开始初始化编码
init_console_encoding()

def main():
    try:
        # 导入 AppLauncher
        from interface.app_launcher import AppLauncher
        
        # 创建应用启动器
        app_launcher = AppLauncher()
        
        # 检查是否是守护进程工作模式
        if app_launcher.is_daemon_worker_mode():
            app_launcher.handle_daemon_worker_mode()
            return
        
        # 正常的主进程流程
        # 1. 环境初始化
        app_launcher.setup_environment()
        
        # 2. 处理各种命令
        if app_launcher.handle_commands():
            return  # 命令已处理，退出
        
        # 3. 启动对应的运行模式
        app_launcher.launch_mode()
        
    except Exception as e:
        # 如果 AppLauncher 还没创建，使用简单的错误处理
        if 'app_launcher' in locals():
            app_launcher.handle_error(e)
        else:
            safe_print(f"❌ 应用启动异常: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()
