"""
数据导出功能
"""
from datetime import datetime
from typing import Dict, Any
from config.config_manager import config
from utils.logger import logger


class DataExporter:
    """数据导出器"""
    
    def __init__(self, connection, statistics_service):
        self.connection = connection
        self.statistics = statistics_service
    
    def export_all(self) -> Dict[str, Any]:
        """导出所有数据"""
        try:
            tracks = self._export_tracks()
            sessions = self._export_sessions()
            
            export_data = {
                'export_info': {
                    'export_time': datetime.now().isoformat(),
                    'total_tracks': len(tracks),
                    'total_sessions': len(sessions)
                },
                'tracks': tracks,
                'sessions': sessions
            }
            
            # 包含统计信息
            if config.get("export.include_statistics", True):
                export_data['statistics'] = self.statistics.get_all_statistics()
            
            return export_data
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return {}
    
    def _export_tracks(self) -> list:
        """导出播放历史"""
        query = '''
            SELECT title, artist, album, album_artist, track_number, app_name, 
                   timestamp, duration, position, play_percentage, playback_status, genre, year
            FROM media_history 
            WHERE title != ''
            ORDER BY timestamp DESC
        '''
        tracks = self.connection.execute_query(query)
        
        return [
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
                'play_percentage': track[9],
                'playback_status': track[10],
                'genre': track[11],
                'year': track[12]
            } for track in tracks
        ]
    
    def _export_sessions(self) -> list:
        """导出会话信息"""
        query = '''
            SELECT session_start, session_end, app_name, tracks_played
            FROM playback_sessions
            ORDER BY session_start DESC
        '''
        sessions = self.connection.execute_query(query)
        
        return [
            {
                'start_time': session[0],
                'end_time': session[1],
                'app_name': session[2],
                'tracks_played': session[3]
            } for session in sessions
        ]