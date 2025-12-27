"""
数据库连接管理
"""
import sqlite3
from contextlib import contextmanager
from typing import Optional
from utils.logger import logger


class DatabaseConnection:
    """数据库连接管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """上下文管理器 - 自动管理连接的打开和关闭"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[tuple]:
        """执行查询并返回单条结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作并返回受影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount