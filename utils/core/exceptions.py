"""
自定义异常类模块
定义框架中使用的各种异常类型
"""
from typing import Dict, Any, Optional


class AutoTestException(Exception):
    """自动化测试框架基础异常"""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        result = f"[{self.__class__.__name__}]"
        if self.error_code:
            result += f"({self.error_code})"
        result += f": {self.message}"
        if self.details:
            result += f" | 详情: {self.details}"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式"""
        return {
            'exception_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ConfigException(AutoTestException):
    """配置相关异常"""
    pass


class DataParsingException(AutoTestException):
    """数据解析异常"""
    pass


class APIException(AutoTestException):
    """API测试异常"""
    pass


class AuthenticationError(APIException):
    """认证失败异常"""
    pass


class APIRequestError(APIException):
    """API请求异常"""
    
    def __init__(self, message: str, status_code: int = None, response_text: str = None, 
                 error_code: str = None):
        super().__init__(message, error_code)
        self.status_code = status_code
        self.response_text = response_text
        self.details.update({
            'status_code': status_code,
            'response_text': response_text[:500] if response_text else None
        })


class WebException(AutoTestException):
    """Web测试异常"""
    pass


class ElementNotFoundException(WebException):
    """页面元素未找到异常"""
    pass


class PageLoadException(WebException):
    """页面加载异常"""
    pass


class BrowserException(WebException):
    """浏览器操作异常"""
    pass


class AssertionException(AutoTestException):
    """断言异常"""
    
    def __init__(self, message: str, expected: str = None, actual: str = None, 
                 assertion_type: str = None):
        super().__init__(message)
        self.expected = expected
        self.actual = actual
        self.assertion_type = assertion_type
        self.details.update({
            'expected': expected,
            'actual': actual,
            'assertion_type': assertion_type
        })


class DatabaseException(AutoTestException):
    """数据库操作异常"""
    pass


class FileException(AutoTestException):
    """文件操作异常"""
    pass


class VariableException(AutoTestException):
    """变量管理异常"""
    pass


class ReportException(AutoTestException):
    """报告生成异常"""
    pass


class NotificationException(AutoTestException):
    """通知发送异常"""
    pass


# 异常处理装饰器
import functools
from typing import Callable, Any
from utils.logging.logger import logger


def handle_exceptions(
    exception_type: type = AutoTestException,
    log_error: bool = True,
    reraise: bool = True,
    default_return: Any = None,
    error_message: Optional[str] = None
):
    """
    异常处理装饰器
    
    Args:
        exception_type: 要捕获的异常类型
        log_error: 是否记录错误日志
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值
        error_message: 自定义错误消息
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                if log_error:
                    custom_msg = error_message or f"执行 {func.__name__} 时发生异常"
                    logger.error(f"{custom_msg}: {str(e)}")
                
                if reraise:
                    raise
                else:
                    return default_return
            except Exception as e:
                if log_error:
                    logger.error(f"执行 {func.__name__} 时发生未预期异常: {str(e)}")
                
                if reraise:
                    # 将未知异常包装为框架异常
                    wrapped_exception = AutoTestException(
                        f"执行 {func.__name__} 时发生未预期异常: {str(e)}",
                        error_code="UNEXPECTED_ERROR",
                        details={'original_exception': type(e).__name__}
                    )
                    raise wrapped_exception from e
                else:
                    return default_return
        
        return wrapper
    return decorator


def retry_on_exception(
    exception_types: tuple = (Exception,),
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
):
    """
    异常重试装饰器
    
    Args:
        exception_types: 需要重试的异常类型
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间递增因子
        max_delay: 最大延迟时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"执行 {func.__name__} 失败 (第{attempt + 1}次尝试)，"
                            f"{current_delay}秒后重试: {str(e)}"
                        )
                        
                        import time
                        time.sleep(current_delay)
                        current_delay = min(current_delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"执行 {func.__name__} 失败，已重试{max_attempts}次: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator