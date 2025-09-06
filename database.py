# database.py
import sqlite3
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from config_manager import config
from logger import logger

class DatabaseManager:
    def __init__(self):
        self.db_path = config.get("database.path", "media_history.db")
        self.init_database()
        self._check_backup()
        
    def init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 媒体历史表
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
            
            # 设置数据库版本
            cursor.execute('''
                INSERT OR REPLACE INTO db_config (key, value, updated_at)
                VALUES ('version', '1.0', ?)
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
        backup_dir = "backups"
        
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
            backup_dir = "backups"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"media_history_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"数据库备份已创建: {backup_file}")
            
        except Exception as e:
            logger.error(f"创建数据库备份失败: {e}")
            
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

# 全局数据库实例
db = DatabaseManager()
