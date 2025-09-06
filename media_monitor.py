# media_monitor.py - 添加静默模式和停止功能
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from config_manager import config
from database import db
from logger import logger

try:
    import winsdk.windows.media.control as wmc
    from winsdk.windows.storage.streams import RandomAccessStreamReference
except ImportError:
    print("需要安装 winsdk 库: pip install winsdk")
    exit(1)

class MediaMonitor:
    def __init__(self):
        self.current_session = None
        self.running = False
        
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        
    async def get_media_info(self) -> Dict[str, Any]:
        """获取当前播放的媒体信息"""
        try:
            sessions_manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            current_session = sessions_manager.get_current_session()
            
            if current_session is None:
                return {}
                
            # 获取媒体属性
            try:
                media_properties = await current_session.try_get_media_properties_async()
            except Exception as e:
                logger.debug(f"获取媒体属性失败: {e}")
                media_properties = None
                
            # 获取播放信息
            try:
                playback_info = current_session.get_playback_info()
                timeline_info = current_session.get_timeline_properties()
            except Exception as e:
                logger.debug(f"获取播放信息失败: {e}")
                playback_info = None
                timeline_info = None
                
            media_info = {}
            
            if media_properties:
                media_info.update({
                    'title': media_properties.title or '',
                    'artist': media_properties.artist or '',
                    'album': media_properties.album_title or '',
                    'album_artist': media_properties.album_artist or '',
                    'track_number': media_properties.track_number or 0,
                    'genre': getattr(media_properties, 'genres', [None])[0] if hasattr(media_properties, 'genres') and media_properties.genres else '',
                })
                
                # 尝试获取年份
                try:
                    if hasattr(media_properties, 'year') and media_properties.year:
                        media_info['year'] = media_properties.year
                except:
                    media_info['year'] = 0
                
            if playback_info:
                status_map = {
                    0: 'Closed',
                    1: 'Opened', 
                    2: 'Changing',
                    3: 'Stopped',
                    4: 'Playing',
                    5: 'Paused'
                }
                media_info['status'] = status_map.get(playback_info.playback_status, 'Unknown')
                
            if timeline_info:
                try:
                    media_info.update({
                        'duration': int(timeline_info.end_time.total_seconds()) if timeline_info.end_time else 0,
                        'position': int(timeline_info.position.total_seconds()) if timeline_info.position else 0,
                    })
                except:
                    media_info.update({
                        'duration': 0,
                        'position': 0,
                    })
                
            # 获取应用信息
            try:
                app_id = current_session.source_app_user_model_id or 'Unknown'
                media_info['app_id'] = app_id
                media_info['app_name'] = config.get_app_name(app_id)
                
                # 检查是否忽略此应用
                if config.is_app_ignored(app_id):
                    return {}
                    
            except Exception as e:
                logger.debug(f"获取应用信息失败: {e}")
                media_info['app_name'] = 'Unknown'
                media_info['app_id'] = 'Unknown'
                
            return media_info
            
        except Exception as e:
            logger.error(f"获取媒体信息时出错: {e}")
            return {}
            
    def _format_media_output(self, media_info: Dict[str, Any], current_time: datetime, silent_mode: bool = False) -> None:
        """格式化媒体输出"""
        if silent_mode:
            return
            
        use_emoji = config.should_use_emoji()
        
        print(f"[{current_time.strftime('%H:%M:%S')}] 正在播放:")
        
        title_prefix = "🎵 " if use_emoji else ""
        print(f"  {title_prefix}歌曲: {media_info.get('title', 'Unknown')}")
        
        if media_info.get('artist'):
            artist_prefix = "🎤 " if use_emoji else ""
            print(f"  {artist_prefix}艺术家: {media_info.get('artist')}")
            
        if media_info.get('album'):
            album_prefix = "💿 " if use_emoji else ""
            print(f"  {album_prefix}专辑: {media_info.get('album')}")
            
        if media_info.get('album_artist') and media_info.get('album_artist') != media_info.get('artist'):
            group_prefix = "👥 " if use_emoji else ""
            print(f"  {group_prefix}专辑艺术家: {media_info.get('album_artist')}")
            
        if config.get("display.show_track_number", True) and media_info.get('track_number'):
            track_prefix = "🔢 " if use_emoji else ""
            print(f"  {track_prefix}曲目号: {media_info.get('track_number')}")
            
        if config.get("display.show_genre", True) and media_info.get('genre'):
            genre_prefix = "🎭 " if use_emoji else ""
            print(f"  {genre_prefix}流派: {media_info.get('genre')}")
            
        if config.get("display.show_year", True) and media_info.get('year'):
            year_prefix = "📅 " if use_emoji else ""
            print(f"  {year_prefix}年份: {media_info.get('year')}")
            
        app_prefix = "📱 " if use_emoji else ""
        print(f"  {app_prefix}应用: {media_info.get('app_name', 'Unknown')}")
        
        status_prefix = "⚡ " if use_emoji else ""
        print(f"  {status_prefix}状态: {media_info.get('status', 'Unknown')}")
        
        if config.get("display.show_progress", True) and media_info.get('duration'):
            duration_str = f"{media_info['duration']//60}:{media_info['duration']%60:02d}"
            position_str = f"{media_info.get('position', 0)//60}:{media_info.get('position', 0)%60:02d}"
            progress_prefix = "⏱️ " if use_emoji else ""
            print(f"  {progress_prefix}进度: {position_str}/{duration_str}")
            
    async def monitor_media(self, interval: int = None, silent_mode: bool = False) -> None:
        """监控媒体播放并记录"""
        if interval is None:
            interval = config.get_monitoring_interval()
            
        if not silent_mode:
            print("开始监控媒体播放...")
            print("支持所有兼容 Windows Media Transport Controls 的应用")
            print("按 Ctrl+C 停止监控\n")
        
        last_song_info = None
        session_start = datetime.now()
        tracks_in_session = 0
        
        self.running = True
        logger.info(f"开始媒体监控，间隔: {interval}秒，静默模式: {silent_mode}")
        
        try:
            while self.running:
                media_info = await self.get_media_info()
                
                if media_info and media_info.get('title'):
                    current_song_id = f"{media_info.get('title')}_{media_info.get('artist')}_{media_info.get('app_name')}"
                    last_song_id = f"{last_song_info.get('title', '')}_{last_song_info.get('artist', '')}_{last_song_info.get('app_name', '')}" if last_song_info else ""
                    
                    # 检查是否是新歌曲或状态变为播放
                    if (current_song_id != last_song_id and media_info.get('status') == 'Playing') or \
                       (last_song_info and last_song_info.get('status') != 'Playing' and media_info.get('status') == 'Playing'):
                        
                        current_time = datetime.now()
                        self._format_media_output(media_info, current_time, silent_mode)
                        
                        # 保存到数据库
                        if db.save_media_info(media_info):
                            if not silent_mode:
                                save_prefix = "✅ " if config.should_use_emoji() else ""
                                print(f"  {save_prefix}已保存到数据库")
                            tracks_in_session += 1
                        else:
                            if not silent_mode:
                                skip_prefix = "ℹ️ " if config.should_use_emoji() else ""
                                print(f"  {skip_prefix}重复记录，跳过保存")
                            
                        if not silent_mode:
                            print("-" * 60)
                        last_song_info = media_info.copy()
                        
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            if not silent_mode:
                print(f"\n监控已停止")
            
            # 保存会话信息
            if tracks_in_session > 0:
                db.save_session_info(session_start, datetime.now(), 
                                   last_song_info.get('app_name', 'Unknown') if last_song_info else 'Unknown', 
                                   tracks_in_session)
                if not silent_mode:
                    print(f"本次会话播放了 {tracks_in_session} 首歌曲")
            
        finally:
            self.running = False
            logger.info("媒体监控已停止")

# 全局监控器实例
monitor = MediaMonitor()
