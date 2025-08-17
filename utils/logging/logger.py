import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    level: str = "INFO",
    file_level: str = "DEBUG", 
    console_level: str = "INFO",
    log_format: Optional[str] = None,
    rotation: str = "100 MB",
    retention: str = "30 days",
    compression: str = "zip"
) -> None:
    """
    设置日志配置
    
    Args:
        level: 默认日志级别
        file_level: 文件日志级别
        console_level: 控制台日志级别
        log_format: 日志格式
        rotation: 日志轮转大小
        retention: 日志保留时间
        compression: 日志压缩格式
    """
    # 移除默认handler
    logger.remove()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 默认日志格式
    if log_format is None:
        log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    
    # 控制台日志
    logger.add(
        sys.stdout,
        level=console_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 文件日志 - 所有级别
    logger.add(
        logs_dir / "app.log",
        level=file_level,
        format=log_format,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # 错误日志单独文件
    logger.add(
        logs_dir / "error.log",
        level="ERROR",
        format=log_format,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # 测试执行日志
    logger.add(
        logs_dir / "test_execution.log",
        level="INFO",
        format=log_format,
        rotation=rotation,
        retention=retention,
        compression=compression,
        encoding="utf-8",
        filter=lambda record: "test" in record["name"].lower() or "case" in record["name"].lower()
    )


def get_logger(name: str = None):
    """
    获取logger实例
    
    Args:
        name: logger名称
        
    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self.is_initialized = False
    
    def init_from_config(self, config: dict):
        """从配置初始化logger"""
        if self.is_initialized:
            return
            
        logging_config = config.get("logging", {})
        
        setup_logger(
            level=logging_config.get("level", "INFO"),
            file_level=logging_config.get("file_level", "DEBUG"),
            console_level=logging_config.get("console_level", "INFO"),
            log_format=logging_config.get("format"),
            rotation=logging_config.get("rotation", "100 MB"),
            retention=logging_config.get("retention", "30 days"),
            compression=logging_config.get("compression", "zip")
        )
        
        self.is_initialized = True
        logger.info("日志系统初始化完成")
    
    def log_test_start(self, test_name: str, test_type: str = ""):
        """记录测试开始"""
        logger.info(f"{'='*50}")
        logger.info(f"开始执行测试: {test_name} {test_type}")
        logger.info(f"{'='*50}")
    
    def log_test_end(self, test_name: str, result: str = ""):
        """记录测试结束"""
        logger.info(f"{'='*50}")
        logger.info(f"测试执行完成: {test_name} {result}")
        logger.info(f"{'='*50}")
    
    def log_case_start(self, case_name: str):
        """记录用例开始"""
        logger.info(f">> 开始执行用例: {case_name}")
    
    def log_case_end(self, case_name: str, result: str, duration: float = 0):
        """记录用例结束"""
        logger.info(f"<< 用例执行完成: {case_name} | 结果: {result} | 耗时: {duration:.2f}s")
    
    def log_step(self, step_name: str, details: str = ""):
        """记录测试步骤"""
        logger.info(f"   步骤: {step_name} {details}")
    
    def log_assertion(self, assertion_type: str, expected: str, actual: str, result: bool):
        """记录断言结果"""
        status = "✓" if result else "✗"
        logger.info(f"   断言 [{assertion_type}] {status} 期望: {expected} | 实际: {actual}")
    
    def log_api_request(self, method: str, url: str, headers: dict = None, data: str = ""):
        """记录API请求"""
        logger.debug(f"API请求: {method} {url}")
        if headers:
            logger.debug(f"请求头: {headers}")
        if data:
            logger.debug(f"请求数据: {data}")
    
    def log_api_response(self, status_code: int, response_text: str, duration: float = 0):
        """记录API响应"""
        logger.debug(f"API响应: {status_code} | 耗时: {duration:.2f}s")
        logger.debug(f"响应内容: {response_text[:200]}..." if len(response_text) > 200 else response_text)
    
    def start_session(self):
        """开始测试会话"""
        logger.info("测试会话开始")
    
    def end_session(self):
        """结束测试会话"""
        logger.info("测试会话结束")
    
    def start_test(self, test_name: str):
        """开始测试"""
        logger.info(f"开始执行测试: {test_name}")
    
    def end_test(self):
        """结束测试"""
        logger.info("测试执行完成")
    
    def log_web_action(self, action: str, locator: str = "", value: str = ""):
        """记录Web操作"""
        logger.debug(f"Web操作: {action} | 定位器: {locator} | 值: {value}")
    
    def log_screenshot(self, screenshot_path: str):
        """记录截图，并尝试附加到Allure报告"""
        logger.info(f"截图已保存: {screenshot_path}")
        try:
            import allure  # type: ignore
            from pathlib import Path
            p = Path(screenshot_path)
            if p.exists():
                with open(p, 'rb') as f:
                    allure.attach(f.read(), name=p.name, attachment_type=allure.attachment_type.PNG)
        except Exception:
            # 不影响主流程
            pass

    def log_error(self, error_msg: str, exception: Exception = None):
        """记录错误"""
        logger.error(error_msg)
        if exception:
            logger.exception(f"异常详情: {exception}")


# 全局logger管理器实例
logger_manager = LoggerManager()

# 初始化基础logger配置
setup_logger()

# 导出logger实例供其他模块使用
__all__ = ['logger', 'logger_manager', 'get_logger', 'setup_logger']