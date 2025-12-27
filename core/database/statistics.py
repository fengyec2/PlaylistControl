"""
统计分析服务
"""
from typing import Dict, Any, List
import re
from utils.logger import logger


class StatisticsService:
    """统计分析服务"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        try:
            stats = {}
            stats.update(self._get_basic_stats())
            stats.update(self._get_top_songs())
            stats.update(self._get_top_artists())
            stats.update(self._get_top_apps())
            stats.update(self._get_time_based_stats())
            stats.update(self._get_duration_stats())
            stats.update(self._get_genre_stats())
            stats.update(self._get_album_stats())
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def _get_basic_stats(self) -> Dict[str, Any]:
        """获取基础统计"""
        stats = {}
        
        # 总播放次数
        result = self.connection.execute_single(
            'SELECT COUNT(*) FROM media_history WHERE title != ""'
        )
        stats['total_plays'] = result[0] if result else 0
        
        # 不同歌曲数量
        result = self.connection.execute_single('''
            SELECT COUNT(*) FROM (
                SELECT DISTINCT title, artist 
                FROM media_history 
                WHERE title != ""
            )
        ''')
        stats['unique_songs'] = result[0] if result else 0
        
        # 会话统计
        result = self.connection.execute_single('SELECT COUNT(*) FROM playback_sessions')
        stats['total_sessions'] = result[0] if result else 0
        
        result = self.connection.execute_single('SELECT AVG(tracks_played) FROM playback_sessions')
        stats['avg_tracks_per_session'] = result[0] if result else 0
        
        # 完成播放次数
        result = self.connection.execute_single('''
            SELECT COUNT(*) FROM media_history 
            WHERE title != "" AND playback_status IN ('completed', 'ended')
        ''')
        stats['completed_play_count'] = result[0] if result else 0
        
        return stats
    
    def _get_top_songs(self) -> Dict[str, Any]:
        """获取最常播放的歌曲"""
        query = '''
            SELECT title, artist, album, COUNT(*) as play_count 
            FROM media_history 
            WHERE title != ""
            GROUP BY title, artist 
            ORDER BY play_count DESC 
            LIMIT 10
        '''
        return {'top_songs': self.connection.execute_query(query)}
    
    def _get_top_artists(self) -> Dict[str, Any]:
        """获取最常播放的艺术家"""
        # 获取所有不同的艺术家记录
        query = '''
            SELECT DISTINCT artist
            FROM media_history 
            WHERE artist != "" AND artist IS NOT NULL
        '''
        unique_artists = [row[0] for row in self.connection.execute_query(query)]
        
        # 统计每个艺术家的播放次数
        artist_counts = {}
        
        for artist_string in unique_artists:
            individual_artists = self._parse_artists(artist_string)
            
            count_query = '''
                SELECT COUNT(*) 
                FROM media_history 
                WHERE artist = ? AND title != ""
            '''
            result = self.connection.execute_single(count_query, (artist_string,))
            count = result[0] if result else 0
            
            if len(individual_artists) <= 1:
                # 单艺术家
                artist_name = individual_artists[0] if individual_artists else artist_string
                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + count
            else:
                # 多艺术家
                for artist in individual_artists:
                    artist_counts[artist] = artist_counts.get(artist, 0) + count
        
        # 排序并取前10
        top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return {'top_artists': top_artists}
    
    def _get_top_apps(self) -> Dict[str, Any]:
        """获取最常使用的应用"""
        query = '''
            SELECT app_name, COUNT(*) as usage_count 
            FROM media_history 
            WHERE title != ""
            GROUP BY app_name 
            ORDER BY usage_count DESC
        '''
        return {'top_apps': self.connection.execute_query(query)}
    
    def _get_time_based_stats(self) -> Dict[str, Any]:
        """获取基于时间的统计"""
        stats = {}
        
        # 最近7天的每日统计
        daily_query = '''
            SELECT DATE(timestamp) as play_date, COUNT(*) as daily_count
            FROM media_history 
            WHERE title != "" AND datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY play_date DESC
        '''
        stats['daily_stats'] = self.connection.execute_query(daily_query)
        
        # 按小时统计
        hourly_query = '''
            SELECT 
                strftime('%H', timestamp) as hour, 
                COUNT(*) as count
            FROM media_history 
            WHERE title != "" 
            AND datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY hour 
            ORDER BY hour
        '''
        hourly_results = self.connection.execute_query(hourly_query)
        stats['hourly_stats'] = [(int(h), c) for h, c in hourly_results]
        
        # 月度统计（近3个月）
        monthly_query = '''
            SELECT 
                strftime('%Y-%m', timestamp) as month, 
                COUNT(*) as count
            FROM media_history 
            WHERE title != "" 
            AND datetime(timestamp) >= datetime('now', '-90 days')
            GROUP BY month 
            ORDER BY month DESC
            LIMIT 3
        '''
        stats['monthly_stats'] = self.connection.execute_query(monthly_query)
        
        return stats
    
    def _get_duration_stats(self) -> Dict[str, Any]:
        """获取时长统计"""
        stats = {}
        
        # 总播放时长
        result = self.connection.execute_single('''
            SELECT SUM(duration) FROM media_history WHERE title != ""
        ''')
        total_duration = result[0] if result and result[0] else 0
        stats['total_duration_minutes'] = total_duration // 60 if total_duration > 0 else 0
        
        # 平均单曲时长
        result = self.connection.execute_single('''
            SELECT AVG(duration) FROM media_history WHERE title != ""
        ''')
        avg_duration = result[0] if result and result[0] else 0
        stats['avg_track_duration_minutes'] = avg_duration // 60 if avg_duration > 0 else 0
        
        return stats
    
    def _get_genre_stats(self) -> Dict[str, Any]:
        """获取流派统计"""
        query = '''
            SELECT genre, COUNT(*) as count 
            FROM media_history 
            WHERE genre != "" AND title != ""
            GROUP BY genre 
            ORDER BY count DESC
        '''
        results = self.connection.execute_query(query)
        return {'genre_distribution': dict(results)}
    
    def _get_album_stats(self) -> Dict[str, Any]:
        """获取专辑统计"""
        query = '''
            SELECT album, AVG(tracks_played) as avg_tracks 
            FROM (
                SELECT album, title, COUNT(*) as tracks_played 
                FROM media_history 
                WHERE album != "" AND title != ""
                GROUP BY album, title
            ) 
            GROUP BY album
            ORDER BY avg_tracks DESC
        '''
        results = self.connection.execute_query(query)
        return {'album_completion_stats': dict(results)}
    
    @staticmethod
    def _parse_artists(artist_string: str) -> List[str]:
        """解析包含多个艺术家的字符串"""
        if not artist_string or artist_string.strip() == "":
            return []
        
        separators = [
            r'\s*/\s*',
            r'\s*&\s*',
            r'\s*,\s*',
            r'\s+feat\.?\s+',
            r'\s+featuring\s+',
            r'\s+ft\.?\s+',
            r'\s+with\s+',
            r'\s*\+\s*',
            r'\s*x\s*',
        ]
        
        combined_pattern = '|'.join(f'({sep})' for sep in separators)
        artists = re.split(combined_pattern, artist_string, flags=re.IGNORECASE)
        
        cleaned_artists = []
        for artist in artists:
            if artist and not re.match(
                r'^\s*[/&,+x]|\bfeat\.?|\bfeaturing|\bft\.?|\bwith\s*$',
                artist.strip(),
                re.IGNORECASE
            ):
                cleaned_artist = artist.strip()
                if cleaned_artist:
                    cleaned_artists.append(cleaned_artist)
        
        return cleaned_artists