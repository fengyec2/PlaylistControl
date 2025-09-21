# PlaylistControl

一个轻量级的 Windows 媒体播放记录器，能够自动追踪和记录您在各种媒体应用中播放的音乐。

## ✨ 功能特性

- 🎵 **自动追踪**: 实时监控并记录正在播放的音乐
- 📊 **详细统计**: 提供播放次数、时长等统计信息
- 🔄 **多应用支持**: 兼容 Spotify、Apple Music、网易云音乐等支持 SMTC 的应用
- 💾 **数据导出**: 支持将播放历史导出为 JSON 格式
- 🔧 **多运行模式**: 交互模式、后台监控、守护进程
- ⚙️ **灵活配置**: 可自定义监控间隔、显示选项等
- 📝 **详细日志**: 完整的操作日志记录

### 参数详解

| 参数 | 长参数 | 描述 |
|------|--------|------|
| `-b` | `--background` | 后台监控模式，可看到输出但在后台运行 |
| `-d` | `--daemon` | 守护进程模式，完全静默后台运行 |
| `-r N` | `--recent N` | 显示最近 N 首播放的歌曲 |
| `-s` | `--stats` | 显示播放统计信息 |
| `-e FILE` | `--export FILE` | 导出播放历史到指定文件 |
| | `--stop` | 停止后台运行的程序 |
| `-i SECONDS` | `--interval SECONDS` | 设置监控间隔（秒） |
| | `--pid-file FILE` | 指定 PID 文件路径 |
| | `--no-emoji` | 禁用 Emoji 显示 |
| `-q` | `--quiet` | 静默模式，减少输出 |
| `-v` | `--verbose` | 详细输出模式 |
| | `--version` | 显示程序版本 |


### 配置选项

程序会在运行目录创建 `config.json` 配置文件，您可以修改以下设置：

```json
{
  "database": {
    "path": "media_history.db",
    "auto_backup": true,
    "backup_interval_days": 7
  },
  "monitoring": {
    "default_interval": 5,
    "min_interval": 1,
    "max_interval": 60,
    "auto_start": false,
    "duplicate_threshold_minutes": 1
  },
  "display": {
    "use_emoji": true,
    "show_progress": true,
    "show_genre": true,
    "show_year": true,
    "show_track_number": true,
    "default_recent_limit": 10,
    "timestamp_format": "%Y-%m-%d %H:%M:%S"
  },
  "export": {
    "default_filename": "media_history.json",
    "include_sessions": true,
    "include_statistics": true,
    "auto_export": false,
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
    "enabled": true,
    "level": "INFO",
    "file": "media_tracker.log",
    "max_size_mb": 10,
    "backup_count": 3
  }
}
```

## 🛠️ 依赖项

### 运行时依赖

- `winsdk` - Windows SDK 接口
- `psutil` - 进程和系统信息
- `sqlite3` - 数据库存储（Python 内置）


## 🏗️ 项目结构

```
PlaylistControl/
├── main.py                    # 主程序入口
├── build.py                   # 打包脚本
├── core/                      # 核心功能模块
│   ├── media_monitor.py       # 媒体监控核心
│   ├── database.py            # 数据库操作
│   └── process_manager.py     # 进程管理
├── config/                    # 配置相关
│   ├── config_manager.py      # 配置管理
│   └── config_editor.py       # 配置编辑
├── interface/                 # 用户界面相关
│   ├── cli_parser.py          # 命令行解析
│   ├── app_launcher.py        # 应用启动器
│   ├── interactive_mode.py    # 交互模式
│   ├── background_mode.py     # 后台模式
│   └── daemon_mode.py         # 守护进程模式
├── utils/                     # 工具模块
│   ├── display_utils.py       # 显示工具
│   ├── system_utils.py        # 系统工具
│   ├── safe_print.py          # 安全打印
│   ├── export_manager.py      # 导出工具
│   └── logger.py              # 日志系统
└── resources/                 # 资源文件
```
