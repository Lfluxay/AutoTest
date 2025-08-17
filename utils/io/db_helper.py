import pymysql
import sqlite3
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from utils.logging.logger import logger
from utils.config.parser import get_merged_config


class DatabaseHelper:
    """数据库操作辅助类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化数据库连接
        
        Args:
            config: 数据库配置
        """
        self.connection = None
        self.db_type = None
        
        if config is None:
            # 从全局配置获取数据库配置
            full_config = get_merged_config()
            config = full_config.get('database', {})
        
        self.config = config
        if config.get('enabled', False):
            self.connect()
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.db_type = self.config.get('type', 'mysql').lower()
            
            if self.db_type == 'mysql':
                self.connection = pymysql.connect(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 3306),
                    database=self.config.get('database'),
                    user=self.config.get('username'),
                    password=self.config.get('password'),
                    charset=self.config.get('charset', 'utf8mb4'),
                    autocommit=True,
                    cursorclass=pymysql.cursors.DictCursor
                )
                logger.info(f"MySQL数据库连接成功: {self.config.get('host')}:{self.config.get('port')}")
                
            elif self.db_type == 'sqlite':
                db_path = self.config.get('database', ':memory:')
                self.connection = sqlite3.connect(db_path)
                self.connection.row_factory = sqlite3.Row  # 返回字典格式结果
                logger.info(f"SQLite数据库连接成功: {db_path}")
                
            elif self.db_type == 'postgresql':
                try:
                    import psycopg2
                    import psycopg2.extras
                    self.connection = psycopg2.connect(
                        host=self.config.get('host', 'localhost'),
                        port=self.config.get('port', 5432),
                        database=self.config.get('database'),
                        user=self.config.get('username'),
                        password=self.config.get('password')
                    )
                    self.connection.autocommit = True
                    logger.info(f"PostgreSQL数据库连接成功: {self.config.get('host')}:{self.config.get('port')}")
                except ImportError:
                    logger.error("PostgreSQL驱动未安装，请安装 psycopg2-binary")
                    raise
            else:
                raise ValueError(f"不支持的数据库类型: {self.db_type}")
                
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询SQL
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            查询结果列表
        """
        if not self.connection:
            logger.error("数据库未连接")
            return []
        
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                if self.db_type == 'sqlite':
                    # SQLite返回Row对象，需要转换为字典
                    result = [dict(row) for row in cursor.fetchall()]
                elif self.db_type == 'postgresql':
                    # PostgreSQL使用DictCursor
                    import psycopg2.extras
                    cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    result = [dict(row) for row in cursor.fetchall()]
                else:
                    # MySQL已经配置了DictCursor
                    result = cursor.fetchall()
                
                logger.debug(f"执行查询成功: {sql[:100]}{'...' if len(sql) > 100 else ''}")
                logger.debug(f"查询结果数量: {len(result)}")
                return result
                
        except Exception as e:
            logger.error(f"执行查询失败: {sql}, 错误: {e}")
            raise
    
    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行更新SQL (INSERT, UPDATE, DELETE)
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            影响的行数
        """
        if not self.connection:
            logger.error("数据库未连接")
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                if params:
                    affected_rows = cursor.execute(sql, params)
                else:
                    affected_rows = cursor.execute(sql)
                
                # 对于不自动提交的数据库，需要手动提交
                if not getattr(self.connection, 'autocommit', True):
                    self.connection.commit()
                
                logger.debug(f"执行更新成功: {sql[:100]}{'...' if len(sql) > 100 else ''}")
                logger.debug(f"影响行数: {affected_rows}")
                return affected_rows
                
        except Exception as e:
            logger.error(f"执行更新失败: {sql}, 错误: {e}")
            if not getattr(self.connection, 'autocommit', True):
                self.connection.rollback()
            raise
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        批量执行SQL
        
        Args:
            sql: SQL语句
            params_list: 参数列表
            
        Returns:
            总影响行数
        """
        if not self.connection:
            logger.error("数据库未连接")
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)
                
                if not getattr(self.connection, 'autocommit', True):
                    self.connection.commit()
                
                logger.debug(f"批量执行成功: {sql[:100]}{'...' if len(sql) > 100 else ''}")
                logger.debug(f"执行数量: {len(params_list)}, 总影响行数: {affected_rows}")
                return affected_rows
                
        except Exception as e:
            logger.error(f"批量执行失败: {sql}, 错误: {e}")
            if not getattr(self.connection, 'autocommit', True):
                self.connection.rollback()
            raise
    
    def query_single(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        查询单条记录
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            单条记录或None
        """
        result = self.execute_query(sql, params)
        return result[0] if result else None
    
    def query_value(self, sql: str, params: tuple = None, column: str = None) -> Any:
        """
        查询单个值
        
        Args:
            sql: SQL语句
            params: 参数元组
            column: 列名，如果不指定则返回第一列的值
            
        Returns:
            单个值
        """
        result = self.query_single(sql, params)
        if result:
            if column:
                return result.get(column)
            else:
                return list(result.values())[0] if result else None
        return None
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            表是否存在
        """
        try:
            if self.db_type == 'mysql':
                sql = "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s"
                result = self.query_value(sql, (table_name,))
                return result > 0
            
            elif self.db_type == 'sqlite':
                sql = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?"
                result = self.query_value(sql, (table_name,))
                return result > 0
            
            elif self.db_type == 'postgresql':
                sql = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s"
                result = self.query_value(sql, (table_name,))
                return result > 0
            
            return False
            
        except Exception as e:
            logger.error(f"检查表存在性失败: {table_name}, 错误: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        获取表的列名
        
        Args:
            table_name: 表名
            
        Returns:
            列名列表
        """
        try:
            if self.db_type == 'mysql':
                sql = "SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = %s ORDER BY ordinal_position"
                result = self.execute_query(sql, (table_name,))
                return [row['column_name'] for row in result]
            
            elif self.db_type == 'sqlite':
                sql = f"PRAGMA table_info({table_name})"
                result = self.execute_query(sql)
                return [row['name'] for row in result]
            
            elif self.db_type == 'postgresql':
                sql = "SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position"
                result = self.execute_query(sql, (table_name,))
                return [row['column_name'] for row in result]
            
            return []
            
        except Exception as e:
            logger.error(f"获取表列名失败: {table_name}, 错误: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("数据库连接已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局数据库实例
db_helper = None

def get_db_helper() -> DatabaseHelper:
    """获取数据库帮助器实例"""
    global db_helper
    if db_helper is None:
        db_helper = DatabaseHelper()
    return db_helper

def execute_sql(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    """执行SQL查询便捷函数"""
    return get_db_helper().execute_query(sql, params)

def query_single(sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """查询单条记录便捷函数"""
    return get_db_helper().query_single(sql, params)

def query_value(sql: str, params: tuple = None, column: str = None) -> Any:
    """查询单个值便捷函数"""
    return get_db_helper().query_value(sql, params, column)