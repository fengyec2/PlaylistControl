# display_utils.py
from datetime import datetime
from config.config_manager import config
from core.database import db
from utils.safe_print import safe_print

# Rich 库导入
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
# from rich.progress import Progress, BarColumn, TextColumn, MofNCompleteColumn
from rich.text import Text
# from rich.layout import Layout
# from rich.align import Align
from rich import box
# import math

class DisplayUtils:
    def __init__(self):
        self.console = Console()
    
    @staticmethod
    def show_recent_tracks(limit: int = None) -> None:
        """显示最近播放的歌曲"""
        if limit is None:
            limit = config.get("display.default_recent_limit", 10)
            
        records = db.get_recent_tracks(limit)
        
        if not records:
            safe_print("暂无播放记录")
            return
            
        use_emoji = config.should_use_emoji()
        timestamp_format = config.get_timestamp_format()
        
        title_prefix = "📋 " if use_emoji else ""
        safe_print(f"\n{title_prefix}最近 {len(records)} 首歌曲:")
        safe_print("=" * 80)
        
        for i, record in enumerate(records, 1):
            title, artist, album, album_artist, app_name, timestamp, duration, status, genre, year, track_number = record
            dt = datetime.fromisoformat(timestamp)
            
            song_prefix = "🎵 " if use_emoji else ""
            safe_print(f"{i:2d}. {song_prefix}{title}")
            
            if artist:
                artist_prefix = "🎤 " if use_emoji else ""
                safe_print(f"     {artist_prefix}{artist}")
                
            if album:
                album_prefix = "💿 " if use_emoji else ""
                safe_print(f"     {album_prefix}{album}")
                
            if album_artist and album_artist != artist:
                group_prefix = "👥 " if use_emoji else ""
                safe_print(f"     {group_prefix}专辑艺术家: {album_artist}")
                
            if config.get("display.show_track_number", True) and track_number:
                track_prefix = "🔢 " if use_emoji else ""
                safe_print(f"     {track_prefix}曲目号: {track_number}")
                
            if config.get("display.show_genre", True) and genre:
                genre_prefix = "🎭 " if use_emoji else ""
                safe_print(f"     {genre_prefix}流派: {genre}")
                
            if config.get("display.show_year", True) and year:
                year_prefix = "📅 " if use_emoji else ""
                safe_print(f"     {year_prefix}年份: {year}")
                
            if duration:
                duration_str = f"{duration//60}:{duration%60:02d}"
                time_prefix = "⏱️ " if use_emoji else ""
                safe_print(f"     {time_prefix}时长: {duration_str}")
                
            app_prefix = "📱 " if use_emoji else ""
            status_prefix = "⚡ " if use_emoji else ""
            time_stamp_prefix = "🕐 " if use_emoji else ""
            safe_print(f"     {app_prefix}{app_name} | {status_prefix}{status} | {time_stamp_prefix}{dt.strftime(timestamp_format)}")
            safe_print()
    
    def show_statistics(self) -> None:
        """增强版播放统计报告 —— Rich 可视化输出"""
        stats = db.get_statistics()
        
        if not stats:
            self.console.print("[red]暂无统计数据[/red]")
            return
        
        # 创建主标题
        title = Text("🎵 播放统计报告", style="bold magenta")
        title.justify = "center"
        
        # === 基础指标面板 ===
        basic_stats = self._create_basic_stats_panel(stats)
        
        # === 播放时间分布图表 ===
        hourly_chart = self._create_hourly_chart(stats.get('hourly_stats', []))
        
        # === 月度趋势图表 ===
        monthly_chart = self._create_monthly_chart(stats.get('monthly_stats', []))
        
        # === 排行榜表格 ===
        top_songs_table = self._create_top_songs_table(stats.get('top_songs', []))
        top_artists_table = self._create_top_artists_table(stats.get('top_artists', []))
        top_apps_table = self._create_top_apps_table(stats.get('top_apps', []))
        
        # === 最近7天活动图表 ===
        daily_chart = self._create_daily_chart(stats.get('daily_stats', []))
        
        # 输出所有内容
        self.console.print(Panel(title, expand=False))
        self.console.print()
        self.console.print(basic_stats)
        self.console.print()
        
        if hourly_chart:
            self.console.print(hourly_chart)
            self.console.print()
        
        if monthly_chart:
            self.console.print(monthly_chart)
            self.console.print()
        
        # 并排显示排行榜
        if top_songs_table or top_artists_table or top_apps_table:
            tables = []
            if top_songs_table:
                tables.append(top_songs_table)
            if top_artists_table:
                tables.append(top_artists_table)
            if top_apps_table:
                tables.append(top_apps_table)
            
            self.console.print(Columns(tables, equal=True, expand=True))
            self.console.print()
        
        if daily_chart:
            self.console.print(daily_chart)
    
    def _create_basic_stats_panel(self, stats) -> Panel:
        """创建基础统计面板"""
        total_plays = stats.get('total_plays', 0)
        unique_songs = stats.get('unique_songs', 0)
        
        content = f"""
[bold cyan]📊 核心指标[/bold cyan]
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📌 总播放记录: [yellow]{total_plays:,}[/yellow] 次         ┃
┃ 🎵 不同歌曲数: [green]{unique_songs:,}[/green] 首          ┃
┃ 🔄 平均重播率: [blue]{(total_plays/unique_songs if unique_songs > 0 else 0):.1f}[/blue] 次/首     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        """.strip()
        
        return Panel(content, title="📈 基础统计", border_style="blue")
    
    def _create_hourly_chart(self, hourly_stats) -> Panel:
        """创建按小时播放分布的ASCII图表"""
        if not hourly_stats:
            return None
        
        # 创建24小时完整数据（填充0）
        hour_data = {h: 0 for h in range(24)}
        for hour, count in hourly_stats:
            hour_data[hour] = count
        
        max_count = max(hour_data.values()) if hour_data.values() else 1
        
        content = "[bold cyan]⏰ 24小时播放分布[/bold cyan]\n\n"
        
        # 创建ASCII柱状图
        for hour in range(24):
            count = hour_data[hour]
            bar_length = int((count / max_count) * 30) if max_count > 0 else 0
            bar = "█" * bar_length
            
            # 根据时间段选择颜色
            if 6 <= hour < 12:
                color = "yellow"  # 早晨
            elif 12 <= hour < 18:
                color = "green"   # 下午
            elif 18 <= hour < 22:
                color = "red"     # 晚上
            else:
                color = "blue"    # 深夜/凌晨
            
            content += f"{hour:2d}:00 [{color}]{bar:30s}[/{color}] {count:4d}\n"
        
        return Panel(content, title="📊 播放时间热力图", border_style="cyan")
    
    def _create_monthly_chart(self, monthly_stats) -> Panel:
        """创建月度趋势图表"""
        if not monthly_stats:
            return None
        
        max_count = max(count for _, count in monthly_stats) if monthly_stats else 1
        
        content = "[bold cyan]📅 月度播放趋势[/bold cyan]\n\n"
        
        for month, count in monthly_stats:
            bar_length = int((count / max_count) * 40) if max_count > 0 else 0
            bar = "▉" * bar_length
            content += f"{month}: [green]{bar:40s}[/green] {count:,}\n"
        
        return Panel(content, title="📈 趋势分析", border_style="green")
    
    def _create_top_songs_table(self, top_songs) -> Table:
        """创建热门歌曲表格"""
        if not top_songs:
            return None
        
        table = Table(title="🏆 热门歌曲 TOP 10", box=box.ROUNDED)
        table.add_column("排名", style="cyan", width=6)
        table.add_column("歌曲", style="magenta", min_width=20)
        table.add_column("艺术家", style="green", min_width=15)
        table.add_column("播放次数", style="yellow", justify="right")
        
        for i, (title, artist, album, count) in enumerate(top_songs[:10], 1):
            # 截断过长的标题
            title_display = title[:25] + "..." if len(title) > 25 else title
            artist_display = artist[:20] + "..." if artist and len(artist) > 20 else (artist or "未知")
            
            table.add_row(
                f"{i}",
                title_display,
                artist_display,
                f"{count:,}"
            )
        
        return table
    
    def _create_top_artists_table(self, top_artists) -> Table:
        """创建热门艺术家表格"""
        if not top_artists:
            return None
        
        table = Table(title="🎤 热门艺术家 TOP 10", box=box.ROUNDED)
        table.add_column("排名", style="cyan", width=6)
        table.add_column("艺术家", style="green", min_width=20)
        table.add_column("播放次数", style="yellow", justify="right")
        table.add_column("占比", style="blue", justify="right")
        
        total_plays = sum(count for _, count in top_artists)
        
        for i, (artist, count) in enumerate(top_artists[:10], 1):
            artist_display = artist[:25] + "..." if len(artist) > 25 else artist
            percentage = (count / total_plays) * 100 if total_plays > 0 else 0
            
            table.add_row(
                f"{i}",
                artist_display,
                f"{count:,}",
                f"{percentage:.1f}%"
            )
        
        return table
    
    def _create_top_apps_table(self, top_apps) -> Table:
        """创建应用使用统计表格"""
        if not top_apps:
            return None
        
        table = Table(title="📱 应用使用统计", box=box.ROUNDED)
        table.add_column("排名", style="cyan", width=6)
        table.add_column("应用", style="blue", min_width=15)
        table.add_column("使用次数", style="yellow", justify="right")
        table.add_column("占比", style="green", justify="right")
        
        total_usage = sum(count for _, count in top_apps)
        
        for i, (app_name, count) in enumerate(top_apps, 1):
            percentage = (count / total_usage) * 100 if total_usage > 0 else 0
            
            table.add_row(
                f"{i}",
                app_name,
                f"{count:,}",
                f"{percentage:.1f}%"
            )
        
        return table
    
    def _create_daily_chart(self, daily_stats) -> Panel:
        """创建最近7天活动图表"""
        if not daily_stats:
            return None
        
        max_count = max(count for _, count in daily_stats) if daily_stats else 1
        
        content = "[bold cyan]📅 最近7天播放活动[/bold cyan]\n\n"
        
        for date, count in daily_stats:
            bar_length = int((count / max_count) * 35) if max_count > 0 else 0
            bar = "▓" * bar_length
            
            # 根据播放量选择颜色
            if count > max_count * 0.8:
                color = "red"      # 高活跃度
            elif count > max_count * 0.5:
                color = "yellow"   # 中等活跃度
            else:
                color = "green"    # 低活跃度
            
            content += f"{date}: [{color}]{bar:35s}[/{color}] {count:,}\n"
        
        return Panel(content, title="📊 近期活动", border_style="yellow")

# 全局显示工具实例
display = DisplayUtils()
