from abc import ABC, abstractmethod
from typing import Any, Dict, List
from utils.logging.logger import logger


class KeywordsBase(ABC):
    """关键字基类 - 定义关键字的基本接口"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        logger.debug(f"初始化关键字类: {self.name}")
    
    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any] = None) -> Any:
        """
        执行关键字操作
        
        Args:
            action: 操作名称
            params: 操作参数
            
        Returns:
            操作结果
        """
        pass
    
    def validate_params(self, params: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        验证参数
        
        Args:
            params: 参数字典
            required_keys: 必需的参数键
            
        Returns:
            验证结果
        """
        if params is None:
            params = {}
        
        missing_keys = [key for key in required_keys if key not in params]
        
        if missing_keys:
            error_msg = f"缺少必需的参数: {missing_keys}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return True
    
    def log_action(self, action: str, details: str = ""):
        """记录操作"""
        logger.info(f"[{self.name}] 执行操作: {action} {details}")
    
    def log_result(self, result: Any):
        """记录结果"""
        logger.debug(f"[{self.name}] 操作结果: {result}")


class TestCaseBase:
    """测试用例基类"""
    
    def __init__(self):
        self.case_name = ""
        self.case_description = ""
        self.case_tags = []
        self.setup_actions = []
        self.teardown_actions = []
        self.variables = {}
    
    def setup(self):
        """用例前置操作"""
        logger.info(f"执行用例前置操作: {self.case_name}")
        for action in self.setup_actions:
            self._execute_action(action)
    
    def teardown(self):
        """用例后置操作"""
        logger.info(f"执行用例后置操作: {self.case_name}")
        for action in self.teardown_actions:
            self._execute_action(action)
    
    def _execute_action(self, action: Dict[str, Any]):
        """执行操作"""
        action_type = action.get("type")
        params = action.get("params", {})
        
        # 这里可以根据action_type调用不同的关键字
        logger.debug(f"执行操作: {action_type}, 参数: {params}")


class TestResult:
    """测试结果类"""
    
    def __init__(self):
        self.case_name = ""
        self.status = "PENDING"  # PENDING, RUNNING, PASSED, FAILED, SKIPPED
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.error_message = ""
        self.steps = []
        self.assertions = []
        self.screenshots = []
        self.extracted_data = {}
    
    def set_passed(self):
        """设置为通过"""
        self.status = "PASSED"
    
    def set_failed(self, error_message: str = ""):
        """设置为失败"""
        self.status = "FAILED"
        self.error_message = error_message
    
    def set_skipped(self, reason: str = ""):
        """设置为跳过"""
        self.status = "SKIPPED"
        self.error_message = reason
    
    def add_step(self, step_name: str, result: str = "PASSED", details: str = ""):
        """添加测试步骤"""
        step = {
            "name": step_name,
            "result": result,
            "details": details,
            "timestamp": logger.opt(record=True).info("")._record.time
        }
        self.steps.append(step)
    
    def add_assertion(self, assertion_type: str, expected: Any, actual: Any, result: bool):
        """添加断言结果"""
        assertion = {
            "type": assertion_type,
            "expected": expected,
            "actual": actual,
            "result": "PASSED" if result else "FAILED"
        }
        self.assertions.append(assertion)
    
    def add_screenshot(self, screenshot_path: str):
        """添加截图"""
        self.screenshots.append(screenshot_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "case_name": self.case_name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "error_message": self.error_message,
            "steps": self.steps,
            "assertions": self.assertions,
            "screenshots": self.screenshots,
            "extracted_data": self.extracted_data
        }