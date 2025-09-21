# database.py
import sqlite3
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
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
    def __init__(self):
        # 使用config的get_database_path()方法获取正确的数据库路径
        self.db_path = config.get_database_path()
        
        # 添加调试输出
        from utils.safe_print import safe_print
        debug_print(f"🔧 调试：数据库管理器使用路径: {self.db_path}")
        
        self.init_database()
        self._check_backup()
        
    def init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
             # 媒体历史表 - 添加删除状态字段
            cursor.execute('''
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
                    playback_status TEXT,
                    genre TEXT,
                    year INTEGER,
                    deletion_status TEXT DEFAULT NULL,  -- 新增：删除状态 (NULL/pending/deleted/failed)
                    deletion_attempted_at DATETIME DEFAULT NULL,  -- 新增：尝试删除时间
                    deletion_notes TEXT DEFAULT NULL,  -- 新增：删除备注
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 播放会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playback_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start DATETIME,
                    session_end DATETIME,
                    app_name TEXT,
                    tracks_played INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 配置表（用于存储数据库版本等）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 检查是否需要添加新字段到现有表
            self._migrate_database_if_needed(cursor)
            
            # 设置数据库版本
            cursor.execute('''
                INSERT OR REPLACE INTO db_config (key, value, updated_at)
                VALUES ('version', '1.1', ?)
            ''', (datetime.now().isoformat(),))
            
            conn.commit()
            conn.close()
            logger.info(f"数据库初始化完成: {self.db_path}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
            
    def _check_backup(self) -> None:
        """检查是否需要备份数据库"""
        if not config.get("database.auto_backup", True):
            return
            
        backup_interval = config.get("database.backup_interval_days", 7)
        
        # 使用可执行文件目录下的backups文件夹
        from utils.system_utils import get_executable_dir
        backup_dir = os.path.join(get_executable_dir(), "backups")
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # 查找最新的备份文件
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("media_history_") and f.endswith(".db")]
        
        if backup_files:
            backup_files.sort(reverse=True)
            latest_backup = os.path.join(backup_dir, backup_files[0])
            backup_time = datetime.fromtimestamp(os.path.getmtime(latest_backup))
            
            if datetime.now() - backup_time < timedelta(days=backup_interval):
                return  # 不需要备份
                
        # 创建备份
        self._create_backup()
        
    def _create_backup(self) -> None:
        """创建数据库备份"""
        try:
            # 使用可执行文件目录下的backups文件夹
            from utils.system_utils import get_executable_dir
            backup_dir = os.path.join(get_executable_dir(), "backups")
            
            # 确保备份目录存在
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"media_history_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_file)
            
            # 使用safe_print而不是logger
            from utils.safe_print import safe_print
            safe_print(f"💾 数据库备份已创建: {backup_file}")
            
            # 清理旧备份文件（可选）
            self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            from utils.safe_print import safe_print
            safe_print(f"❌ 创建数据库备份失败: {e}")

    def _cleanup_old_backups(self, backup_dir: str, keep_count: int = 10) -> None:
        """清理旧的备份文件，只保留最新的几个"""
        try:
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith("media_history_") and f.endswith(".db")]
            
            if len(backup_files) <= keep_count:
                return
                
            # 按修改时间排序，保留最新的文件
            backup_files_with_time = []
            for f in backup_files:
                file_path = os.path.join(backup_dir, f)
                mtime = os.path.getmtime(file_path)
                backup_files_with_time.append((mtime, f, file_path))
            
            # 按时间倒序排序
            backup_files_with_time.sort(reverse=True)
            
            # 删除多余的备份文件
            for _, filename, file_path in backup_files_with_time[keep_count:]:
                os.remove(file_path)
                from utils.safe_print import safe_print
                safe_print(f"🗑️ 已删除旧备份: {filename}")
                
        except Exception as e:
            from utils.safe_print import safe_print
            safe_print(f"⚠️ 清理旧备份文件失败: {e}")

            
    def save_media_info(self, media_info: Dict[str, Any]) -> bool:
        """保存媒体信息到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查重复记录
            threshold_minutes = config.get("monitoring.duplicate_threshold_minutes", 1)
            cursor.execute('''
                SELECT id FROM media_history 
                WHERE title = ? AND artist = ? AND app_name = ? AND 
                      ABS(julianday(?) - julianday(timestamp)) < ?
            ''', (
                media_info.get('title', ''),
                media_info.get('artist', ''),
                media_info.get('app_name', ''),
                datetime.now().isoformat(),
                threshold_minutes / (24 * 60)  # 转换为天数
            ))
            
            if cursor.fetchone() is None:  # 如果不存在重复记录
                cursor.execute('''
                    INSERT INTO media_history 
                    (title, artist, album, album_artist, track_number, app_name, app_id, 
                     timestamp, duration, position, playback_status, genre, year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    media_info.get('title', ''),
                    media_info.get('artist', ''),
                    media_info.get('album', ''),
                    media_info.get('album_artist', ''),
                    media_info.get('track_number', 0),
                    media_info.get('app_name', ''),
                    media_info.get('app_id', ''),
                    datetime.now().isoformat(),
                    media_info.get('duration', 0),
                    media_info.get('position', 0),
                    media_info.get('status', ''),
                    media_info.get('genre', ''),
                    media_info.get('year', 0)
                ))
                
                conn.commit()
                conn.close()
                logger.info(f"保存媒体信息: {media_info.get('title', 'Unknown')} - {media_info.get('artist', 'Unknown')}")
                return True
            else:
                conn.close()
                logger.debug("跳过重复记录")
                return False
                
        except Exception as e:
            logger.error(f"保存媒体信息失败: {e}")
            return False
            
    def save_session_info(self, start_time: datetime, end_time: datetime, app_name: str, tracks_count: int) -> None:
        """保存播放会话信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO playback_sessions (session_start, session_end, app_name, tracks_played)
                VALUES (?, ?, ?, ?)
            ''', (start_time.isoformat(), end_time.isoformat(), app_name, tracks_count))
            
            conn.commit()
            conn.close()
            logger.info(f"保存会话信息: {app_name}, {tracks_count} 首歌曲")
            
        except Exception as e:
            logger.error(f"保存会话信息失败: {e}")
            
    def get_recent_tracks(self, limit: int = None) -> List[Tuple]:
        """获取最近播放的歌曲"""
        if limit is None:
            limit = config.get("display.default_recent_limit", 10)
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, artist, album, album_artist, app_name, timestamp, 
                       duration, playback_status, genre, year, track_number
                FROM media_history 
                WHERE title != ''
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            records = cursor.fetchall()
            conn.close()
            return records
            
        except Exception as e:
            logger.error(f"获取最近播放记录失败: {e}")
            return []
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取播放统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # 基础统计
            cursor.execute('SELECT COUNT(*) FROM media_history WHERE title != ""')
            stats['total_plays'] = cursor.fetchone()[0]
            
            # 修改这里：使用子查询来计算不同歌曲数量
            cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT title, artist 
                    FROM media_history 
                    WHERE title != ""
                )
            ''')
            stats['unique_songs'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM playback_sessions')
            stats['total_sessions'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(tracks_played) FROM playback_sessions')
            stats['avg_tracks_per_session'] = cursor.fetchone()[0] or 0
            
            # 最常播放的歌曲
            cursor.execute('''
                SELECT title, artist, album, COUNT(*) as play_count 
                FROM media_history 
                WHERE title != ""
                GROUP BY title, artist 
                ORDER BY play_count DESC 
                LIMIT 10
            ''')
            stats['top_songs'] = cursor.fetchall()
            
            # 最常播放的艺术家
            cursor.execute('''
                SELECT artist, COUNT(*) as play_count 
                FROM media_history 
                WHERE artist != ""
                GROUP BY artist 
                ORDER BY play_count DESC 
                LIMIT 10
            ''')
            stats['top_artists'] = cursor.fetchall()
            
            # 最常使用的应用
            cursor.execute('''
                SELECT app_name, COUNT(*) as usage_count 
                FROM media_history 
                WHERE title != ""
                GROUP BY app_name 
                ORDER BY usage_count DESC
            ''')
            stats['top_apps'] = cursor.fetchall()
            
            # 最近7天的播放统计
            cursor.execute('''
                SELECT DATE(timestamp) as play_date, COUNT(*) as daily_count
                FROM media_history 
                WHERE title != "" AND datetime(timestamp) >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY play_date DESC
            ''')
            stats['daily_stats'] = cursor.fetchall()
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
            
    def export_data(self) -> Dict[str, Any]:
        """导出所有数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 导出播放历史
            cursor.execute('''
                SELECT title, artist, album, album_artist, track_number, app_name, 
                       timestamp, duration, position, playback_status, genre, year
                FROM media_history 
                WHERE title != ''
                ORDER BY timestamp DESC
            ''')
            tracks = cursor.fetchall()
            
            # 导出会话信息
            cursor.execute('''
                SELECT session_start, session_end, app_name, tracks_played
                FROM playback_sessions
                ORDER BY session_start DESC
            ''')
            sessions = cursor.fetchall()
            
            conn.close()
            
            export_data = {
                'export_info': {
                    'export_time': datetime.now().isoformat(),
                    'total_tracks': len(tracks),
                    'total_sessions': len(sessions)
                },
                'tracks': [
                    {
                        'title': track[0],
                        'artist': track[1],
                        'album': track[2],
                        'album_artist': track[3],
                        'track_number': track[4],
                        'app_name': track[5],
                        'timestamp': track[6],
                        'duration': track[7],
                        'position': track[8],
                        'playback_status': track[9],
                        'genre': track[10],
                        'year': track[11]
                    } for track in tracks
                ],
                'sessions': [
                    {
                        'start_time': session[0],
                        'end_time': session[1],
                        'app_name': session[2],
                        'tracks_played': session[3]
                    } for session in sessions
                ]
            }
            
            # 包含统计信息
            if config.get("export.include_statistics", True):
                export_data['statistics'] = self.get_statistics()
                
            return export_data
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return {}

    def _migrate_database_if_needed(self, cursor):
        """检查并迁移数据库结构"""
        try:
            # 检查是否已有删除状态字段
            cursor.execute("PRAGMA table_info(media_history)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'deletion_status' not in columns:
                cursor.execute('ALTER TABLE media_history ADD COLUMN deletion_status TEXT DEFAULT NULL')
                logger.info("添加 deletion_status 字段")
                
            if 'deletion_attempted_at' not in columns:
                cursor.execute('ALTER TABLE media_history ADD COLUMN deletion_attempted_at DATETIME DEFAULT NULL')
                logger.info("添加 deletion_attempted_at 字段")
                
            if 'deletion_notes' not in columns:
                cursor.execute('ALTER TABLE media_history ADD COLUMN deletion_notes TEXT DEFAULT NULL')
                logger.info("添加 deletion_notes 字段")
                
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")

    def get_recent_tracks_for_deletion(self, limit: int = None, app_filter: str = None) -> List[Dict[str, Any]]:
        """获取最近播放的歌曲，用于删除操作"""
        if limit is None:
            limit = config.get("display.default_recent_limit", 10)
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            where_clause = "WHERE title != '' AND title IS NOT NULL"
            params = []
            
            if app_filter:
                where_clause += " AND app_name = ?"
                params.append(app_filter)
            
            cursor.execute(f'''
                SELECT id, title, artist, album, app_name, timestamp, 
                    deletion_status, deletion_attempted_at, deletion_notes
                FROM media_history 
                {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', params + [limit])
            
            records = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            result = []
            for record in records:
                result.append({
                    'id': record[0],
                    'title': record[1],
                    'artist': record[2],
                    'album': record[3],
                    'app_name': record[4],
                    'timestamp': record[5],
                    'deletion_status': record[6],
                    'deletion_attempted_at': record[7],
                    'deletion_notes': record[8]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取最近播放记录失败: {e}")
            return []

    def mark_song_deletion_status(self, song_id: int, status: str, notes: str = None) -> bool:
        """标记歌曲的删除状态
        
        Args:
            song_id: 歌曲记录ID
            status: 删除状态 ('pending', 'deleted', 'failed')
            notes: 删除备注
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE media_history 
                SET deletion_status = ?, deletion_attempted_at = ?, deletion_notes = ?
                WHERE id = ?
            ''', (status, datetime.now().isoformat(), notes, song_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"更新歌曲删除状态: ID={song_id}, 状态={status}")
            return True
            
        except Exception as e:
            logger.error(f"更新删除状态失败: {e}")
            return False

    def get_deletion_statistics(self) -> Dict[str, Any]:
        """获取删除操作统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # 删除状态统计
            cursor.execute('''
                SELECT deletion_status, COUNT(*) as count
                FROM media_history 
                WHERE deletion_status IS NOT NULL
                GROUP BY deletion_status
            ''')
            deletion_stats = dict(cursor.fetchall())
            
            stats['deletion_counts'] = {
                'pending': deletion_stats.get('pending', 0),
                'deleted': deletion_stats.get('deleted', 0),
                'failed': deletion_stats.get('failed', 0),
                'total_attempted': sum(deletion_stats.values())
            }
            
            # 最近删除的歌曲
            cursor.execute('''
                SELECT title, artist, app_name, deletion_status, deletion_attempted_at
                FROM media_history 
                WHERE deletion_status IS NOT NULL
                ORDER BY deletion_attempted_at DESC
                LIMIT 10
            ''')
            stats['recent_deletions'] = cursor.fetchall()
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"获取删除统计失败: {e}")
            return {}

    def reset_deletion_status(self, song_ids: List[int] = None) -> bool:
        """重置删除状态（清除删除标记）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if song_ids:
                # 重置指定歌曲
                placeholders = ','.join('?' * len(song_ids))
                cursor.execute(f'''
                    UPDATE media_history 
                    SET deletion_status = NULL, deletion_attempted_at = NULL, deletion_notes = NULL
                    WHERE id IN ({placeholders})
                ''', song_ids)
            else:
                # 重置所有歌曲
                cursor.execute('''
                    UPDATE media_history 
                    SET deletion_status = NULL, deletion_attempted_at = NULL, deletion_notes = NULL
                    WHERE deletion_status IS NOT NULL
                ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"重置删除状态完成")
            return True
            
        except Exception as e:
            logger.error(f"重置删除状态失败: {e}")
            return False

# 全局数据库实例
db = DatabaseManager()
