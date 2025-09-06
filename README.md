# Windows 媒体播放记录器 v4.0

一个功能强大的Windows媒体播放监控和记录工具，支持所有兼容Windows Media Transport Controls的应用。

## 🚀 主要功能

- 🎧 实时监控媒体播放
- 💾 自动保存播放历史
- 📊 详细的播放统计分析
- ⚙️ 灵活的配置管理
- 🎨 美观的界面显示
- 📱 支持多种音乐应用

## 📁 项目结构

```
media_tracker/
├── main.py              # 主程序入口
├── config_manager.py    # 配置管理器
├── database.py          # 数据库管理器
├── media_monitor.py     # 媒体监控器
├── display_utils.py     # 显示工具
├── logger.py           # 日志管理器
├── install.py          # 安装脚本
├── config.json         # 配置文件
├── README.md           # 项目说明
└── 启动媒体记录器.bat   # Windows启动脚本
```

## 🔧 安装和使用

### 快速安装
```bash
python install.py
```

### 手动安装
```bash
pip install winsdk
python main.py
```

### Windows一键启动
双击 `启动媒体记录器.bat`

## ⚙️ 配置说明

所有配置都保存在 `config.json` 文件中，支持以下配置：

- **数据库设置**: 路径、自动备份等
- **监控设置**: 间隔时间、去重阈值等  
- **显示设置**: emoji、进度显示、时间格式等
- **导出设置**: 文件名、包含内容等
- **应用设置**: 名称映射、忽略列表等
- **日志设置**: 级别、文件大小等

## 📱 支持的应用

- Spotify, VLC, Windows Media Player, iTunes
- 网易云音乐, QQ音乐, 酷狗音乐, 酷我音乐
- Chrome, Firefox, Edge (网页音乐)
- 所有支持Windows Media Transport Controls的应用

## 📊 功能特点

- **智能去重**: 避免短时间内重复记录
- **会话管理**: 记录完整的播放会话
- **统计分析**: 最常播放歌曲、艺术家、应用等
- **数据导出**: JSON格式完整导出
- **自动备份**: 定期备份数据库
- **日志记录**: 详细的运行日志

## 🛠️ 技术栈

- Python 3.7+
- Windows SDK (winsdk)
- SQLite数据库
- asyncio异步编程
- Windows Media Transport Controls API

## 📄 许可证

GPLv3 License
```

## 使用方法

1. **安装依赖**：
   ```bash
   python install.py
   ```

2. **运行程序**：
   ```bash
   python main.py
   ```

3. **配置自定义**：
   编辑 `config.json` 文件来自定义各种设置

## 主要改进

1. **模块化设计**：将功能拆分到不同文件中，提高可维护性
2. **外部配置**：所有设置都可以通过JSON文件配置
3. **日志系统**：完整的日志记录和管理
4. **配置编辑器**：程序内置的配置修改功能
5. **自动安装**：一键安装脚本和启动脚本
6. **错误处理**：更好的异常处理和用户提示
7. **数据备份**：自动数据库备份功能
