"""
日志记录标准化工具
提供统一的日志记录接口和标准
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional
import time
import traceback
from utils.logging.logger import logger, logger_manager


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, operation_name: str, **context_data):
        self.operation_name = operation_name
        self.context_data = context_data
        self.start_time = None
    
    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()
        logger.info(f"[{self.operation_name}] 开始执行", extra=self.context_data)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            logger.info(
                f"[{self.operation_name}] 执行完成 | 耗时: {duration:.3f}s",
                extra=self.context_data
            )
        else:
            logger.error(
                f"[{self.operation_name}] 执行失败 | 耗时: {duration:.3f}s | 异常: {exc_val}",
                extra={**self.context_data, 'exception_type': exc_type.__name__}
            )
        
        return False  # 不抑制异常


def log_function_call(
    log_args: bool = True,
    log_result: bool = False,
    log_duration: bool = True,
    exclude_args: list = None,
    operation_name: str = None
):
    """
    函数调用日志装饰器
    
    Args:
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_duration: 是否记录执行时间
        exclude_args: 排除的参数名列表（例如密码等敏感信息）
        operation_name: 操作名称，默认使用函数名
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            # 记录函数调用开始
            log_data = {'function': func.__name__, 'module': func.__module__}
            
            if log_args:
                # 过滤敏感参数
                filtered_kwargs = kwargs.copy()
                if exclude_args:
                    for arg_name in exclude_args:
                        if arg_name in filtered_kwargs:
                            filtered_kwargs[arg_name] = "***HIDDEN***"
                
                log_data.update({
                    'args_count': len(args),
                    'kwargs': filtered_kwargs
                })
            
            logger.debug(f"[{op_name}] 函数调用开始", extra=log_data)
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录执行成功
                duration = time.time() - start_time
                success_data = {'function': func.__name__, 'success': True}
                
                if log_duration:
                    success_data['duration'] = f"{duration:.3f}s"
                
                if log_result and result is not None:
                    # 限制结果长度避免日志过长
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    success_data['result'] = result_str
                
                logger.debug(f"[{op_name}] 函数调用完成", extra=success_data)
                
                return result
                
            except Exception as e:
                # 记录执行失败
                duration = time.time() - start_time
                error_data = {
                    'function': func.__name__,
                    'success': False,
                    'duration': f"{duration:.3f}s",
                    'exception_type': type(e).__name__,
                    'exception_message': str(e)
                }
                
                logger.error(f"[{op_name}] 函数调用失败", extra=error_data)
                raise
        
        return wrapper
    return decorator


def log_test_step(step_name: str, description: str = ""):
    """
    测试步骤日志记录装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger_manager.log_step(step_name, description)
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"步骤执行成功: {step_name}")
                return result
            except Exception as e:
                logger.error(f"步骤执行失败: {step_name} | 错误: {str(e)}")
                raise
        
        return wrapper
    return decorator


def log_api_call(api_name: str = None):
    """
    API调用日志记录装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = api_name or func.__name__
            
            # 提取常见的API参数
            method = kwargs.get('method', 'UNKNOWN')
            url = kwargs.get('url', 'UNKNOWN')
            
            logger_manager.log_api_request(method, url)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 尝试获取状态码
                status_code = getattr(result, 'status_code', 'UNKNOWN')
                response_text = getattr(result, 'text', '')
                
                logger_manager.log_api_response(status_code, response_text, duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"API调用失败: {name} | {method} {url} | "
                    f"耗时: {duration:.3f}s | 错误: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def log_web_action(action_name: str = None):
    """
    Web操作日志记录装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = action_name or func.__name__
            
            # 提取常见的Web操作参数
            locator = kwargs.get('locator', kwargs.get('selector', ''))
            value = kwargs.get('value', kwargs.get('text', ''))
            
            logger_manager.log_web_action(name, locator, value)
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Web操作成功: {name}")
                return result
                
            except Exception as e:
                logger.error(f"Web操作失败: {name} | 错误: {str(e)}")
                raise
        
        return wrapper
    return decorator


class StandardLogger:
    """
    标准化日志记录器
    提供统一的日志记录方法
    """
    
    @staticmethod
    def log_test_case_start(case_name: str, case_data: Dict = None):
        """记录测试用例开始"""
        logger_manager.log_case_start(case_name)
        if case_data:
            logger.debug(f"用例数据: {case_data}")
    
    @staticmethod
    def log_test_case_end(case_name: str, result: str, duration: float = 0, error: str = None):
        """记录测试用例结束"""
        logger_manager.log_case_end(case_name, result, duration)
        if error:
            logger.error(f"用例执行错误: {error}")
    
    @staticmethod
    def log_assertion(assertion_type: str, expected: Any, actual: Any, result: bool, message: str = ""):
        """记录断言结果"""
        logger_manager.log_assertion(assertion_type, str(expected), str(actual), result)
        if message:
            logger.info(f"断言说明: {message}")
    
    @staticmethod
    def log_data_extraction(extract_type: str, source: str, target: str, result: Any):
        """记录数据提取"""
        success = result is not None
        status = "成功" if success else "失败"
        
        logger.info(
            f"数据提取{status}: {extract_type} | {source} -> {target} | 结果: {result}"
        )
    
    @staticmethod
    def log_configuration_loaded(config_file: str, config_keys: list):
        """记录配置加载"""
        logger.info(
            f"配置加载完成: {config_file} | "
            f"包含配置项: {', '.join(config_keys) if config_keys else 'None'}"
        )
    
    @staticmethod
    def log_file_operation(operation: str, file_path: str, success: bool, error: str = None):
        """记录文件操作"""
        status = "成功" if success else "失败"
        message = f"文件{operation}{status}: {file_path}"
        
        if success:
            logger.info(message)
        else:
            logger.error(f"{message} | 错误: {error}")
    
    @staticmethod
    def log_database_operation(operation: str, query: str, affected_rows: int = None, error: str = None):
        """记录数据库操作"""
        if error:
            logger.error(f"数据库{operation}失败: {query[:100]}... | 错误: {error}")
        else:
            logger.info(
                f"数据库{operation}成功: {query[:100]}..." +
                (f" | 影响行数: {affected_rows}" if affected_rows is not None else "")
            )
    
    @staticmethod
    def log_performance_metric(metric_name: str, value: float, unit: str = "", threshold: float = None):
        """记录性能指标"""
        message = f"性能指标: {metric_name} = {value}{unit}"
        
        if threshold is not None:
            if value > threshold:
                message += f" | ⚠️ 超过阈值 {threshold}{unit}"
                logger.warning(message)
            else:
                message += f" | ✓ 低于阈值 {threshold}{unit}"
                logger.info(message)
        else:
            logger.info(message)
    
    @staticmethod
    def log_exception_details(exception: Exception, context: Dict = None):
        """记录异常详情"""
        exc_data = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback.format_exc()
        }
        
        if context:
            exc_data.update(context)
        
        logger.error(f"异常发生: {type(exception).__name__}", extra=exc_data)


# 导出的便捷函数
def with_logging(operation_name: str = None):
    """便捷的日志装饰器"""
    return log_function_call(operation_name=operation_name, log_duration=True)


def with_test_logging(step_name: str, description: str = ""):
    """便捷的测试步骤日志装饰器"""
    return log_test_step(step_name, description)


# 全局标准日志实例
standard_logger = StandardLogger()