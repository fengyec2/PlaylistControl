# logger.py
import logging
import logging.handlers
import os
from config.config_manager import config
from utils.safe_print import safe_print

class Logger:
    def __init__(self, name: str = "MediaTracker"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
        
    def _setup_logger(self) -> None:
        """设置日志记录器"""
        if not config.get("logging.enabled", True):
            self.logger.disabled = True
            return
            
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # 设置日志级别
        level = config.get("logging.level", "INFO")
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)  # 控制台只显示警告及以上
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 使用正确的路径
        self._setup_file_handler(formatter)
            
    def _setup_file_handler(self, formatter) -> None:
        """设置文件处理器"""
        try:
            # 获取日志文件的完整路径
            log_file = self._get_log_file_path()
            
            # 确保日志文件所在目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            max_size = config.get("logging.max_size_mb", 10) * 1024 * 1024  # MB to bytes
            backup_count = config.get("logging.backup_count", 3)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_size, backupCount=backup_count, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            safe_print(f"📝 日志文件设置完成: {log_file}")
            
        except Exception as e:
            safe_print(f"⚠️ 无法设置日志文件: {e}")
    
    def _get_log_file_path(self) -> str:
        """获取日志文件的完整路径"""
        log_file = config.get("logging.file", "media_tracker.log")
        
        # 如果配置中的路径是绝对路径，直接使用
        if os.path.isabs(log_file):
            return log_file
        
        # 如果是相对路径，则相对于可执行文件目录
        from utils.system_utils import get_executable_dir
        return os.path.join(get_executable_dir(), log_file)
        
    def info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(message)
        
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(message)
        
    def error(self, message: str) -> None:
        """记录错误日志"""
        self.logger.error(message)
        
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(message)
    
    def get_log_file_path(self) -> str:
        """公开方法：获取当前日志文件路径"""
        return self._get_log_file_path()

# 全局日志实例
logger = Logger()
