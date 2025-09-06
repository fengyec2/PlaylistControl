import json
from config_manager import config

class ConfigEditor:
    @staticmethod
    def show_config_editor():
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
                ConfigEditor._show_current_config()
            elif choice == '2':
                ConfigEditor._modify_monitoring_interval()
            elif choice == '3':
                ConfigEditor._toggle_emoji_display()
            elif choice == '4':
                ConfigEditor._manage_ignored_apps()
            elif choice == '5':
                config.save_config()
            elif choice == '6':
                break
            else:
                print("❌ 无效的选择，请重试")

    @staticmethod
    def _show_current_config():
        """显示当前配置"""
        print("\n当前配置:")
        print(json.dumps(config.config, ensure_ascii=False, indent=2))

    @staticmethod
    def _modify_monitoring_interval():
        """修改监控间隔"""
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

    @staticmethod
    def _toggle_emoji_display():
        """切换emoji显示"""
        current = config.get("display.use_emoji", True)
        config.set("display.use_emoji", not current)
        status = "启用" if not current else "禁用"
        print(f"✅ Emoji显示已{status}")

    @staticmethod
    def _manage_ignored_apps():
        """管理忽略的应用"""
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
