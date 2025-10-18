# config_manager.py
import json
import os
from typing import Dict, Any, Optional
from utils.safe_print import safe_print

# 全局变量控制调试输出
_verbose_mode = False

def set_verbose_mode(verbose: bool):
    """设置详细输出模式"""
    global _verbose_mode
    _verbose_mode = verbose

def debug_print(message):
    """只在 verbose 模式下打印调试信息"""
    if _verbose_mode:
        safe_print(message)

class VersionInfo:
    """版本信息类 - 不会被保存到配置文件"""
    VERSION = "2.5.0"
    VERSION_TUPLE = (2, 5, 0, 0)
    APP_NAME = "PlaylistControl"
    AUTHOR = "fengyec2"
    COMPANY = "https://github.com/fengyec2/PlaylistControl"
    DESCRIPTION = "PlaylistControl"
    
    @classmethod
    def get_version(cls) -> str:
        """获取版本号"""
        return cls.VERSION
    
    @classmethod
    def get_version_tuple(cls) -> tuple:
        """获取版本元组"""
        return cls.VERSION_TUPLE
    
    @classmethod
    def get_app_name(cls) -> str:
        """获取应用名称"""
        return cls.APP_NAME
    
    @classmethod
    def get_copyright(cls) -> str:
        """获取版权信息"""
        return f"Copyright © 2025 {cls.AUTHOR}"
    
    @classmethod
    def get_full_name(cls) -> str:
        """获取完整应用名称和版本"""
        return f"{cls.APP_NAME} v{cls.VERSION}"

class ConfigManager:
    def __init__(self, config_file: str = None):
        # 导入放在这里避免循环导入
        from utils.system_utils import get_config_file_path, get_database_path, get_log_file_path
        
        # 如果没有指定配置文件路径，使用默认路径
        if config_file is None:
            self.config_file = get_config_file_path()
        else:
            # 如果指定了配置文件，但不是绝对路径，则相对于可执行文件目录
            if not os.path.isabs(config_file):
                from utils.system_utils import get_executable_dir
                self.config_file = os.path.join(get_executable_dir(), config_file)
            else:
                self.config_file = config_file
        
        # 获取其他文件的正确路径
        self.database_path = get_database_path()
        self.log_file_path = get_log_file_path()
        
        debug_print(f"🔧 调试：配置文件路径: {self.config_file}")
        debug_print(f"🔧 调试：数据库路径: {self.database_path}")
        debug_print(f"🔧 调试：日志文件路径: {self.log_file_path}")
        
        self.config = self._load_default_config()
        self.load_config()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "database": {
                "path": self.database_path,  # 使用正确的数据库路径
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
                "file": self.log_file_path,  # 使用正确的日志文件路径
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
                try:
                    safe_print(f"✅ 配置文件已加载: {self.config_file}")
                except UnicodeEncodeError:
                    safe_print(f"[OK] 配置文件已加载: {self.config_file}")
            except Exception as e:
                safe_print(f"⚠️ 加载配置文件失败: {e}")
                safe_print("使用默认配置")
        else:
            # 创建默认配置文件
            self.save_config()
            safe_print(f"📄 已创建默认配置文件: {self.config_file}")
            
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
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            safe_print(f"💾 配置已保存到: {self.config_file}")
        except Exception as e:
            safe_print(f"❌ 保存配置失败: {e}")
            
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
    
    def get_database_path(self) -> str:
        """获取数据库文件路径"""
        # 优先使用配置中的路径，如果是相对路径则相对于可执行文件目录
        db_path = self.get("database.path", self.database_path)
        if not os.path.isabs(db_path):
            from utils.system_utils import get_executable_dir
            db_path = os.path.join(get_executable_dir(), db_path)
        return db_path
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        # 优先使用配置中的路径，如果是相对路径则相对于可执行文件目录
        log_path = self.get("logging.file", self.log_file_path)
        if not os.path.isabs(log_path):
            from utils.system_utils import get_executable_dir
            log_path = os.path.join(get_executable_dir(), log_path)
        return log_path
    
    def get_export_file_path(self, filename: str = None) -> str:
        """获取导出文件路径"""
        if filename is None:
            filename = self.get("export.default_filename", "media_history.json")
        
        if not os.path.isabs(filename):
            from utils.system_utils import get_executable_dir
            filename = os.path.join(get_executable_dir(), filename)
        return filename

# 全局配置实例
config = ConfigManager()
# 版本信息实例
version_info = VersionInfo()
