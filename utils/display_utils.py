# display_utils.py
from datetime import datetime
from config.config_manager import config
from core.database import db
from utils.safe_print import safe_print

class DisplayUtils:
    @staticmethod
    def show_recent_tracks(limit: int = None) -> None:
        """显示最近播放的歌曲"""
        if limit is None:
            limit = config.get("display.default_recent_limit", 10)
            
        records = db.get_recent_tracks(limit)
        
        if not records:
            safe_print("暂无播放记录")
            return
            
        use_emoji = config.should_use_emoji()
        timestamp_format = config.get_timestamp_format()
        
        title_prefix = "📋 " if use_emoji else ""
        safe_print(f"\n{title_prefix}最近 {len(records)} 首歌曲:")
        safe_print("=" * 80)
        
        for i, record in enumerate(records, 1):
            title, artist, album, album_artist, app_name, timestamp, duration, status, genre, year, track_number = record
            dt = datetime.fromisoformat(timestamp)
            
            song_prefix = "🎵 " if use_emoji else ""
            safe_print(f"{i:2d}. {song_prefix}{title}")
            
            if artist:
                artist_prefix = "🎤 " if use_emoji else ""
                safe_print(f"     {artist_prefix}{artist}")
                
            if album:
                album_prefix = "💿 " if use_emoji else ""
                safe_print(f"     {album_prefix}{album}")
                
            if album_artist and album_artist != artist:
                group_prefix = "👥 " if use_emoji else ""
                safe_print(f"     {group_prefix}专辑艺术家: {album_artist}")
                
            if config.get("display.show_track_number", True) and track_number:
                track_prefix = "🔢 " if use_emoji else ""
                safe_print(f"     {track_prefix}曲目号: {track_number}")
                
            if config.get("display.show_genre", True) and genre:
                genre_prefix = "🎭 " if use_emoji else ""
                safe_print(f"     {genre_prefix}流派: {genre}")
                
            if config.get("display.show_year", True) and year:
                year_prefix = "📅 " if use_emoji else ""
                safe_print(f"     {year_prefix}年份: {year}")
                
            if duration:
                duration_str = f"{duration//60}:{duration%60:02d}"
                time_prefix = "⏱️ " if use_emoji else ""
                safe_print(f"     {time_prefix}时长: {duration_str}")
                
            app_prefix = "📱 " if use_emoji else ""
            status_prefix = "⚡ " if use_emoji else ""
            time_stamp_prefix = "🕐 " if use_emoji else ""
            safe_print(f"     {app_prefix}{app_name} | {status_prefix}{status} | {time_stamp_prefix}{dt.strftime(timestamp_format)}")
            safe_print()
    
    @staticmethod
    def show_statistics() -> None:
        """增强版播放统计报告 —— 更深入的用户行为洞察"""
        stats = db.get_statistics()
        
        if not stats:
            safe_print("暂无统计数据")
            return
            
        use_emoji = config.should_use_emoji()
        
        stats_prefix = "📊 " if use_emoji else ""
        safe_print(f"\n{stats_prefix}播放统计报告")
        safe_print("=" * 90)
        
        # === 基础指标 ===
        safe_print(f"📌 总播放记录: {stats.get('total_plays', 0):,}")
        safe_print(f"🎵 不同歌曲数: {stats.get('unique_songs', 0):,}")
        
        # === 播放时间分布（按小时）===
        hourly_stats = stats.get('hourly_stats', [])
        if hourly_stats:
            time_prefix = "⏰ " if use_emoji else ""
            safe_print(f"\n{time_prefix}每日播放高峰时段（按小时）:")
            hourly_list = sorted(hourly_stats, key=lambda x: x[1], reverse=True)
            for hour, count in hourly_list[:5]:
                safe_print(f"  🏁 {hour:02d}:00–{hour+1:02d}:00: {count:,} 次")
        
        # === 月度趋势（近3个月）===
        monthly_stats = stats.get('monthly_stats', [])
        if monthly_stats:
            month_prefix = "📅 " if use_emoji else ""
            safe_print(f"\n{month_prefix}近3个月月度播放趋势:")
            for month, count in monthly_stats:
                safe_print(f"  {month}: {count:,} 次")
        
        # === 最常播放的歌曲 & 艺术家（保持原逻辑）===
        top_songs = stats.get('top_songs', [])
        if top_songs:
            trophy_prefix = "🏆 " if use_emoji else ""
            safe_print(f"\n{trophy_prefix}最常播放的歌曲:")
            for i, (title, artist, album, count) in enumerate(top_songs, 1):
                artist_str = f" - {artist}" if artist else ""
                album_str = f" ({album})" if album else ""
                safe_print(f"  {i:2d}. {title}{artist_str}{album_str} - {count:,} 次")
        
        top_artists = stats.get('top_artists', [])
        if top_artists:
            mic_prefix = "🎤 " if use_emoji else ""
            safe_print(f"\n{mic_prefix}最常播放的艺术家:")
            for i, (artist, count) in enumerate(top_artists, 1):
                safe_print(f"  {i:2d}. {artist} - {count:,} 次")
        
        top_apps = stats.get('top_apps', [])
        if top_apps:
            app_prefix = "📱 " if use_emoji else ""
            safe_print(f"\n{app_prefix}最常使用的应用:")
            for i, (app_name, count) in enumerate(top_apps, 1):
                safe_print(f"  {i:2d}. {app_name} - {count:,} 次")
        
        # === 最近7天（保持原有）===
        daily_stats = stats.get('daily_stats', [])
        if daily_stats:
            calendar_prefix = "📅 " if use_emoji else ""
            safe_print(f"\n{calendar_prefix}最近7天播放统计:")
            for date, count in daily_stats:
                safe_print(f"  {date}: {count:,} 次")

# 全局显示工具实例
display = DisplayUtils()
