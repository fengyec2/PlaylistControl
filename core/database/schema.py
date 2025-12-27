"""
数据库表结构定义
"""
from datetime import datetime
from utils.logger import logger


class DatabaseSchema:
    """数据库表结构管理"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def create_tables(self) -> None:
        """创建所有必需的表"""
        self._create_media_history_table()
        self._create_playback_sessions_table()
        self._create_config_table()
        self._set_database_version()
        self._migrate_if_needed()
    
    def _create_media_history_table(self) -> None:
        """创建媒体历史表"""
        query = '''
            CREATE TABLE IF NOT EXISTS media_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                artist TEXT,
                album TEXT,
                album_artist TEXT,
                track_number INTEGER,
                app_name TEXT,
                app_id TEXT,
                timestamp DATETIME,
                duration INTEGER,
                position INTEGER,
                play_percentage INTEGER DEFAULT 0,
                playback_status TEXT,
                genre TEXT,
                year INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.connection.execute_update(query)
    
    def _create_playback_sessions_table(self) -> None:
        """创建播放会话表"""
        query = '''
            CREATE TABLE IF NOT EXISTS playback_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start DATETIME,
                session_end DATETIME,
                app_name TEXT,
                tracks_played INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.connection.execute_update(query)
    
    def _create_config_table(self) -> None:
        """创建配置表"""
        query = '''
            CREATE TABLE IF NOT EXISTS db_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.connection.execute_update(query)
    
    def _set_database_version(self) -> None:
        """设置数据库版本"""
        query = '''
            INSERT OR REPLACE INTO db_config (key, value, updated_at)
            VALUES ('version', '1.1', ?)
        '''
        self.connection.execute_update(query, (datetime.now().isoformat(),))
    
    def _migrate_if_needed(self) -> None:
        """执行必要的数据库迁移"""
        try:
            # 检查 play_percentage 列是否存在
            with self.connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(media_history)")
                cols = [r[1] for r in cursor.fetchall()]
                
                if 'play_percentage' not in cols:
                    cursor.execute(
                        "ALTER TABLE media_history ADD COLUMN play_percentage INTEGER DEFAULT 0"
                    )
                    conn.commit()
                    logger.info("数据库迁移：已添加 play_percentage 列")
        except Exception as e:
            logger.warning(f"数据库迁移检查失败: {e}")