"""
数据库备份管理
"""
import os
import shutil
from datetime import datetime, timedelta
from config.config_manager import config
from utils.logger import logger


class BackupManager:
    """数据库备份管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        from utils.system_utils import get_executable_dir
        self.backup_dir = os.path.join(get_executable_dir(), "backups")
    
    def check_and_backup(self) -> None:
        """检查是否需要备份并执行"""
        if not config.get("database.auto_backup", True):
            return
        
        backup_interval = config.get("database.backup_interval_days", 7)
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # 查找最新的备份文件
        backup_files = self._get_backup_files()
        
        if backup_files:
            latest_backup = os.path.join(self.backup_dir, backup_files[0])
            backup_time = datetime.fromtimestamp(os.path.getmtime(latest_backup))
            
            if datetime.now() - backup_time < timedelta(days=backup_interval):
                return  # 不需要备份
        
        # 创建备份
        self.create_backup()
    
    def create_backup(self) -> bool:
        """创建数据库备份"""
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"media_history_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_file)
            
            from utils.safe_print import safe_print
            safe_print(f"💾 数据库备份已创建: {backup_file}")
            
            # 清理旧备份
            self.cleanup_old_backups()
            return True
            
        except Exception as e:
            from utils.safe_print import safe_print
            safe_print(f"❌ 创建数据库备份失败: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> None:
        """清理旧备份文件"""
        try:
            backup_files = self._get_backup_files()
            
            if len(backup_files) <= keep_count:
                return
            
            # 删除多余的备份文件
            for filename in backup_files[keep_count:]:
                file_path = os.path.join(self.backup_dir, filename)
                os.remove(file_path)
                from utils.safe_print import safe_print
                safe_print(f"🗑️ 已删除旧备份: {filename}")
                
        except Exception as e:
            from utils.safe_print import safe_print
            safe_print(f"⚠️ 清理旧备份文件失败: {e}")
    
    def _get_backup_files(self) -> list:
        """获取所有备份文件，按时间倒序排序"""
        if not os.path.exists(self.backup_dir):
            return []
        
        backup_files = [
            f for f in os.listdir(self.backup_dir)
            if f.startswith("media_history_") and f.endswith(".db")
        ]
        
        # 按修改时间排序（最新的在前）
        backup_files_with_time = []
        for f in backup_files:
            file_path = os.path.join(self.backup_dir, f)
            mtime = os.path.getmtime(file_path)
            backup_files_with_time.append((mtime, f))
        
        backup_files_with_time.sort(reverse=True)
        return [f for _, f in backup_files_with_time]