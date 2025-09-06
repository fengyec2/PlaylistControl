import asyncio
from config_manager import config, version_info
from display_utils import display
from export_manager import ExportManager
from config_editor import ConfigEditor
from logger import logger

class InteractiveMode:
    def __init__(self, monitor):
        self.monitor = monitor

    def run(self):
        """运行交互模式"""
        use_emoji = config.should_use_emoji()
        title_prefix = "🎵 " if use_emoji else ""
        print(f"{title_prefix}{version_info.get_full_name()}")
        print("=" * 50)
        
        feature_prefix = "🚀 " if use_emoji else ""
        support_prefix = "📱 " if use_emoji else ""
        save_prefix = "💾 " if use_emoji else ""
        
        print(f"{feature_prefix}使用 Windows Media Transport Controls API")
        print(f"{support_prefix}支持所有兼容的媒体应用")
        print(f"{save_prefix}自动保存播放历史和统计信息")
        
        logger.info("程序启动 - 交互模式")
        
        # 检查自动启动
        if config.get("monitoring.auto_start", False):
            print("\n🚀 自动启动监控...")
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
            print(f"\n{target_prefix}选择操作:")
            
            headphone_prefix = "🎧 " if use_emoji else ""
            list_prefix = "📋 " if use_emoji else ""
            chart_prefix = "📊 " if use_emoji else ""
            disk_prefix = "💾 " if use_emoji else ""
            gear_prefix = "⚙️ " if use_emoji else ""
            cross_prefix = "❌ " if use_emoji else ""
            
            print(f"1. {headphone_prefix}开始监控媒体播放")
            print(f"2. {list_prefix}查看最近播放记录")
            print(f"3. {chart_prefix}查看播放统计")
            print(f"4. {disk_prefix}导出播放历史")
            print(f"5. {gear_prefix}配置设置")
            print(f"6. {cross_prefix}退出")
            
            choice = input("\n请输入选择 (1-6): ").strip()
            
            if choice == '1':
                self._start_monitoring()
            elif choice == '2':
                self._show_recent_tracks()
            elif choice == '3':
                display.show_statistics()
            elif choice == '4':
                ExportManager.export_history_interactive()
            elif choice == '5':
                ConfigEditor.show_config_editor()
            elif choice == '6':
                wave_prefix = "👋 " if config.should_use_emoji() else ""
                print(f"{wave_prefix}再见!")
                logger.info("程序退出")
                break
            else:
                print("❌ 无效的选择，请重试")

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
                    print(f"⚠️ 间隔必须在{min_interval}-{max_interval}秒之间，使用默认值{current_interval}秒")
                    interval = current_interval
            else:
                interval = current_interval
                
            asyncio.run(self.monitor.monitor_media(interval))
            
        except ValueError:
            print(f"⚠️ 无效的间隔时间，使用默认值{config.get_monitoring_interval()}秒")
            asyncio.run(self.monitor.monitor_media())
        except Exception as e:
            print(f"❌ 监控过程中出错: {e}")
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
