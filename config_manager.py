# config_manager.py
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self.load_config()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "database": {
                "path": "media_history.db",
                "auto_backup": True,
                "backup_interval_days": 7
            },
            "monitoring": {
                "default_interval": 5,
                "min_interval": 1,
                "max_interval": 60,
                "auto_start": False,
                "duplicate_threshold_minutes": 1
            },
            "display": {
                "use_emoji": True,
                "show_progress": True,
                "show_genre": True,
                "show_year": True,
                "show_track_number": True,
                "default_recent_limit": 10,
                "timestamp_format": "%Y-%m-%d %H:%M:%S"
            },
            "export": {
                "default_filename": "media_history.json",
                "include_sessions": True,
                "include_statistics": True,
                "auto_export": False,
                "auto_export_interval_days": 30
            },
            "apps": {
                "name_mapping": {
                    "Spotify.exe": "Spotify",
                    "Microsoft.ZuneMusic": "Groove 音乐",
                    "Microsoft.WindowsMediaPlayer": "Windows Media Player",
                    "VLC.exe": "VLC Media Player",
                    "iTunes.exe": "iTunes",
                    "chrome.exe": "Google Chrome",
                    "firefox.exe": "Mozilla Firefox",
                    "msedge.exe": "Microsoft Edge",
                    "CloudMusic.exe": "网易云音乐",
                    "QQMusic.exe": "QQ音乐",
                    "KugouMusic.exe": "酷狗音乐",
                    "KuwoMusic.exe": "酷我音乐",
                    "opera.exe": "Opera Browser"
                },
                "ignored_apps": []
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "file": "media_tracker.log",
                "max_size_mb": 10,
                "backup_count": 3
            }
        }
        
    def load_config(self) -> None:
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self.config, file_config)
                print(f"✅ 配置文件已加载: {self.config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}")
                print("使用默认配置")
        else:
            # 创建默认配置文件
            self.save_config()
            print(f"📄 已创建默认配置文件: {self.config_file}")
            
    def _merge_config(self, default: Dict[str, Any], override: Dict[str, Any]) -> None:
        """递归合并配置"""
        for key, value in override.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
                
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"💾 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
        
    def set(self, key_path: str, value: Any) -> None:
        """设置配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        current[keys[-1]] = value
        
    def get_app_name(self, app_id: str) -> str:
        """获取应用的显示名称"""
        name_mapping = self.get("apps.name_mapping", {})
        return name_mapping.get(app_id, app_id)
        
    def is_app_ignored(self, app_id: str) -> bool:
        """检查应用是否被忽略"""
        ignored_apps = self.get("apps.ignored_apps", [])
        return app_id in ignored_apps
        
    def get_timestamp_format(self) -> str:
        """获取时间戳格式"""
        return self.get("display.timestamp_format", "%Y-%m-%d %H:%M:%S")
        
    def should_use_emoji(self) -> bool:
        """是否使用emoji"""
        return self.get("display.use_emoji", True)
        
    def get_monitoring_interval(self) -> int:
        """获取监控间隔"""
        interval = self.get("monitoring.default_interval", 5)
        min_interval = self.get("monitoring.min_interval", 1)
        max_interval = self.get("monitoring.max_interval", 60)
        return max(min_interval, min(max_interval, interval))

# 全局配置实例
config = ConfigManager()
