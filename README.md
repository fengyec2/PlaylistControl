# Windows Media Tracker

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

一个轻量级的 Windows 媒体播放记录器，能够自动追踪和记录您在各种媒体应用中播放的音乐。

## ✨ 功能特性

- 🎵 **自动追踪**: 实时监控并记录正在播放的音乐
- 📊 **详细统计**: 提供播放次数、时长等统计信息
- 🔄 **多应用支持**: 兼容 Spotify、Apple Music、网易云音乐等主流音乐应用
- 💾 **数据导出**: 支持将播放历史导出为 JSON 格式
- 🔧 **多运行模式**: 交互模式、后台监控、守护进程
- ⚙️ **灵活配置**: 可自定义监控间隔、显示选项等
- 📝 **详细日志**: 完整的操作日志记录

## 🚀 快速开始

### 预编译版本（推荐）

1. 从 [Releases](https://github.com/fengyec2/windows-media-tracker/releases) 页面下载最新版本
2. 解压到任意目录
3. 运行 `MediaTracker.exe`

### 从源码安装

#### 系统要求

- Windows 10/11
- Python 3.8+

#### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/fengyec2/PlaylistControl.git
cd windows-media-tracker
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**
```bash
python main.py
```

## 📖 使用方法

### 命令行界面

```bash
# 交互模式（默认）
MediaTracker.exe

# 后台监控模式
MediaTracker.exe -b

# 守护进程模式（静默运行）
MediaTracker.exe -d

# 显示最近播放的歌曲
MediaTracker.exe -r 20

# 显示统计信息
MediaTracker.exe -s

# 导出播放历史
MediaTracker.exe -e playlist.json

# 停止后台运行的程序
MediaTracker.exe --stop

# 查看所有相关进程
MediaTracker.exe --list-processes
```

### 守护进程管理

**启动守护进程**:
```bash
MediaTracker.exe -d --pid-file daemon.pid
```

**停止守护进程**:
```bash
MediaTracker.exe --stop --pid-file daemon.pid
```

**检查状态**:
```bash
MediaTracker.exe --list-processes
```

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
    "default_interval": 1,
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

### 开发依赖

- `PyInstaller` - 用于打包可执行文件

完整依赖列表请参考 [`requirements.txt`](requirements.txt)

## 🏗️ 项目结构

```
windows-media-tracker/
├── main.py                # 主程序入口
├── config_manager.py      # 配置管理
├── config_editor.py       # 配置编辑模块
├── database.py            # 数据库操作
├── media_monitor.py       # 媒体监控核心
├── display_utils.py       # 显示工具
├── cli_parser.py          # 命令行参数解析模块
├── system_utils.py        # 系统工具模块
├── process_manager.py     # 进程管理模块
├── run_modes.py           # 导出功能模块
├── interactive_mode.py    # 命令行交互模式模块
├── logger.py              # 日志系统
├── build.py               # 打包脚本
├── config.json            # 配置文件（自动生成）
```

## 🔧 开发与构建

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/fengyec2/PlaylistControl.git
cd windows-media-tracker

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 构建可执行文件

```bash
python build.py
```

构建完成后，可执行文件将位于 `dist/MediaTracker.exe`


## 📋 版本历史

查看完整的变更日志：[CHANGELOG.md](CHANGELOG.md)


## 📄 许可证

本项目基于 **GNU General Public License v3.0** 开源协议发布。