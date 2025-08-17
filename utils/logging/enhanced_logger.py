"""
增强的日志管理器
提供结构化日志、上下文管理、性能监控等功能
"""
import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from loguru import logger as loguru_logger
from utils.config_parser import get_merged_config


@dataclass
class LogContext:
    """日志上下文信息"""
    test_id: Optional[str] = None
    test_name: Optional[str] = None
    test_type: Optional[str] = None
    worker_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceLog:
    """性能日志记录"""
    operation: str
    duration: float
    timestamp: float
    success: bool
    details: Optional[Dict[str, Any]] = None


class EnhancedLogger:
    """增强的日志管理器"""
    
    def __init__(self):
        self._context_storage = threading.local()
        self._performance_logs: List[PerformanceLog] = []
        self._lock = threading.Lock()
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """设置日志配置"""
        config = get_merged_config().get('logging', {})
        
        # 移除默认handler
        loguru_logger.remove()
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 日志格式
        log_format = config.get('format', 
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}")
        
        # 控制台日志
        console_level = config.get('console_level', 'INFO')
        loguru_logger.add(
            sys.stdout,
            level=console_level,
            format=log_format,
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=self._log_filter
        )
        
        # 文件日志
        file_level = config.get('file_level', 'DEBUG')
        rotation = config.get('rotation', '100 MB')
        retention = config.get('retention', '30 days')
        compression = config.get('compression', 'zip')
        
        # 应用日志
        loguru_logger.add(
            logs_dir / "app.log",
            level=file_level,
            format=log_format,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            filter=self._log_filter
        )
        
        # 错误日志
        loguru_logger.add(
            logs_dir / "error.log",
            level="ERROR",
            format=log_format,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            filter=self._log_filter
        )
        
        # 结构化日志（JSON格式）
        loguru_logger.add(
            logs_dir / "structured.log",
            level=file_level,
            format="{message}",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            serialize=True,
            filter=lambda record: record["extra"].get("structured", False)
        )
        
        # 性能日志
        loguru_logger.add(
            logs_dir / "performance.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            filter=lambda record: record["extra"].get("performance", False)
        )
    
    def _log_filter(self, record) -> bool:
        """日志过滤器"""
        # 过滤掉结构化日志和性能日志
        return not record["extra"].get("structured", False) and not record["extra"].get("performance", False)
    
    def set_context(self, context: LogContext) -> None:
        """设置日志上下文"""
        self._context_storage.context = context
    
    def get_context(self) -> Optional[LogContext]:
        """获取当前日志上下文"""
        return getattr(self._context_storage, 'context', None)
    
    def clear_context(self) -> None:
        """清除日志上下文"""
        if hasattr(self._context_storage, 'context'):
            delattr(self._context_storage, 'context')
    
    @contextmanager
    def context_manager(self, context: LogContext):
        """日志上下文管理器"""
        old_context = self.get_context()
        self.set_context(context)
        try:
            yield
        finally:
            if old_context:
                self.set_context(old_context)
            else:
                self.clear_context()
    
    def _enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """丰富日志记录"""
        context = self.get_context()
        if context:
            record.update({
                "test_id": context.test_id,
                "test_name": context.test_name,
                "test_type": context.test_type,
                "worker_id": context.worker_id,
                "session_id": context.session_id,
                "request_id": context.request_id,
                "user_id": context.user_id,
            })
            if context.extra_data:
                record.update(context.extra_data)
        
        # 添加线程信息
        record["thread_id"] = threading.current_thread().ident
        record["thread_name"] = threading.current_thread().name
        
        return record
    
    def debug(self, message: str, **kwargs) -> None:
        """调试日志"""
        loguru_logger.debug(message, **self._enrich_record(kwargs))
    
    def info(self, message: str, **kwargs) -> None:
        """信息日志"""
        loguru_logger.info(message, **self._enrich_record(kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        """警告日志"""
        loguru_logger.warning(message, **self._enrich_record(kwargs))
    
    def error(self, message: str, **kwargs) -> None:
        """错误日志"""
        loguru_logger.error(message, **self._enrich_record(kwargs))
    
    def critical(self, message: str, **kwargs) -> None:
        """严重错误日志"""
        loguru_logger.critical(message, **self._enrich_record(kwargs))
    
    def structured_log(self, level: str, event: str, data: Dict[str, Any]) -> None:
        """结构化日志"""
        log_data = {
            "timestamp": time.time(),
            "level": level,
            "event": event,
            "data": data
        }
        log_data = self._enrich_record(log_data)
        
        loguru_logger.bind(structured=True).info(json.dumps(log_data, ensure_ascii=False))
    
    def performance_log(self, operation: str, duration: float, success: bool = True, 
                       details: Optional[Dict[str, Any]] = None) -> None:
        """性能日志"""
        perf_log = PerformanceLog(
            operation=operation,
            duration=duration,
            timestamp=time.time(),
            success=success,
            details=details
        )
        
        with self._lock:
            self._performance_logs.append(perf_log)
        
        # 记录到性能日志文件
        log_message = f"PERF | {operation} | {duration:.3f}s | {'SUCCESS' if success else 'FAILED'}"
        if details:
            log_message += f" | {json.dumps(details, ensure_ascii=False)}"
        
        loguru_logger.bind(performance=True).info(log_message)
    
    @contextmanager
    def performance_timer(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """性能计时器上下文管理器"""
        start_time = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            self.performance_log(operation, duration, success, details)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            if not self._performance_logs:
                return {"message": "没有性能数据"}
            
            total_operations = len(self._performance_logs)
            successful_operations = sum(1 for log in self._performance_logs if log.success)
            failed_operations = total_operations - successful_operations
            
            durations = [log.duration for log in self._performance_logs]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # 按操作类型统计
            operation_stats = {}
            for log in self._performance_logs:
                if log.operation not in operation_stats:
                    operation_stats[log.operation] = {
                        "count": 0,
                        "total_duration": 0.0,
                        "success_count": 0,
                        "failure_count": 0
                    }
                
                stats = operation_stats[log.operation]
                stats["count"] += 1
                stats["total_duration"] += log.duration
                if log.success:
                    stats["success_count"] += 1
                else:
                    stats["failure_count"] += 1
            
            # 计算平均时间
            for operation, stats in operation_stats.items():
                stats["avg_duration"] = stats["total_duration"] / stats["count"]
            
            return {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0,
                "avg_duration": avg_duration,
                "max_duration": max_duration,
                "min_duration": min_duration,
                "operation_stats": operation_stats
            }
    
    def clear_performance_logs(self) -> None:
        """清除性能日志"""
        with self._lock:
            self._performance_logs.clear()


# 全局增强日志实例
enhanced_logger = EnhancedLogger()

# 便捷函数
def debug(message: str, **kwargs) -> None:
    enhanced_logger.debug(message, **kwargs)

def info(message: str, **kwargs) -> None:
    enhanced_logger.info(message, **kwargs)

def warning(message: str, **kwargs) -> None:
    enhanced_logger.warning(message, **kwargs)

def error(message: str, **kwargs) -> None:
    enhanced_logger.error(message, **kwargs)

def critical(message: str, **kwargs) -> None:
    enhanced_logger.critical(message, **kwargs)

def structured_log(level: str, event: str, data: Dict[str, Any]) -> None:
    enhanced_logger.structured_log(level, event, data)

def performance_log(operation: str, duration: float, success: bool = True, 
                   details: Optional[Dict[str, Any]] = None) -> None:
    enhanced_logger.performance_log(operation, duration, success, details)

def set_log_context(context: LogContext) -> None:
    enhanced_logger.set_context(context)

def get_log_context() -> Optional[LogContext]:
    return enhanced_logger.get_context()

def clear_log_context() -> None:
    enhanced_logger.clear_context()
