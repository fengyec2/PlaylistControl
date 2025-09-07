import os
import sys
import time
import subprocess
from system_utils import get_executable_dir, get_pid_file_path, is_process_running, terminate_process
from logger import logger
from safe_print import safe_print

class ProcessManager:
    @staticmethod
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
                safe_print("❌ 未找到运行中的后台程序")
                safe_print("💡 可能的原因：")
                safe_print("   - 程序未在后台运行")
                safe_print("   - PID文件被意外删除")
                safe_print("   - 使用了不同的PID文件路径")
                safe_print(f"💡 查找目录: {exe_dir}")
                safe_print(f"💡 查找的文件: {', '.join(possible_files)}")
                
                # 显示当前目录的所有 .pid 文件
                try:
                    pid_files = [f for f in os.listdir(exe_dir) if f.endswith('.pid')]
                    if pid_files:
                        safe_print(f"💡 发现的PID文件: {', '.join(pid_files)}")
                    else:
                        safe_print("💡 当前目录没有发现任何 .pid 文件")
                except Exception as e:
                    safe_print(f"💡 无法读取目录: {e}")
                
                # 尝试查找并终止所有MediaTracker进程
                if getattr(sys, 'frozen', False):
                    safe_print("💡 尝试查找MediaTracker进程...")
                    try:
                        result = subprocess.run(
                            ['tasklist', '/FI', 'IMAGENAME eq MediaTracker.exe'],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if 'MediaTracker.exe' in result.stdout:
                            safe_print("💡 发现MediaTracker进程，尝试强制终止...")
                            subprocess.run(
                                ['taskkill', '/IM', 'MediaTracker.exe', '/F'],
                                capture_output=True,
                                text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            safe_print("✅ 已强制终止所有MediaTracker进程")
                            return True
                        else:
                            safe_print("💡 未发现MediaTracker进程")
                    except Exception as e:
                        safe_print(f"💡 查找进程时出错: {e}")
                
                return False
            
            pid_file_path = found_file
        else:
            pid_file_path = get_pid_file_path(pid_file)
        
        if not os.path.exists(pid_file_path):
            safe_print(f"❌ PID文件不存在: {pid_file_path}")
            return False
        
        try:
            with open(pid_file_path, 'r') as f:
                pid_str = f.read().strip()
                
            if not pid_str:
                safe_print("❌ PID文件为空")
                os.remove(pid_file_path)  # 清理空文件
                return False
                
            pid = int(pid_str)
            safe_print(f"🔍 找到进程 PID: {pid}")
            
            # 检查进程是否存在
            if not is_process_running(pid):
                safe_print(f"❌ 进程 {pid} 已不存在，清理PID文件")
                os.remove(pid_file_path)
                return False
            
            safe_print(f"🎯 正在终止进程 {pid}...")
            
            # 尝试终止进程
            success = terminate_process(pid)
            
            if success:
                # 等待一下确保进程完全停止
                time.sleep(2)
                
                # 再次检查进程是否已停止
                if is_process_running(pid):
                    safe_print(f"⚠️ 进程 {pid} 仍在运行，尝试强制终止...")
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
                
                safe_print(f"✅ 后台程序已停止 (PID: {pid})")
                logger.info(f"后台程序已停止: PID {pid}")
                return True
            else:
                safe_print(f"❌ 无法停止进程 {pid}")
                return False
                
        except ValueError:
            safe_print("❌ PID文件内容无效")
            return False
        except PermissionError:
            safe_print("❌ 权限不足，无法停止进程")
            safe_print("💡 请以管理员身份运行")
            return False
        except Exception as e:
            safe_print(f"❌ 停止后台程序失败: {e}")
            logger.error(f"停止后台程序失败: {e}")
            return False

    @staticmethod
    def create_pid_file(pid_file_path: str) -> bool:
        """创建PID文件"""
        try:
            with open(pid_file_path, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"PID文件已创建: {pid_file_path}")
            return True
        except Exception as e:
            logger.error(f"创建PID文件失败: {e}")
            return False

    @staticmethod
    def cleanup_pid_file(pid_file_path: str):
        """清理PID文件"""
        if os.path.exists(pid_file_path):
            try:
                os.remove(pid_file_path)
                logger.info(f"PID文件已删除: {pid_file_path}")
            except Exception as e:
                logger.error(f"删除PID文件失败: {e}")
