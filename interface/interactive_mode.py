import asyncio
from config.config_manager import config, version_info
from utils.display_utils import display
from utils.export_manager import ExportManager
from config.config_editor import ConfigEditor
from utils.logger import logger
from utils.safe_print import safe_print
from core.database import db

class InteractiveMode:
    def __init__(self, monitor):
        self.monitor = monitor

    def run(self):
        """运行交互模式"""
        use_emoji = config.should_use_emoji()
        title_prefix = "🎵 " if use_emoji else ""
        safe_print(f"{title_prefix}{version_info.get_full_name()}")
        safe_print("=" * 50)
        
        feature_prefix = "🚀 " if use_emoji else ""
        support_prefix = "📱 " if use_emoji else ""
        save_prefix = "💾 " if use_emoji else ""
        
        safe_print(f"{feature_prefix}使用 Windows Media Transport Controls API")
        safe_print(f"{support_prefix}支持所有兼容的媒体应用")
        safe_print(f"{save_prefix}自动保存播放历史和统计信息")
        
        logger.info("程序启动 - 交互模式")
        
        # 检查自动启动
        if config.get("monitoring.auto_start", False):
            safe_print("\n🚀 自动启动监控...")
            try:
                asyncio.run(self.monitor.monitor_media())
            except Exception as e:
                logger.error(f"自动监控失败: {e}")
        
        self._main_menu_loop()

    def _main_menu_loop(self):
        """主菜单循环"""
        while True:
            use_emoji = config.should_use_emoji()
            target_prefix = "🎯 " if use_emoji else ""
            safe_print(f"\n{target_prefix}选择操作:")
            
            headphone_prefix = "🎧 " if use_emoji else ""
            list_prefix = "📋 " if use_emoji else ""
            chart_prefix = "📊 " if use_emoji else ""
            disk_prefix = "💾 " if use_emoji else ""
            gear_prefix = "⚙️ " if use_emoji else ""
            music_prefix = "🎵 " if use_emoji else ""
            cross_prefix = "❌ " if use_emoji else ""
            
            safe_print(f"1. {headphone_prefix}开始监控媒体播放")
            safe_print(f"2. {list_prefix}查看最近播放记录")
            safe_print(f"3. {chart_prefix}查看播放统计")
            safe_print(f"4. {disk_prefix}导出播放历史")
            safe_print(f"5. {music_prefix}QQ音乐歌单管理")  # 新增
            safe_print(f"6. {gear_prefix}配置设置")
            safe_print(f"7. {cross_prefix}退出")
            
            choice = input("\n请输入选择 (1-7): ").strip()
            
            if choice == '1':
                self._start_monitoring()
            elif choice == '2':
                self._show_recent_tracks()
            elif choice == '3':
                display.show_statistics()
            elif choice == '4':
                ExportManager.export_history_interactive()
            elif choice == '5':
                self._qqmusic_management_menu()  # 新增
            elif choice == '6':
                ConfigEditor.show_config_editor()
            elif choice == '7':
                wave_prefix = "👋 " if config.should_use_emoji() else ""
                safe_print(f"{wave_prefix}再见!")
                logger.info("程序退出")
                break
            else:
                safe_print("❌ 无效的选择，请重试")

    def _start_monitoring(self):
        """开始监控"""
        try:
            current_interval = config.get_monitoring_interval()
            interval_input = input(f"⏱️ 监控间隔 (秒，当前默认{current_interval}): ").strip()
            
            if interval_input:
                interval = int(interval_input)
                min_interval = config.get("monitoring.min_interval", 1)
                max_interval = config.get("monitoring.max_interval", 60)
                
                if interval < min_interval or interval > max_interval:
                    safe_print(f"⚠️ 间隔必须在{min_interval}-{max_interval}秒之间，使用默认值{current_interval}秒")
                    interval = current_interval
            else:
                interval = current_interval
                
            asyncio.run(self.monitor.monitor_media(interval))
            
        except ValueError:
            safe_print(f"⚠️ 无效的间隔时间，使用默认值{config.get_monitoring_interval()}秒")
            asyncio.run(self.monitor.monitor_media())
        except Exception as e:
            safe_print(f"❌ 监控过程中出错: {e}")
            logger.error(f"监控出错: {e}")

    def _show_recent_tracks(self):
        """显示最近播放记录"""
        try:
            default_limit = config.get("display.default_recent_limit", 10)
            limit_input = input(f"📋 显示最近多少首歌 (默认{default_limit}): ").strip()
            
            if limit_input:
                limit = int(limit_input)
                if limit < 1:
                    limit = default_limit
            else:
                limit = default_limit
                
            display.show_recent_tracks(limit)
            
        except ValueError:
            display.show_recent_tracks()

    def _qqmusic_management_menu(self):
        """QQ音乐歌单管理菜单"""
        while True:
            use_emoji = config.should_use_emoji()
            music_prefix = "🎵 " if use_emoji else ""
            safe_print(f"\n{music_prefix}QQ音乐歌单管理:")
            
            list_prefix = "📋 " if use_emoji else ""
            delete_prefix = "🗑️ " if use_emoji else ""
            chart_prefix = "📊 " if use_emoji else ""
            reset_prefix = "🔄 " if use_emoji else ""
            back_prefix = "↩️ " if use_emoji else ""
            
            safe_print(f"1. {list_prefix}查看最近播放记录（带删除状态）")
            safe_print(f"2. {delete_prefix}删除最近播放的歌曲")
            safe_print(f"3. {chart_prefix}查看删除统计")
            safe_print(f"4. {reset_prefix}重置删除状态")
            safe_print(f"5. {back_prefix}返回主菜单")
            
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == '1':
                self._show_recent_tracks_with_deletion_status()
            elif choice == '2':
                self._delete_recent_tracks_menu()
            elif choice == '3':
                self._show_deletion_statistics()
            elif choice == '4':
                self._reset_deletion_status_menu()
            elif choice == '5':
                break
            else:
                safe_print("❌ 无效的选择，请重试")

    def _show_recent_tracks_with_deletion_status(self):
        """显示带删除状态的最近播放记录"""
        try:
            default_limit = config.get("display.default_recent_limit", 10)
            limit_input = input(f"📋 显示最近多少首歌 (默认{default_limit}): ").strip()
            
            if limit_input:
                limit = int(limit_input)
                if limit < 1:
                    limit = default_limit
            else:
                limit = default_limit
            
            # 应用过滤
            app_filter = input("🎵 过滤应用 (留空显示所有，如 'QQ音乐'): ").strip()
            if not app_filter:
                app_filter = None
                
            tracks = db.get_recent_tracks_for_deletion(limit, app_filter)
            
            if not tracks:
                safe_print("📝 没有找到播放记录")
                return
            
            use_emoji = config.should_use_emoji()
            safe_print(f"\n📋 最近播放记录 (共 {len(tracks)} 首):")
            safe_print("=" * 80)
            
            status_emojis = {
                None: "⚪",
                'pending': "🟡",
                'deleted': "✅",
                'failed': "❌"
            }
            
            for i, track in enumerate(tracks, 1):
                status = track['deletion_status']
                emoji = status_emojis.get(status, "⚪")
                
                safe_print(f"{i:2d}. {emoji} {track['title']}")
                safe_print(f"     🎤 {track['artist']} | 📱 {track['app_name']}")
                safe_print(f"     ⏰ {track['timestamp']}")
                
                if status:
                    status_text = {
                        'pending': '等待删除',
                        'deleted': '已删除',
                        'failed': '删除失败'
                    }.get(status, status)
                    safe_print(f"     🏷️ 状态: {status_text}")
                    
                    if track['deletion_notes']:
                        safe_print(f"     📝 备注: {track['deletion_notes']}")
                
                safe_print()
                
        except ValueError:
            safe_print("❌ 无效的数字")
        except Exception as e:
            safe_print(f"❌ 显示记录时出错: {e}")

    def _delete_recent_tracks_menu(self):
        """删除最近播放歌曲的菜单"""
        try:
            # 获取最近播放记录
            limit_input = input("🎵 选择最近多少首歌进行删除 (默认10): ").strip()
            limit = int(limit_input) if limit_input else 10
            
            # 应用过滤
            app_filter = input("🎵 只删除特定应用的歌曲 (留空删除所有，推荐填 'QQ音乐'): ").strip()
            if not app_filter:
                app_filter = None
            
            tracks = db.get_recent_tracks_for_deletion(limit, app_filter)
            
            if not tracks:
                safe_print("📝 没有找到播放记录")
                return
            
            # 过滤掉已经处理过的歌曲
            unprocessed_tracks = [t for t in tracks if not t['deletion_status']]
            
            if not unprocessed_tracks:
                safe_print("📝 所有歌曲都已处理过，没有需要删除的歌曲")
                safe_print("💡 提示: 使用 '重置删除状态' 功能可以重新处理")
                return
            
            # 显示将要删除的歌曲
            safe_print(f"\n🗑️ 将要删除的歌曲 (共 {len(unprocessed_tracks)} 首):")
            safe_print("-" * 60)
            
            for i, track in enumerate(unprocessed_tracks, 1):
                safe_print(f"{i:2d}. {track['title']} - {track['artist']} ({track['app_name']})")
            
            # 确认删除
            confirm = input(f"\n⚠️ 确认删除这 {len(unprocessed_tracks)} 首歌曲吗? (y/N): ").strip().lower()
            
            if confirm == 'y':
                # 执行批量删除
                from core.qqmusic_manager import qqmusic_manager
                with qqmusic_manager as manager:
                    results = manager.batch_delete_from_recent_tracks(unprocessed_tracks)
                    
                if 'error' in results:
                    safe_print(f"❌ 删除失败: {results['error']}")
                else:
                    safe_print(f"\n🎉 删除操作完成!")
                    safe_print(f"📊 详细结果已保存到数据库")
            else:
                safe_print("❌ 删除操作已取消")
                
        except ValueError:
            safe_print("❌ 无效的数字")
        except Exception as e:
            safe_print(f"❌ 删除操作时出错: {e}")
            logger.error(f"删除操作失败: {e}")

    def _show_deletion_statistics(self):
        """显示删除统计"""
        try:
            stats = db.get_deletion_statistics()
            
            if not stats:
                safe_print("📊 暂无删除统计数据")
                return
            
            use_emoji = config.should_use_emoji()
            safe_print(f"\n📊 删除操作统计:")
            safe_print("=" * 40)
            
            counts = stats.get('deletion_counts', {})
            safe_print(f"🟡 等待删除: {counts.get('pending', 0)}")
            safe_print(f"✅ 删除成功: {counts.get('deleted', 0)}")
            safe_print(f"❌ 删除失败: {counts.get('failed', 0)}")
            safe_print(f"📊 总计尝试: {counts.get('total_attempted', 0)}")
            
            if counts.get('total_attempted', 0) > 0:
                success_rate = counts.get('deleted', 0) / counts.get('total_attempted', 1) * 100
                safe_print(f"🎯 成功率: {success_rate:.1f}%")
            
            # 显示最近删除记录
            recent = stats.get('recent_deletions', [])
            if recent:
                safe_print(f"\n📋 最近删除记录:")
                safe_print("-" * 40)
                
                status_emojis = {
                    'pending': "🟡",
                    'deleted': "✅", 
                    'failed': "❌"
                }
                
                for record in recent[:5]:  # 只显示最近5条
                    title, artist, app_name, status, attempted_at = record
                    emoji = status_emojis.get(status, "⚪")
                    safe_print(f"{emoji} {title} - {artist}")
                    safe_print(f"   📱 {app_name} | ⏰ {attempted_at}")
                    
        except Exception as e:
            safe_print(f"❌ 获取统计信息时出错: {e}")
            logger.error(f"获取删除统计失败: {e}")

    def _reset_deletion_status_menu(self):
        """重置删除状态菜单"""
        try:
            safe_print("\n🔄 重置删除状态:")
            safe_print("1. 重置所有删除状态")
            safe_print("2. 只重置失败的删除状态")
            safe_print("3. 取消")
            
            choice = input("\n请选择 (1-3): ").strip()
            
            if choice == '1':
                confirm = input("⚠️ 确认重置所有删除状态吗? (y/N): ").strip().lower()
                if confirm == 'y':
                    if db.reset_deletion_status():
                        safe_print("✅ 所有删除状态已重置")
                    else:
                        safe_print("❌ 重置失败")
                        
            elif choice == '2':
                # 这里可以实现只重置失败状态的逻辑
                safe_print("🚧 此功能即将实现")
                
            elif choice == '3':
                safe_print("❌ 操作已取消")
            else:
                safe_print("❌ 无效的选择")
                
        except Exception as e:
            safe_print(f"❌ 重置操作时出错: {e}")
            logger.error(f"重置删除状态失败: {e}")
