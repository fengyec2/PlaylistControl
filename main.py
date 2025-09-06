# main.py
import asyncio
import json
import os
from datetime import datetime
from config_manager import config
from database import db
from media_monitor import monitor
from display_utils import display
from logger import logger

def check_and_install_dependencies() -> bool:
    """检查并安装依赖"""
    try:
        import winsdk.windows.media.control as wmc
        return True
    except ImportError:
        print("❌ 缺少必要的 winsdk 库")
        print("🔧 正在尝试自动安装...")
        
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "winsdk"])
            print("✅ winsdk 安装成功!")
            print("🔄 请重新运行程序")
            return False
        except Exception as e:
            print(f"❌ 自动安装失败: {e}")
            print("🛠️ 请手动执行: pip install winsdk")
            return False

def export_history() -> None:
    """导出播放历史"""
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

def show_config_editor() -> None:
    """显示配置编辑器"""
    while True:
        print("\n⚙️ 配置编辑器:")
        print("1. 📊 显示当前配置")
        print("2. ⏱️ 修改监控间隔")
        print("3. 🎨 切换emoji显示")
        print("4. 📱 管理忽略的应用")
        print("5. 💾 保存配置")
        print("6. 🔙 返回主菜单")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == '1':
            print("\n当前配置:")
            print(json.dumps(config.config, ensure_ascii=False, indent=2))
            
        elif choice == '2':
            current = config.get("monitoring.default_interval", 5)
            new_interval = input(f"新的监控间隔 (当前: {current}秒): ").strip()
            try:
                interval = int(new_interval)
                if 1 <= interval <= 60:
                    config.set("monitoring.default_interval", interval)
                    print(f"✅ 监控间隔已设置为 {interval}秒")
                else:
                    print("❌ 间隔必须在1-60秒之间")
            except ValueError:
                print("❌ 请输入有效的数字")
                
        elif choice == '3':
            current = config.get("display.use_emoji", True)
            config.set("display.use_emoji", not current)
            status = "启用" if not current else "禁用"
            print(f"✅ Emoji显示已{status}")
            
        elif choice == '4':
            ignored_apps = config.get("apps.ignored_apps", [])
            print(f"\n当前忽略的应用: {ignored_apps}")
            
            action = input("添加(a)/删除(d)/清空(c)忽略列表: ").strip().lower()
            if action == 'a':
                app = input("输入要忽略的应用ID: ").strip()
                if app and app not in ignored_apps:
                    ignored_apps.append(app)
                    config.set("apps.ignored_apps", ignored_apps)
                    print(f"✅ 已添加 {app} 到忽略列表")
                    
            elif action == 'd':
                if ignored_apps:
                    app = input("输入要移除的应用ID: ").strip()
                    if app in ignored_apps:
                        ignored_apps.remove(app)
                        config.set("apps.ignored_apps", ignored_apps)
                        print(f"✅ 已从忽略列表移除 {app}")
                    else:
                        print("❌ 应用不在忽略列表中")
                else:
                    print("忽略列表为空")
                    
            elif action == 'c':
                config.set("apps.ignored_apps", [])
                print("✅ 忽略列表已清空")
                
        elif choice == '5':
            config.save_config()
            
        elif choice == '6':
            break
            
        else:
            print("❌ 无效的选择，请重试")

def main():
    if not check_and_install_dependencies():
        return
        
    use_emoji = config.should_use_emoji()
    
    title_prefix = "🎵 " if use_emoji else ""
    print(f"{title_prefix}Windows 媒体播放记录器 v4.0")
    print("=" * 50)
    
    feature_prefix = "🚀 " if use_emoji else ""
    support_prefix = "📱 " if use_emoji else ""
    save_prefix = "💾 " if use_emoji else ""
    
    print(f"{feature_prefix}使用 Windows Media Transport Controls API")
    print(f"{support_prefix}支持所有兼容的媒体应用")
    print(f"{save_prefix}自动保存播放历史和统计信息")
    
    logger.info("程序启动")
    
    # 检查自动启动
    if config.get("monitoring.auto_start", False):
        print("\n🚀 自动启动监控...")
        try:
            asyncio.run(monitor.monitor_media())
        except Exception as e:
            logger.error(f"自动监控失败: {e}")
    
    while True:
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
                    
                asyncio.run(monitor.monitor_media(interval))
                
            except ValueError:
                print(f"⚠️ 无效的间隔时间，使用默认值{config.get_monitoring_interval()}秒")
                asyncio.run(monitor.monitor_media())
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                logger.error(f"监控出错: {e}")
                
        elif choice == '2':
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
                
        elif choice == '3':
            display.show_statistics()
            
        elif choice == '4':
            export_history()
            
        elif choice == '5':
            show_config_editor()
            
        elif choice == '6':
            wave_prefix = "👋 " if use_emoji else ""
            print(f"{wave_prefix}再见!")
            logger.info("程序退出")
            break
            
        else:
            print("❌ 无效的选择，请重试")

if __name__ == "__main__":
    main()
