"""
标准测试用例数据类定义
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class TestCaseType(Enum):
    """测试用例类型"""
    API = "api"
    WEB = "web"
    WORKFLOW = "workflow"


class TestCaseSource(Enum):
    """测试用例来源"""
    YAML = "yaml"
    EXCEL = "excel"
    TEMPLATE = "template"
    INLINE = "inline"


@dataclass
class TestAssertion:
    """测试断言"""
    type: str
    expected: Any = None
    operator: str = "=="
    path: Optional[str] = None
    message: Optional[str] = None
    condition: Optional[str] = None
    max_time: Optional[int] = None
    attribute: Optional[str] = None
    locator: Optional[str] = None


@dataclass
class TestExtraction:
    """数据提取"""
    name: str
    type: str
    path: Optional[str] = None
    locator: Optional[str] = None
    condition: Optional[str] = None
    source: Optional[str] = None


@dataclass
class TestRequest:
    """API请求信息"""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    data: Optional[Union[Dict, str]] = None
    params: Optional[Dict[str, str]] = None
    files: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None


@dataclass
class TestStep:
    """Web测试步骤"""
    action: str
    params: Dict[str, Any]
    condition: Optional[str] = None


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_name: str
    step_template: str
    step_data: Dict[str, Any]
    depends_on: Optional[str] = None
    condition: Optional[str] = None
    extract_to_global: Optional[List[TestExtraction]] = None
    on_failure: str = "continue"


@dataclass
class TestCase:
    """标准测试用例"""
    case_name: str
    description: str = ""
    case_type: TestCaseType = TestCaseType.API
    source: TestCaseSource = TestCaseSource.YAML
    module: str = ""
    tags: List[str] = field(default_factory=list)
    severity: str = "normal"
    enabled: bool = True
    
    # API测试相关
    request: Optional[TestRequest] = None
    
    # Web测试相关
    steps: Optional[List[TestStep]] = None
    
    # 工作流测试相关
    workflow_steps: Optional[List[WorkflowStep]] = None
    workflow_assertions: Optional[List[TestAssertion]] = None
    
    # 通用字段
    assertions: List[TestAssertion] = field(default_factory=list)
    extract: List[TestExtraction] = field(default_factory=list)
    
    # 元数据
    template_path: Optional[str] = None
    dataset_path: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    override_config: Optional[Dict[str, Any]] = None
    
    # 执行相关
    setup: Optional[Dict[str, Any]] = None
    teardown: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    timeout: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "case_name": self.case_name,
            "description": self.description,
            "case_type": self.case_type.value,
            "source": self.source.value,
            "module": self.module,
            "tags": self.tags,
            "severity": self.severity,
            "enabled": self.enabled
        }
        
        # 添加请求信息
        if self.request:
            result["request"] = {
                "method": self.request.method,
                "url": self.request.url,
                "headers": self.request.headers,
                "data": self.request.data,
                "params": self.request.params,
                "files": self.request.files,
                "timeout": self.request.timeout
            }
        
        # 添加Web步骤
        if self.steps:
            result["steps"] = [
                {
                    "action": step.action,
                    "params": step.params,
                    "condition": step.condition
                }
                for step in self.steps
            ]
        
        # 添加工作流步骤
        if self.workflow_steps:
            result["workflow_steps"] = [
                {
                    "step_name": step.step_name,
                    "step_template": step.step_template,
                    "step_data": step.step_data,
                    "depends_on": step.depends_on,
                    "condition": step.condition,
                    "extract_to_global": [
                        {
                            "name": ext.name,
                            "type": ext.type,
                            "path": ext.path,
                            "condition": ext.condition
                        }
                        for ext in step.extract_to_global
                    ] if step.extract_to_global else None,
                    "on_failure": step.on_failure
                }
                for step in self.workflow_steps
            ]
        
        # 添加断言
        if self.assertions:
            result["assertions"] = [
                {
                    "type": assertion.type,
                    "expected": assertion.expected,
                    "operator": assertion.operator,
                    "path": assertion.path,
                    "message": assertion.message,
                    "condition": assertion.condition,
                    "max_time": assertion.max_time,
                    "attribute": assertion.attribute,
                    "locator": assertion.locator
                }
                for assertion in self.assertions
            ]
        
        # 添加提取
        if self.extract:
            result["extract"] = [
                {
                    "name": ext.name,
                    "type": ext.type,
                    "path": ext.path,
                    "locator": ext.locator,
                    "condition": ext.condition
                }
                for ext in self.extract
            ]
        
        # 添加其他字段
        if self.template_path:
            result["template_path"] = self.template_path
        if self.dataset_path:
            result["dataset_path"] = self.dataset_path
        if self.test_data:
            result["test_data"] = self.test_data
        if self.override_config:
            result["override_config"] = self.override_config
        if self.setup:
            result["setup"] = self.setup
        if self.teardown:
            result["teardown"] = self.teardown
        if self.retry_count > 0:
            result["retry_count"] = self.retry_count
        if self.timeout:
            result["timeout"] = self.timeout
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """从字典创建测试用例"""
        # 基本信息
        case = cls(
            case_name=data.get("case_name", ""),
            description=data.get("description", ""),
            case_type=TestCaseType(data.get("case_type", "api")),
            source=TestCaseSource(data.get("source", "yaml")),
            module=data.get("module", ""),
            tags=data.get("tags", []),
            severity=data.get("severity", "normal"),
            enabled=data.get("enabled", True)
        )
        
        # 请求信息
        if "request" in data:
            req_data = data["request"]
            case.request = TestRequest(
                method=req_data.get("method", "GET"),
                url=req_data.get("url", ""),
                headers=req_data.get("headers"),
                data=req_data.get("data"),
                params=req_data.get("params"),
                files=req_data.get("files"),
                timeout=req_data.get("timeout")
            )
        
        # Web步骤
        if "steps" in data:
            case.steps = [
                TestStep(
                    action=step.get("action", ""),
                    params=step.get("params", {}),
                    condition=step.get("condition")
                )
                for step in data["steps"]
            ]
        
        # 断言
        if "assertions" in data:
            case.assertions = [
                TestAssertion(
                    type=assertion.get("type", ""),
                    expected=assertion.get("expected"),
                    operator=assertion.get("operator", "=="),
                    path=assertion.get("path"),
                    message=assertion.get("message"),
                    condition=assertion.get("condition"),
                    max_time=assertion.get("max_time"),
                    attribute=assertion.get("attribute"),
                    locator=assertion.get("locator")
                )
                for assertion in data["assertions"]
            ]
        
        # 提取
        if "extract" in data:
            case.extract = [
                TestExtraction(
                    name=ext.get("name", ""),
                    type=ext.get("type", ""),
                    path=ext.get("path"),
                    locator=ext.get("locator"),
                    condition=ext.get("condition")
                )
                for ext in data["extract"]
            ]
        
        # 其他字段
        case.template_path = data.get("template_path")
        case.dataset_path = data.get("dataset_path")
        case.test_data = data.get("test_data")
        case.override_config = data.get("override_config")
        case.setup = data.get("setup")
        case.teardown = data.get("teardown")
        case.retry_count = data.get("retry_count", 0)
        case.timeout = data.get("timeout")
        
        return case


@dataclass
class TestSuite:
    """测试套件"""
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    module: str = ""
    version: str = "1.0"
    author: str = ""
    test_cases: List[TestCase] = field(default_factory=list)
    
    def add_test_case(self, test_case: TestCase):
        """添加测试用例"""
        self.test_cases.append(test_case)
    
    def filter_by_tags(self, tags: List[str]) -> 'TestSuite':
        """按标签过滤"""
        filtered_cases = []
        for case in self.test_cases:
            if any(tag in case.tags for tag in tags):
                filtered_cases.append(case)
        
        filtered_suite = TestSuite(
            title=f"{self.title} (过滤: {', '.join(tags)})",
            description=self.description,
            tags=self.tags,
            module=self.module,
            version=self.version,
            author=self.author,
            test_cases=filtered_cases
        )
        
        return filtered_suite
    
    def filter_by_severity(self, severity: str) -> 'TestSuite':
        """按严重级别过滤"""
        filtered_cases = [case for case in self.test_cases if case.severity == severity]
        
        filtered_suite = TestSuite(
            title=f"{self.title} (严重级别: {severity})",
            description=self.description,
            tags=self.tags,
            module=self.module,
            version=self.version,
            author=self.author,
            test_cases=filtered_cases
        )
        
        return filtered_suite
