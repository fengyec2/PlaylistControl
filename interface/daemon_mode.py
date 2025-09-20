# interface/daemon_mode.py
import os
import sys
import time
import signal
from pathlib import Path
from utils.safe_print import safe_print
from utils.logger import logger
from config.config_manager import config
from core.process_manager import ProcessManager

class DaemonMode:
    def __init__(self, monitor):
        self.monitor = monitor
        self.verbose = False
    
    def set_verbose(self, verbose):
        """设置详细输出模式"""
        self.verbose = verbose
    
    def debug_print(self, message):
        """只在 verbose 模式下打印调试信息"""
        if self.verbose:
            safe_print(message)
    
    def run_daemon(self, interval=None, pid_file=None):
        """启动守护进程模式（主进程）"""
        if interval is None:
            interval = config.get_monitoring_interval()
        
        if pid_file is None:
            pid_file = config.get("daemon.default_pid_file", "media_tracker.pid")
        
        self.debug_print(f"🔧 主进程准备启动守护进程")
        self.debug_print(f"⏱️ 监控间隔: {interval}秒")
        self.debug_print(f"📁 PID文件: {pid_file}")
        
        try:
            ProcessManager.start_background_process(
                interval=interval,
                pid_file=pid_file,
                verbose=self.verbose
            )
        except Exception as e:
            error_msg = f"启动守护进程失败: {e}"
            safe_print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise
    
    def run_daemon_worker(self, interval, pid_file_path):
        """守护进程工作模式（子进程）"""
        self.debug_print(f"🔧 守护进程工作模式启动，PID: {os.getpid()}")
        self.debug_print(f"⏱️ 监控间隔: {interval}秒")
        self.debug_print(f"📁 PID文件: {pid_file_path}")
        
        logger.info(f"守护进程工作模式启动，PID: {os.getpid()}, 间隔: {interval}秒")
        
        # 创建PID文件
        self._create_pid_file(pid_file_path)
        
        # 设置信号处理
        self._setup_signal_handlers(pid_file_path)
        
        try:
            # 开始监控循环
            self._monitoring_loop(interval)
        except Exception as e:
            error_msg = f"守护进程工作异常: {e}"
            logger.error(error_msg)
            self.debug_print(f"❌ {error_msg}")
            raise
        finally:
            self._cleanup(pid_file_path)
    
    def _create_pid_file(self, pid_file_path):
        """创建PID文件"""
        try:
            pid_file = Path(pid_file_path)
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            self.debug_print(f"✅ PID文件创建成功: {pid_file_path}")
            logger.info(f"PID文件创建: {pid_file_path}")
            
        except Exception as e:
            error_msg = f"创建PID文件失败: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _setup_signal_handlers(self, pid_file_path):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.debug_print(f"🛑 收到信号 {signal_name}，准备退出...")
            logger.info(f"收到信号 {signal_name}，守护进程准备退出")
            self._cleanup(pid_file_path)
            sys.exit(0)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Windows特有信号
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def _monitoring_loop(self, interval):
        """主监控循环"""
        self.debug_print("🔄 开始监控循环...")
        
        while True:
            try:
                # 执行一次监控检查
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(
                        self.monitor.check_media_once()
                    )
                finally:
                    loop.close()
                
                # 等待下一个检查周期
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.debug_print("🛑 监控循环被中断")
                break
            except Exception as e:
                error_msg = f"监控循环异常: {e}"
                logger.error(error_msg)
                self.debug_print(f"⚠️ {error_msg}")
                # 继续循环，不退出
                time.sleep(interval)
    
    def _cleanup(self, pid_file_path):
        """清理资源"""
        try:
            # 删除PID文件
            pid_file = Path(pid_file_path)
            if pid_file.exists():
                pid_file.unlink()
                self.debug_print(f"🗑️ PID文件已删除: {pid_file_path}")
                logger.info(f"PID文件已删除: {pid_file_path}")
        except Exception as e:
            logger.error(f"清理PID文件失败: {e}")
