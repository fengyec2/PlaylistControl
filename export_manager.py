import json
from config_manager import config
from database import db
from logger import logger

class ExportManager:
    @staticmethod
    def export_history_interactive():
        """交互式导出播放历史"""
        default_filename = config.get("export.default_filename", "media_history.json")
        filename = input(f"💾 导出文件名 (默认{default_filename}): ").strip() or default_filename
        
        try:
            export_data = db.export_data()
            
            if not export_data:
                print("❌ 没有数据可导出")
                return
                
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            use_emoji = config.should_use_emoji()
            success_prefix = "✅ " if use_emoji else ""
            stats_prefix = "📊 " if use_emoji else ""
            
            print(f"{success_prefix}播放历史已导出到 {filename}")
            print(f"{stats_prefix}包含 {export_data['export_info']['total_tracks']} 条播放记录和 {export_data['export_info']['total_sessions']} 个播放会话")
            
            logger.info(f"导出播放历史到 {filename}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            logger.error(f"导出失败: {e}")

    @staticmethod
    def export_to_file(filename: str) -> bool:
        """导出到指定文件"""
        try:
            export_data = db.export_data()
            if not export_data:
                print("❌ 没有数据可导出")
                return False
                
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            use_emoji = config.should_use_emoji()
            success_prefix = "✅ " if use_emoji else ""
            stats_prefix = "📊 " if use_emoji else ""
            
            print(f"{success_prefix}播放历史已导出到 {filename}")
            print(f"{stats_prefix}包含 {export_data['export_info']['total_tracks']} 条播放记录")
            
            logger.info(f"导出播放历史到 {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            logger.error(f"导出失败: {e}")
            return False
