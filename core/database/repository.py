"""
数据仓储层 - 负责数据的CRUD操作
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from utils.logger import logger


class MediaRepository:
    """媒体信息仓储"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def save(self, media_info: Dict[str, Any]) -> bool:
        """保存媒体信息"""
        try:
            duration = int(media_info.get('duration', 0) or 0)
            position = int(media_info.get('position', 0) or 0)
            play_percentage = self._calculate_percentage(duration, position)
            
            query = '''
                INSERT INTO media_history 
                (title, artist, album, album_artist, track_number, app_name, app_id, 
                 timestamp, duration, position, play_percentage, playback_status, genre, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                media_info.get('title', ''),
                media_info.get('artist', ''),
                media_info.get('album', ''),
                media_info.get('album_artist', ''),
                media_info.get('track_number', 0),
                media_info.get('app_name', ''),
                media_info.get('app_id', ''),
                datetime.now().isoformat(),
                duration,
                position,
                play_percentage,
                media_info.get('status', ''),
                media_info.get('genre', ''),
                media_info.get('year', 0)
            )
            
            self.connection.execute_update(query, params)
            logger.info(f"保存媒体信息: {media_info.get('title', 'Unknown')} - {media_info.get('artist', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"保存媒体信息失败: {e}")
            return False
    
    def update_progress(self, media_info: Dict[str, Any]) -> bool:
        """更新播放进度"""
        try:
            duration = int(media_info.get('duration', 0) or 0)
            position = int(media_info.get('position', 0) or 0)
            play_percentage = self._calculate_percentage(duration, position)
            
            # 查找最近的匹配记录
            find_query = '''
                SELECT id FROM media_history
                WHERE title = ? AND artist = ? AND app_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            '''
            find_params = (
                media_info.get('title', ''),
                media_info.get('artist', ''),
                media_info.get('app_name', '')
            )
            
            row = self.connection.execute_single(find_query, find_params)
            
            if row:
                # 更新现有记录
                record_id = row[0]
                update_query = '''
                    UPDATE media_history
                    SET position = ?, play_percentage = ?, playback_status = ?, timestamp = ?
                    WHERE id = ?
                '''
                update_params = (
                    position,
                    play_percentage,
                    media_info.get('status', ''),
                    datetime.now().isoformat(),
                    record_id
                )
                self.connection.execute_update(update_query, update_params)
                logger.debug(f"更新播放进度: {media_info.get('title','')} -> {play_percentage}%")
                return True
            else:
                # 没有找到记录，创建新记录
                return self.save(media_info)
                
        except Exception as e:
            logger.error(f"更新播放进度失败: {e}")
            return False
    
    def get_recent(self, limit: int) -> List[Tuple]:
        """获取最近播放的歌曲"""
        try:
            query = '''
                SELECT title, artist, album, album_artist, app_name, timestamp, 
                       duration, playback_status, genre, year, play_percentage, track_number
                FROM media_history 
                WHERE title != ''
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            return self.connection.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"获取最近播放记录失败: {e}")
            return []
    
    def get_track_history(self, title: str, artist: str = '', limit: int = 5) -> List[Tuple]:
        """获取指定歌曲的历史记录"""
        try:
            query = '''
                SELECT timestamp, play_percentage, playback_status, app_name
                FROM media_history
                WHERE title = ? AND (? = '' OR artist = ?)
                ORDER BY timestamp DESC
                LIMIT ?
            '''
            return self.connection.execute_query(query, (title, artist, artist, limit))
        except Exception as e:
            logger.error(f"查询歌曲历史失败: {e}")
            return []
    
    @staticmethod
    def _calculate_percentage(duration: int, position: int) -> int:
        """计算播放百分比"""
        if duration <= 0:
            return 0
        try:
            percentage = int((position / duration) * 100)
            return max(0, min(100, percentage))
        except Exception:
            return 0


class SessionRepository:
    """会话信息仓储"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def save(self, start_time: datetime, end_time: datetime, app_name: str, tracks_count: int) -> None:
        """保存播放会话"""
        try:
            query = '''
                INSERT INTO playback_sessions (session_start, session_end, app_name, tracks_played)
                VALUES (?, ?, ?, ?)
            '''
            params = (start_time.isoformat(), end_time.isoformat(), app_name, tracks_count)
            self.connection.execute_update(query, params)
            logger.info(f"保存会话信息: {app_name}, {tracks_count} 首歌曲")
        except Exception as e:
            logger.error(f"保存会话信息失败: {e}")