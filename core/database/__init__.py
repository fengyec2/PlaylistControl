
"""
数据库模块 - 统一对外接口
"""
from .connection import DatabaseConnection
from .repository import MediaRepository, SessionRepository
from .statistics import StatisticsService
from .backup import BackupManager
from .exporter import DataExporter
from .schema import DatabaseSchema
from config.config_manager import config
from utils.logger import logger

# 全局变量控制调试输出
_verbose_mode = False

def set_verbose_mode(verbose: bool):
    """设置详细输出模式"""
    global _verbose_mode
    _verbose_mode = verbose

def debug_print(message):
    """只在 verbose 模式下打印调试信息"""
    if _verbose_mode:
        from utils.safe_print import safe_print
        safe_print(message)


class DatabaseManager:
    """数据库管理器 - 整合各个子模块"""
    
    def __init__(self):
        # 获取数据库路径
        self.db_path = config.get_database_path()
        debug_print(f"🔧 调试：数据库管理器使用路径: {self.db_path}")
        
        # 初始化各个子模块
        self.connection = DatabaseConnection(self.db_path)
        self.schema = DatabaseSchema(self.connection)
        self.backup_manager = BackupManager(self.db_path)
        self.media_repo = MediaRepository(self.connection)
        self.session_repo = SessionRepository(self.connection)
        self.statistics = StatisticsService(self.connection)
        self.exporter = DataExporter(self.connection, self.statistics)
        
        # 初始化数据库
        self.init_database()
        self.backup_manager.check_and_backup()
    
    def init_database(self) -> None:
        """初始化数据库"""
        try:
            self.schema.create_tables()
            logger.info(f"数据库初始化完成: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    # ========== 媒体信息相关方法 ==========
    
    def save_media_info(self, media_info: dict) -> bool:
        """保存媒体信息"""
        return self.media_repo.save(media_info)
    
    def update_media_progress(self, media_info: dict) -> bool:
        """更新播放进度"""
        return self.media_repo.update_progress(media_info)
    
    def get_recent_tracks(self, limit: int = None) -> list:
        """获取最近播放的歌曲"""
        if limit is None:
            limit = config.get("display.default_recent_limit", 10)
        return self.media_repo.get_recent(limit)
    
    def get_track_history(self, title: str, artist: str = '', limit: int = 5) -> list:
        """获取指定歌曲的历史记录"""
        return self.media_repo.get_track_history(title, artist, limit)
    
    # ========== 会话相关方法 ==========
    
    def save_session_info(self, start_time, end_time, app_name: str, tracks_count: int) -> None:
        """保存播放会话信息"""
        self.session_repo.save(start_time, end_time, app_name, tracks_count)
    
    # ========== 统计相关方法 ==========
    
    def get_statistics(self) -> dict:
        """获取播放统计"""
        return self.statistics.get_all_statistics()
    
    # ========== 导出相关方法 ==========
    
    def export_data(self) -> dict:
        """导出所有数据"""
        return self.exporter.export_all()


# 全局数据库实例
db = DatabaseManager()