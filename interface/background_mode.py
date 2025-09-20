# interface/background_mode.py
import asyncio
from utils.safe_print import safe_print
from utils.logger import logger
from config.config_manager import config

class BackgroundMode:
    def __init__(self, monitor):
        self.monitor = monitor
    
    async def run(self, interval=None, quiet=False):
        """运行后台监控模式"""
        if interval is None:
            interval = config.get_monitoring_interval()
        
        if not quiet:
            use_emoji = config.should_use_emoji()
            rocket_prefix = "🚀 " if use_emoji else ""
            safe_print(f"{rocket_prefix}开始后台监控模式...")
            safe_print(f"⏱️ 监控间隔: {interval}秒")
            safe_print("按 Ctrl+C 停止监控")
        
        logger.info(f"后台监控模式启动，间隔: {interval}秒")
        
        try:
            await self.monitor.monitor_media(interval)
        except KeyboardInterrupt:
            if not quiet:
                safe_print("\n后台监控已停止")
            logger.info("后台监控被用户中断")
        except Exception as e:
            error_msg = f"后台监控异常: {e}"
            if not quiet:
                safe_print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise
