# display_utils.py
from datetime import datetime
from typing import List, Tuple, Dict, Any
from config_manager import config
from database import db

class DisplayUtils:
    @staticmethod
    def show_recent_tracks(limit: int = None) -> None:
        """显示最近播放的歌曲"""
        if limit is None:
            limit = config.get("display.default_recent_limit", 10)
            
        records = db.get_recent_tracks(limit)
        
        if not records:
            print("暂无播放记录")
            return
            
        use_emoji = config.should_use_emoji()
        timestamp_format = config.get_timestamp_format()
        
        title_prefix = "📋 " if use_emoji else ""
        print(f"\n{title_prefix}最近 {len(records)} 首歌曲:")
        print("=" * 80)
        
        for i, record in enumerate(records, 1):
            title, artist, album, album_artist, app_name, timestamp, duration, status, genre, year, track_number = record
            dt = datetime.fromisoformat(timestamp)
            
            song_prefix = "🎵 " if use_emoji else ""
            print(f"{i:2d}. {song_prefix}{title}")
            
            if artist:
                artist_prefix = "🎤 " if use_emoji else ""
                print(f"     {artist_prefix}{artist}")
                
            if album:
                album_prefix = "💿 " if use_emoji else ""
                print(f"     {album_prefix}{album}")
                
            if album_artist and album_artist != artist:
                group_prefix = "👥 " if use_emoji else ""
                print(f"     {group_prefix}专辑艺术家: {album_artist}")
                
            if config.get("display.show_track_number", True) and track_number:
                track_prefix = "🔢 " if use_emoji else ""
                print(f"     {track_prefix}曲目号: {track_number}")
                
            if config.get("display.show_genre", True) and genre:
                genre_prefix = "🎭 " if use_emoji else ""
                print(f"     {genre_prefix}流派: {genre}")
                
            if config.get("display.show_year", True) and year:
                year_prefix = "📅 " if use_emoji else ""
                print(f"     {year_prefix}年份: {year}")
                
            if duration:
                duration_str = f"{duration//60}:{duration%60:02d}"
                time_prefix = "⏱️ " if use_emoji else ""
                print(f"     {time_prefix}时长: {duration_str}")
                
            app_prefix = "📱 " if use_emoji else ""
            status_prefix = "⚡ " if use_emoji else ""
            time_stamp_prefix = "🕐 " if use_emoji else ""
            print(f"     {app_prefix}{app_name} | {status_prefix}{status} | {time_stamp_prefix}{dt.strftime(timestamp_format)}")
            print()
            
    @staticmethod
    def show_statistics() -> None:
        """显示播放统计"""
        stats = db.get_statistics()
        
        if not stats:
            print("暂无统计数据")
            return
            
        use_emoji = config.should_use_emoji()
        
        stats_prefix = "📊 " if use_emoji else ""
        print(f"\n{stats_prefix}播放统计报告")
        print("=" * 60)
        
        chart_prefix = "📈 " if use_emoji else ""
        song_prefix = "🎵 " if use_emoji else ""
        session_prefix = "🎧 " if use_emoji else ""
        avg_prefix = "📊 " if use_emoji else ""
        
        print(f"{chart_prefix}总播放记录: {stats.get('total_plays', 0)}")
        print(f"{song_prefix}不同歌曲数: {stats.get('unique_songs', 0)}")
        print(f"{session_prefix}播放会话数: {stats.get('total_sessions', 0)}")
        print(f"{avg_prefix}平均每会话播放: {stats.get('avg_tracks_per_session', 0):.1f} 首")
        
        top_songs = stats.get('top_songs', [])
        if top_songs:
            trophy_prefix = "🏆 " if use_emoji else ""
            print(f"\n{trophy_prefix}最常播放的歌曲:")
            for i, (title, artist, album, count) in enumerate(top_songs, 1):
                artist_str = f" - {artist}" if artist else ""
                album_str = f" ({album})" if album else ""
                print(f"  {i:2d}. {title}{artist_str}{album_str} - {count}次")
                
        top_artists = stats.get('top_artists', [])
        if top_artists:
            mic_prefix = "🎤 " if use_emoji else ""
            print(f"\n{mic_prefix}最常播放的艺术家:")
            for i, (artist, count) in enumerate(top_artists, 1):
                print(f"  {i:2d}. {artist} - {count}次")
                
        top_apps = stats.get('top_apps', [])
        if top_apps:
            app_prefix = "📱 " if use_emoji else ""
            print(f"\n{app_prefix}最常使用的应用:")
            for i, (app_name, count) in enumerate(top_apps, 1):
                print(f"  {i:2d}. {app_name} - {count}次")
                
        daily_stats = stats.get('daily_stats', [])
        if daily_stats:
            calendar_prefix = "📅 " if use_emoji else ""
            print(f"\n{calendar_prefix}最近7天播放统计:")
            for date, count in daily_stats:
                print(f"  {date}: {count}次")

# 全局显示工具实例
display = DisplayUtils()
