#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常处理框架
解决异常处理代码重复、错误信息不统一、缺乏统一错误码等问题
"""

import functools
import time
import traceback
import threading
from typing import Callable, Any, Optional, Dict, List, Type, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from utils.logging.logger import logger
from utils.core.exceptions import AutoTestException


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误分类"""
    CONFIG = "config"
    NETWORK = "network"
    DATABASE = "database"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """错误信息结构"""
    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    retry_able: bool = False
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_action: Optional[str] = None
    user_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ErrorRegistry:
    """错误注册表 - 统一管理错误码和信息"""
    
    def __init__(self):
        self._errors: Dict[str, ErrorInfo] = {}
        self._lock = threading.RLock()
        self._register_builtin_errors()
    
    def _register_builtin_errors(self):
        """注册内置错误"""
        builtin_errors = [
            ErrorInfo("CONFIG_001", "配置文件不存在", ErrorCategory.CONFIG, ErrorSeverity.HIGH),
            ErrorInfo("CONFIG_002", "配置文件格式错误", ErrorCategory.CONFIG, ErrorSeverity.HIGH),
            ErrorInfo("CONFIG_003", "配置项缺失", ErrorCategory.CONFIG, ErrorSeverity.MEDIUM),
            
            ErrorInfo("NETWORK_001", "网络连接超时", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, 
                     retry_able=True, max_retries=3, retry_delay=2.0),
            ErrorInfo("NETWORK_002", "网络连接失败", ErrorCategory.NETWORK, ErrorSeverity.HIGH,
                     retry_able=True, max_retries=2, retry_delay=5.0),
            ErrorInfo("NETWORK_003", "HTTP请求失败", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM,
                     retry_able=True, max_retries=3, retry_delay=1.0),
            
            ErrorInfo("DB_001", "数据库连接失败", ErrorCategory.DATABASE, ErrorSeverity.HIGH,
                     retry_able=True, max_retries=3, retry_delay=2.0),
            ErrorInfo("DB_002", "SQL执行错误", ErrorCategory.DATABASE, ErrorSeverity.MEDIUM),
            ErrorInfo("DB_003", "数据库事务失败", ErrorCategory.DATABASE, ErrorSeverity.HIGH),
            
            ErrorInfo("FILE_001", "文件不存在", ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM),
            ErrorInfo("FILE_002", "文件读取失败", ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM),
            ErrorInfo("FILE_003", "文件写入失败", ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM),
            ErrorInfo("FILE_004", "文件权限不足", ErrorCategory.FILE_IO, ErrorSeverity.HIGH),
            
            ErrorInfo("AUTH_001", "认证失败", ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            ErrorInfo("AUTH_002", "权限不足", ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            ErrorInfo("AUTH_003", "Token过期", ErrorCategory.AUTHENTICATION, ErrorSeverity.MEDIUM,
                     retry_able=True, max_retries=1),
            
            ErrorInfo("VALID_001", "参数验证失败", ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
            ErrorInfo("VALID_002", "数据格式错误", ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
            ErrorInfo("VALID_003", "必填字段缺失", ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
            
            ErrorInfo("SYS_001", "系统资源不足", ErrorCategory.SYSTEM, ErrorSeverity.HIGH),
            ErrorInfo("SYS_002", "系统调用失败", ErrorCategory.SYSTEM, ErrorSeverity.HIGH),
            ErrorInfo("SYS_003", "未知系统错误", ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
        ]
        
        for error in builtin_errors:
            self.register_error(error)
    
    def register_error(self, error_info: ErrorInfo):
        """注册错误信息"""
        with self._lock:
            self._errors[error_info.error_code] = error_info
    
    def get_error_info(self, error_code: str) -> Optional[ErrorInfo]:
        """获取错误信息"""
        return self._errors.get(error_code)
    
    def get_all_errors(self) -> Dict[str, ErrorInfo]:
        """获取所有错误信息"""
        return self._errors.copy()


class ExceptionFramework:
    """统一异常处理框架"""
    
    def __init__(self):
        self.error_registry = ErrorRegistry()
        self._retry_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def handle_with_retry(
        self,
        error_code: str = None,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        max_attempts: Optional[int] = None,
        delay: Optional[float] = None,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        on_failure: Optional[Callable[[Exception], Any]] = None
    ):
        """
        带重试的异常处理装饰器
        
        Args:
            error_code: 错误码，用于获取重试配置
            exceptions: 要捕获的异常类型
            max_attempts: 最大重试次数
            delay: 重试延迟
            backoff_factor: 退避因子
            max_delay: 最大延迟时间
            on_retry: 重试时的回调函数
            on_failure: 最终失败时的回调函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 获取错误信息配置
                error_info = None
                if error_code:
                    error_info = self.error_registry.get_error_info(error_code)
                
                # 确定重试参数
                attempts = max_attempts or (error_info.max_retries if error_info else 3)
                retry_delay = delay or (error_info.retry_delay if error_info else 1.0)
                
                last_exception = None
                
                for attempt in range(attempts):
                    try:
                        result = func(*args, **kwargs)
                        
                        # 记录成功统计
                        if attempt > 0:
                            self._record_retry_success(func.__name__, attempt)
                        
                        return result
                        
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < attempts - 1:  # 不是最后一次尝试
                            # 计算延迟时间
                            current_delay = min(retry_delay * (backoff_factor ** attempt), max_delay)
                            
                            # 调用重试回调
                            if on_retry:
                                try:
                                    on_retry(attempt + 1, e)
                                except Exception as callback_error:
                                    logger.error(f"重试回调函数执行失败: {callback_error}")
                            
                            logger.warning(f"函数 {func.__name__} 执行失败，{current_delay}秒后进行第{attempt + 2}次尝试: {e}")
                            time.sleep(current_delay)
                        else:
                            # 记录失败统计
                            self._record_retry_failure(func.__name__, attempts, e)
                
                # 所有重试都失败了
                if on_failure:
                    try:
                        return on_failure(last_exception)
                    except Exception as callback_error:
                        logger.error(f"失败回调函数执行失败: {callback_error}")
                
                # 包装异常
                if error_code and error_info:
                    wrapped_exception = AutoTestException(
                        error_info.message,
                        error_code=error_code,
                        details={
                            'original_exception': str(last_exception),
                            'attempts': attempts,
                            'function': func.__name__
                        }
                    )
                    raise wrapped_exception from last_exception
                else:
                    raise last_exception
            
            return wrapper
        return decorator
    
    def handle_with_fallback(
        self,
        fallback_func: Optional[Callable] = None,
        fallback_value: Any = None,
        error_code: str = None,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        log_error: bool = True,
        reraise: bool = False
    ):
        """
        带降级的异常处理装饰器
        
        Args:
            fallback_func: 降级函数
            fallback_value: 降级返回值
            error_code: 错误码
            exceptions: 要捕获的异常类型
            log_error: 是否记录错误日志
            reraise: 是否重新抛出异常
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if log_error:
                        error_info = self.error_registry.get_error_info(error_code) if error_code else None
                        message = error_info.message if error_info else f"执行 {func.__name__} 时发生异常"
                        logger.error(f"{message}: {str(e)}")
                    
                    if reraise:
                        raise
                    
                    # 执行降级逻辑
                    if fallback_func:
                        try:
                            return fallback_func(*args, **kwargs)
                        except Exception as fallback_error:
                            logger.error(f"降级函数执行失败: {fallback_error}")
                            return fallback_value
                    else:
                        return fallback_value
            
            return wrapper
        return decorator
    
    def handle_with_circuit_breaker(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        熔断器模式异常处理装饰器
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间
            expected_exception: 预期异常类型
        """
        def decorator(func: Callable) -> Callable:
            circuit_state = {
                'failure_count': 0,
                'last_failure_time': None,
                'state': 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
            }
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # 检查熔断器状态
                if circuit_state['state'] == 'OPEN':
                    if current_time - circuit_state['last_failure_time'] > recovery_timeout:
                        circuit_state['state'] = 'HALF_OPEN'
                        logger.info(f"熔断器半开状态: {func.__name__}")
                    else:
                        raise AutoTestException(
                            f"熔断器开启状态，拒绝调用: {func.__name__}",
                            error_code="CIRCUIT_BREAKER_OPEN"
                        )
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 成功时重置计数器
                    if circuit_state['state'] == 'HALF_OPEN':
                        circuit_state['state'] = 'CLOSED'
                        circuit_state['failure_count'] = 0
                        logger.info(f"熔断器关闭状态: {func.__name__}")
                    
                    return result
                    
                except expected_exception as e:
                    circuit_state['failure_count'] += 1
                    circuit_state['last_failure_time'] = current_time
                    
                    if circuit_state['failure_count'] >= failure_threshold:
                        circuit_state['state'] = 'OPEN'
                        logger.warning(f"熔断器开启: {func.__name__}, 失败次数: {circuit_state['failure_count']}")
                    
                    raise
            
            return wrapper
        return decorator
    
    def _record_retry_success(self, func_name: str, attempts: int):
        """记录重试成功统计"""
        with self._lock:
            if func_name not in self._retry_stats:
                self._retry_stats[func_name] = {
                    'success_count': 0,
                    'failure_count': 0,
                    'total_attempts': 0,
                    'avg_attempts': 0.0
                }
            
            stats = self._retry_stats[func_name]
            stats['success_count'] += 1
            stats['total_attempts'] += attempts
            stats['avg_attempts'] = stats['total_attempts'] / (stats['success_count'] + stats['failure_count'])
    
    def _record_retry_failure(self, func_name: str, attempts: int, exception: Exception):
        """记录重试失败统计"""
        with self._lock:
            if func_name not in self._retry_stats:
                self._retry_stats[func_name] = {
                    'success_count': 0,
                    'failure_count': 0,
                    'total_attempts': 0,
                    'avg_attempts': 0.0
                }
            
            stats = self._retry_stats[func_name]
            stats['failure_count'] += 1
            stats['total_attempts'] += attempts
            stats['avg_attempts'] = stats['total_attempts'] / (stats['success_count'] + stats['failure_count'])
    
    def get_retry_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取重试统计信息"""
        return self._retry_stats.copy()
    
    def clear_retry_stats(self):
        """清除重试统计信息"""
        with self._lock:
            self._retry_stats.clear()
    
    def create_exception(self, error_code: str, details: Dict[str, Any] = None) -> AutoTestException:
        """创建标准异常"""
        error_info = self.error_registry.get_error_info(error_code)
        if not error_info:
            return AutoTestException(f"未知错误码: {error_code}", error_code=error_code, details=details)
        
        return AutoTestException(
            error_info.message,
            error_code=error_code,
            details=details or {}
        )


# 全局异常处理框架实例
exception_framework = ExceptionFramework()

# 便捷装饰器函数
def retry_on_error(error_code: str = None, max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器便捷函数"""
    return exception_framework.handle_with_retry(
        error_code=error_code,
        max_attempts=max_attempts,
        delay=delay
    )

def fallback_on_error(fallback_value: Any = None, error_code: str = None):
    """降级装饰器便捷函数"""
    return exception_framework.handle_with_fallback(
        fallback_value=fallback_value,
        error_code=error_code
    )

def circuit_breaker(failure_threshold: int = 5, recovery_timeout: float = 60.0):
    """熔断器装饰器便捷函数"""
    return exception_framework.handle_with_circuit_breaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )
