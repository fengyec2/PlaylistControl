# logger.py
import logging
import logging.handlers
import os
from typing import Optional
from config_manager import config

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
        
        # 文件处理器
        log_file = config.get("logging.file", "media_tracker.log")
        max_size = config.get("logging.max_size_mb", 10) * 1024 * 1024  # MB to bytes
        backup_count = config.get("logging.backup_count", 3)
        
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_size, backupCount=backup_count, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️ 无法设置日志文件: {e}")
            
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

# 全局日志实例
logger = Logger()
