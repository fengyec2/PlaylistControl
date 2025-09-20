# media_monitor.py - 添加静默模式和停止功能
import asyncio
import time
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from config.config_manager import config
from core.database import db
from utils.logger import logger
from utils.safe_print import safe_print

try:
    import winsdk.windows.media.control as wmc
    from winsdk.windows.storage.streams import RandomAccessStreamReference
except ImportError:
    safe_print("需要安装 winsdk 库: pip install winsdk")
    exit(1)

class MediaMonitor:
    def __init__(self):
        self.current_session = None
        self.running = False
        self._stop_flag = False
        self._monitoring_task = None
        self.last_complete_info = {}  # 缓存上一次完整的信息
        self.pending_info_cache = {}  # 缓存待验证的信息
        
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        self._stop_flag = True
        # 如果有正在运行的监控任务，取消它
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
    
    def set_stop_flag(self):
        """设置停止标志"""
        self._stop_flag = True
        self.running = False
    
    def _is_duration_valid(self, duration: int) -> bool:
        """检查时长是否有效"""
        return duration is not None and duration > 0
    
    def _is_info_complete(self, media_info: Dict[str, Any]) -> bool:
        """检查媒体信息是否完整"""
        if not media_info.get('title'):
            return False
        
        # 对于正在播放的歌曲，时长应该是有效的
        if media_info.get('status') == 'Playing':
            return self._is_duration_valid(media_info.get('duration', 0))
        
        return True
    
    def _calculate_info_completeness_score(self, media_info: Dict[str, Any]) -> int:
        """计算信息完整度分数"""
        score = 0
        important_fields = {
            'title': 3,      # 歌名最重要
            'artist': 2,     # 艺术家重要
            'duration': 2,   # 时长重要
            'album': 1,      # 专辑一般重要
            'status': 1      # 状态一般重要
        }
        
        for field, weight in important_fields.items():
            value = media_info.get(field)
            if value and str(value) not in ['', 'Unknown', '0']:
                if field == 'duration' and self._is_duration_valid(value):
                    score += weight
                elif field != 'duration':
                    score += weight
        
        return score
    
    def _merge_media_info(self, cached_info: Dict[str, Any], new_info: Dict[str, Any]) -> Dict[str, Any]:
        """智能合并媒体信息，优先使用更完整的数据"""
        if not cached_info:
            return new_info
        
        merged = cached_info.copy()
        
        # 优先使用新的非空值
        for key, value in new_info.items():
            if value and str(value) not in ['', 'Unknown', '0']:
                # 对于时长字段，确保新值是有效的
                if key == 'duration':
                    if self._is_duration_valid(value):
                        merged[key] = value
                else:
                    merged[key] = value
        
        return merged
    
    def _get_track_identifier(self, media_info: Dict[str, Any]) -> str:
        """生成歌曲的唯一标识符"""
        return f"{media_info.get('title', '')}_{media_info.get('artist', '')}_{media_info.get('app_name', '')}"

    async def get_media_info(self) -> Dict[str, Any]:
        """获取当前播放的媒体信息，带重试和验证机制"""
        try:
            # 检查停止标志
            if self._stop_flag:
                return {}
                
            # 获取基础信息
            raw_info = await self._get_raw_media_info()
            
            if not raw_info or not raw_info.get('title'):
                return {}
            
            track_id = self._get_track_identifier(raw_info)
            
            # 检查是否是新歌曲
            is_new_track = track_id not in self.last_complete_info
            
            # 如果是新歌曲且信息不完整，尝试获取完整信息
            if is_new_track and not self._is_info_complete(raw_info):
                complete_info = await self._get_complete_media_info(raw_info)
                if complete_info:
                    self.last_complete_info[track_id] = complete_info
                    return complete_info
            
            # 如果是已知歌曲，合并信息
            if track_id in self.last_complete_info:
                merged_info = self._merge_media_info(self.last_complete_info[track_id], raw_info)
                self.last_complete_info[track_id] = merged_info
                return merged_info
            
            # 存储完整信息
            if self._is_info_complete(raw_info):
                self.last_complete_info[track_id] = raw_info
            
            return raw_info
            
        except Exception as e:
            logger.error(f"获取媒体信息时出错: {e}")
            return {}
    
    async def _get_complete_media_info(self, initial_info: Dict[str, Any], max_wait: float = 5.0) -> Dict[str, Any]:
        """等待获取完整的媒体信息，特别是时长信息"""
        start_time = time.time()
        best_info = initial_info
        best_score = self._calculate_info_completeness_score(initial_info)
        
        logger.debug(f"等待完整信息: {initial_info.get('title', 'Unknown')} (初始分数: {best_score})")
        
        retry_intervals = [0.5, 1.0, 1.5, 2.0]  # 渐进式重试间隔
        
        for retry_interval in retry_intervals:
            if time.time() - start_time >= max_wait or self._stop_flag:
                break
                
            try:
                await asyncio.sleep(retry_interval)
            except asyncio.CancelledError:
                logger.debug("等待媒体信息时被取消")
                break
            
            # 再次检查停止标志
            if self._stop_flag:
                break
            
            try:
                current_info = await self._get_raw_media_info()
                
                if not current_info or not current_info.get('title'):
                    continue
                
                # 确保还是同一首歌
                if (current_info.get('title') != initial_info.get('title') or 
                    current_info.get('artist') != initial_info.get('artist')):
                    logger.debug("歌曲已切换，停止等待")
                    break
                
                current_score = self._calculate_info_completeness_score(current_info)
                
                # 如果找到更完整的信息
                if current_score > best_score:
                    best_info = current_info
                    best_score = current_score
                    logger.debug(f"找到更完整的信息 (分数: {current_score})")
                    
                    # 如果信息已经足够完整，提前退出
                    if self._is_info_complete(current_info):
                        logger.debug("信息已完整，提前结束等待")
                        break
                        
            except Exception as e:
                logger.debug(f"重试获取信息时出错: {e}")
                continue
        
        elapsed = time.time() - start_time
        logger.debug(f"等待完成，耗时: {elapsed:.1f}s，最终分数: {best_score}")
        
        return best_info

    async def _get_raw_media_info(self) -> Dict[str, Any]:
        """获取原始媒体信息（单次调用）"""
        try:
            # 检查停止标志
            if self._stop_flag:
                return {}
                
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
            logger.error(f"获取原始媒体信息时出错: {e}")
            return {}
            
    def _format_media_output(self, media_info: Dict[str, Any], current_time: datetime, silent_mode: bool = False) -> None:
        """格式化媒体输出"""
        if silent_mode:
            return
            
        use_emoji = config.should_use_emoji()
        
        safe_print(f"[{current_time.strftime('%H:%M:%S')}] 正在播放:")
        
        title_prefix = "🎵 " if use_emoji else ""
        safe_print(f"  {title_prefix}歌曲: {media_info.get('title', 'Unknown')}")
        
        if media_info.get('artist'):
            artist_prefix = "🎤 " if use_emoji else ""
            safe_print(f"  {artist_prefix}艺术家: {media_info.get('artist')}")
            
        if media_info.get('album'):
            album_prefix = "💿 " if use_emoji else ""
            safe_print(f"  {album_prefix}专辑: {media_info.get('album')}")
            
        if media_info.get('album_artist') and media_info.get('album_artist') != media_info.get('artist'):
            group_prefix = "👥 " if use_emoji else ""
            safe_print(f"  {group_prefix}专辑艺术家: {media_info.get('album_artist')}")
            
        if config.get("display.show_track_number", True) and media_info.get('track_number'):
            track_prefix = "🔢 " if use_emoji else ""
            safe_print(f"  {track_prefix}曲目号: {media_info.get('track_number')}")
            
        if config.get("display.show_genre", True) and media_info.get('genre'):
            genre_prefix = "🎭 " if use_emoji else ""
            safe_print(f"  {genre_prefix}流派: {media_info.get('genre')}")
            
        if config.get("display.show_year", True) and media_info.get('year'):
            year_prefix = "📅 " if use_emoji else ""
            safe_print(f"  {year_prefix}年份: {media_info.get('year')}")
            
        app_prefix = "📱 " if use_emoji else ""
        safe_print(f"  {app_prefix}应用: {media_info.get('app_name', 'Unknown')}")
        
        status_prefix = "⚡ " if use_emoji else ""
        safe_print(f"  {status_prefix}状态: {media_info.get('status', 'Unknown')}")
        
        if config.get("display.show_progress", True) and media_info.get('duration'):
            duration_str = f"{media_info['duration']//60}:{media_info['duration']%60:02d}"
            position_str = f"{media_info.get('position', 0)//60}:{media_info.get('position', 0)%60:02d}"
            progress_prefix = "⏱️ " if use_emoji else ""
            safe_print(f"  {progress_prefix}进度: {position_str}/{duration_str}")

    async def _monitoring_loop(self, interval: int, silent_mode: bool = False):
        """监控循环的核心实现"""
        last_song_info = None
        session_start = datetime.now()
        tracks_in_session = 0
        
        try:
            while self.running and not self._stop_flag:
                try:
                    media_info = await self.get_media_info()
                    
                    # 检查停止标志
                    if self._stop_flag:
                        break
                    
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
                                    safe_print(f"  {save_prefix}已保存到数据库")
                                tracks_in_session += 1
                            else:
                                if not silent_mode:
                                    skip_prefix = "ℹ️ " if config.should_use_emoji() else ""
                                    safe_print(f"  {skip_prefix}重复记录，跳过保存")
                                
                            if not silent_mode:
                                safe_print("-" * 60)
                            last_song_info = media_info.copy()
                    
                    # 检查停止标志再次，避免不必要的等待
                    if self._stop_flag:
                        break
                        
                    # 使用可中断的sleep
                    try:
                        await asyncio.sleep(interval)
                    except asyncio.CancelledError:
                        logger.debug("监控循环中的sleep被取消")
                        break
                        
                except asyncio.CancelledError:
                    logger.debug("监控循环被取消")
                    break
                except Exception as e:
                    logger.error(f"监控循环中发生错误: {e}")
                    if not silent_mode:
                        safe_print(f"监控过程中发生错误: {e}")
                    
                    # 如果发生错误，短暂等待后继续
                    if not self._stop_flag:
                        try:
                            await asyncio.sleep(1)
                        except asyncio.CancelledError:
                            break
                
        finally:
            # 保存会话信息
            if tracks_in_session > 0:
                try:
                    db.save_session_info(session_start, datetime.now(), 
                                       last_song_info.get('app_name', 'Unknown') if last_song_info else 'Unknown', 
                                       tracks_in_session)
                    if not silent_mode:
                        safe_print(f"本次会话播放了 {tracks_in_session} 首歌曲")
                except Exception as e:
                    logger.error(f"保存会话信息时出错: {e}")

    async def monitor_media(self, interval: int = None, silent_mode: bool = False) -> None:
        """监控媒体播放并记录"""
        if interval is None:
            interval = config.get_monitoring_interval()
            
        if not silent_mode:
            safe_print("开始监控媒体播放...")
            safe_print("支持所有兼容 Windows Media Transport Controls 的应用")
            safe_print("按 Ctrl+C 停止监控\n")
        
        self.running = True
        self._stop_flag = False
        logger.info(f"开始媒体监控，间隔: {interval}秒，静默模式: {silent_mode}")
        
        try:
            # 创建监控任务
            self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval, silent_mode))
            await self._monitoring_task
            
        except KeyboardInterrupt:
            if not silent_mode:
                safe_print(f"\n接收到键盘中断信号")
        except asyncio.CancelledError:
            if not silent_mode:
                safe_print(f"\n监控任务被取消")
        except Exception as e:
            logger.error(f"监控过程中发生未预期的错误: {e}")
            if not silent_mode:
                safe_print(f"\n监控过程中发生错误: {e}")
        finally:
            # 清理工作
            self.running = False
            self._stop_flag = True
            
            if not silent_mode:
                safe_print(f"\n监控已停止")
            
            logger.info("媒体监控已停止")

# 全局监控器实例
monitor = MediaMonitor()
