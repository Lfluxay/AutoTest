"""
自定义并发测试执行器
支持Web和API用例的并发执行
"""

import asyncio
import threading
import time
import queue
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from utils.logging.logger import logger
from utils.config.parser import config


class TestType(Enum):
    """测试类型枚举"""
    API = "api"
    WEB = "web"


@dataclass
class TestCase:
    """测试用例数据类"""
    id: str
    name: str
    type: TestType
    data: Dict[str, Any]
    file_path: str
    priority: int = 1


@dataclass
class TestResult:
    """测试结果数据类"""
    test_case: TestCase
    success: bool
    duration: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    thread_id: int = None
    start_time: float = None
    end_time: float = None


class ConcurrentTestExecutor:
    """并发测试执行器"""

    def __init__(self, max_workers: int = None, timeout: int = None, test_type: str = "mixed"):
        """
        初始化并发执行器

        Args:
            max_workers: 最大工作线程数（None时从配置读取）
            timeout: 单个测试用例超时时间（None时从配置读取）
            test_type: 测试类型 ("api", "web", "mixed")
        """
        # 加载配置
        self.test_type = test_type
        self._load_config()

        # 设置参数（优先使用传入参数，否则使用配置）
        self.max_workers = max_workers or self.config_max_workers
        self.timeout = timeout or self.config_timeout

        self.results = []
        self.failed_cases = []
        self.success_cases = []
        self.start_time = None
        self.end_time = None

        # 线程安全的队列和锁
        self.result_queue = queue.Queue()
        self.lock = threading.Lock()

        logger.info(f"并发测试执行器初始化: {self.max_workers} 个工作线程, 超时 {self.timeout} 秒, 类型: {test_type}")

    def _load_config(self):
        """加载并发配置"""
        try:
            from utils.config.parser import ConfigParser

            config_parser = ConfigParser()
            config_data = config_parser.load_config()
            concurrent_config = config_data.get('concurrent', {})

            # 检查并发是否启用
            if not concurrent_config.get('enabled', True):
                logger.warning("并发执行已在配置中禁用")

            # 根据测试类型获取配置
            if self.test_type == "api":
                type_config = concurrent_config.get('api', {})
                self.config_enabled = type_config.get('enabled', True)
                self.config_max_workers = type_config.get('max_workers', 3)
                self.config_timeout = type_config.get('timeout', 120)
            elif self.test_type == "web":
                type_config = concurrent_config.get('web', {})
                self.config_enabled = type_config.get('enabled', True)
                self.config_max_workers = type_config.get('max_workers', 2)
                self.config_timeout = type_config.get('timeout', 300)
                self.config_headless = type_config.get('headless', True)
            else:  # mixed
                type_config = concurrent_config.get('mixed', {})
                self.config_enabled = type_config.get('enabled', True)
                self.config_max_workers = type_config.get('max_workers', 4)
                self.config_timeout = type_config.get('timeout', 300)

            # 全局配置作为后备
            if not hasattr(self, 'config_max_workers'):
                self.config_max_workers = concurrent_config.get('max_workers', 2)
            if not hasattr(self, 'config_timeout'):
                self.config_timeout = concurrent_config.get('timeout', 300)

        except Exception as e:
            logger.warning(f"加载并发配置失败，使用默认值: {e}")
            self.config_enabled = True
            self.config_max_workers = 2
            self.config_timeout = 300
    
    def load_test_cases(self, test_files: List[str]) -> List[TestCase]:
        """
        加载测试用例
        
        Args:
            test_files: 测试文件路径列表
            
        Returns:
            测试用例列表
        """
        test_cases = []
        
        for file_path in test_files:
            try:
                file_path = Path(file_path)
                if not file_path.exists():
                    logger.warning(f"测试文件不存在: {file_path}")
                    continue
                
                # 根据文件路径判断测试类型
                if "api" in str(file_path).lower():
                    test_type = TestType.API
                elif "web" in str(file_path).lower():
                    test_type = TestType.WEB
                else:
                    logger.warning(f"无法识别测试类型: {file_path}")
                    continue
                
                # 加载YAML测试用例
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    cases = self._load_yaml_cases(file_path, test_type)
                    test_cases.extend(cases)
                else:
                    logger.warning(f"不支持的文件格式: {file_path}")
                    
            except Exception as e:
                logger.error(f"加载测试文件失败 {file_path}: {e}")
        
        logger.info(f"成功加载 {len(test_cases)} 个测试用例")
        return test_cases
    
    def _load_yaml_cases(self, file_path: Path, test_type: TestType) -> List[TestCase]:
        """加载YAML格式的测试用例"""
        import yaml
        
        test_cases = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'test_cases' in data:
                for i, case_data in enumerate(data['test_cases']):
                    test_case = TestCase(
                        id=f"{file_path.stem}_{i}",
                        name=case_data.get('case_name', f'Case_{i}'),
                        type=test_type,
                        data=case_data,
                        file_path=str(file_path),
                        priority=case_data.get('priority', 1)
                    )
                    test_cases.append(test_case)
            
        except Exception as e:
            logger.error(f"解析YAML文件失败 {file_path}: {e}")
        
        return test_cases
    
    def execute_test_case(self, test_case: TestCase) -> TestResult:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            测试结果
        """
        thread_id = threading.get_ident()
        start_time = time.time()
        
        logger.info(f"[线程{thread_id}] 开始执行: {test_case.name}")
        
        try:
            if test_case.type == TestType.API:
                result = self._execute_api_case(test_case, thread_id)
            elif test_case.type == TestType.WEB:
                result = self._execute_web_case(test_case, thread_id)
            else:
                raise ValueError(f"不支持的测试类型: {test_case.type}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = TestResult(
                test_case=test_case,
                success=result.get('success', False),
                duration=duration,
                error_message=result.get('error'),
                response_data=result.get('data'),
                thread_id=thread_id,
                start_time=start_time,
                end_time=end_time
            )
            
            status = "✅ 成功" if test_result.success else "❌ 失败"
            logger.info(f"[线程{thread_id}] {status}: {test_case.name} ({duration:.2f}s)")
            
            return test_result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = TestResult(
                test_case=test_case,
                success=False,
                duration=duration,
                error_message=str(e),
                thread_id=thread_id,
                start_time=start_time,
                end_time=end_time
            )
            
            logger.error(f"[线程{thread_id}] ❌ 异常: {test_case.name} - {e}")
            return test_result
    
    def _execute_api_case(self, test_case: TestCase, thread_id: int) -> Dict[str, Any]:
        """执行API测试用例"""
        from utils.core.api.client import APIClient
        from utils.core.api.assertions import APIAssertions
        
        try:
            # 创建线程独立的API客户端
            api_client = APIClient()

            case_data = test_case.data
            request_data = case_data.get('request', {})

            # 发送API请求
            response = api_client.request(
                method=request_data.get('method', 'GET'),
                url=request_data.get('url'),
                headers=request_data.get('headers'),
                data=request_data.get('data'),
                params=request_data.get('params')
            )

            # 执行断言
            assertions = case_data.get('assertions', [])
            assertion_results = []

            for assertion in assertions:
                assertion_type = assertion.get('type')
                expected = assertion.get('expected')
                message = assertion.get('message', '')

                try:
                    if assertion_type == 'status_code':
                        APIAssertions.assert_status_code(response, expected, message)
                        assertion_results.append({'passed': True, 'type': assertion_type})
                    elif assertion_type == 'json_path':
                        path = assertion.get('path')
                        APIAssertions.assert_json_path(response, path, expected, message)
                        assertion_results.append({'passed': True, 'type': assertion_type})
                    elif assertion_type == 'response_time':
                        max_time = assertion.get('max_time')
                        APIAssertions.assert_response_time(response, max_time, message)
                        assertion_results.append({'passed': True, 'type': assertion_type})
                    else:
                        assertion_results.append({'passed': False, 'type': assertion_type, 'error': f'不支持的断言类型: {assertion_type}'})
                except Exception as e:
                    assertion_results.append({'passed': False, 'type': assertion_type, 'error': str(e)})
            
            # 判断是否所有断言都通过
            all_passed = all(result.get('passed', False) for result in assertion_results)
            
            return {
                'success': all_passed,
                'data': {
                    'response': {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'body': response.text[:1000] if response.text else None  # 限制响应体长度
                    },
                    'assertions': assertion_results
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_web_case(self, test_case: TestCase, thread_id: int) -> Dict[str, Any]:
        """执行Web测试用例"""
        from utils.core.web.browser import BrowserManager
        from utils.core.web.web_actions import WebActions

        try:
            # 创建线程独立的浏览器管理器
            browser_manager = BrowserManager()
            # 根据配置决定是否使用无头模式
            headless = getattr(self, 'config_headless', True)
            browser_manager.start_browser(headless=headless)
            
            web_actions = WebActions(browser_manager.page)
            case_data = test_case.data
            
            # 执行Web操作
            steps = case_data.get('steps', [])
            for step in steps:
                action = step.get('action')
                if action == 'navigate':
                    web_actions.navigate(step.get('url'))
                elif action == 'click':
                    web_actions.click(step.get('selector'))
                elif action == 'fill':
                    web_actions.fill(step.get('selector'), step.get('value'))
                elif action == 'wait':
                    web_actions.wait(step.get('timeout', 1000))
                # 可以添加更多操作类型
            
            # 执行断言
            assertions = case_data.get('assertions', [])
            assertion_results = []
            
            for assertion in assertions:
                if assertion.get('type') == 'element_visible':
                    result = web_actions.is_element_visible(assertion.get('selector'))
                    assertion_results.append({'passed': result})
                elif assertion.get('type') == 'page_title':
                    title = browser_manager.page.title()
                    expected = assertion.get('expected')
                    result = expected in title if expected else True
                    assertion_results.append({'passed': result})
                # 可以添加更多断言类型
            
            # 清理浏览器
            browser_manager.stop_browser()
            
            all_passed = all(result.get('passed', False) for result in assertion_results)
            
            return {
                'success': all_passed,
                'data': {
                    'assertions': assertion_results
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_concurrent(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        并发执行测试用例
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            测试结果列表
        """
        if not test_cases:
            logger.warning("没有测试用例需要执行")
            return []
        
        self.start_time = time.time()
        logger.info(f"开始并发执行 {len(test_cases)} 个测试用例，使用 {self.max_workers} 个线程")
        
        # 按优先级排序
        test_cases.sort(key=lambda x: x.priority, reverse=True)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_case = {
                executor.submit(self.execute_test_case, case): case 
                for case in test_cases
            }
            
            # 收集结果
            for future in as_completed(future_to_case, timeout=self.timeout * len(test_cases)):
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                    
                    if result.success:
                        self.success_cases.append(result)
                    else:
                        self.failed_cases.append(result)
                        
                except Exception as e:
                    case = future_to_case[future]
                    error_result = TestResult(
                        test_case=case,
                        success=False,
                        duration=0,
                        error_message=f"执行超时或异常: {e}",
                        thread_id=threading.get_ident()
                    )
                    results.append(error_result)
                    self.failed_cases.append(error_result)
        
        self.end_time = time.time()
        self.results = results
        
        # 输出执行统计
        self._print_execution_summary()
        
        return results
    
    def _print_execution_summary(self):
        """打印执行统计信息"""
        total_duration = self.end_time - self.start_time
        total_cases = len(self.results)
        success_count = len(self.success_cases)
        failed_count = len(self.failed_cases)
        success_rate = (success_count / total_cases * 100) if total_cases > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 并发执行统计报告")
        logger.info("=" * 60)
        logger.info(f"总执行时间: {total_duration:.2f} 秒")
        logger.info(f"总用例数: {total_cases}")
        logger.info(f"成功数: {success_count}")
        logger.info(f"失败数: {failed_count}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"平均执行时间: {total_duration/total_cases:.2f} 秒/用例")
        logger.info(f"并发线程数: {self.max_workers}")
        
        if self.failed_cases:
            logger.info("\n❌ 失败用例:")
            for result in self.failed_cases:
                logger.info(f"  - {result.test_case.name}: {result.error_message}")
        
        logger.info("=" * 60)
    
    def generate_report(self, output_path: str = "reports/concurrent_report.json"):
        """
        生成测试报告
        
        Args:
            output_path: 报告输出路径
        """
        report_data = {
            'summary': {
                'total_cases': len(self.results),
                'success_count': len(self.success_cases),
                'failed_count': len(self.failed_cases),
                'success_rate': len(self.success_cases) / len(self.results) * 100 if self.results else 0,
                'total_duration': self.end_time - self.start_time if self.end_time and self.start_time else 0,
                'max_workers': self.max_workers,
                'start_time': self.start_time,
                'end_time': self.end_time
            },
            'results': []
        }
        
        for result in self.results:
            report_data['results'].append({
                'case_id': result.test_case.id,
                'case_name': result.test_case.name,
                'test_type': result.test_case.type.value,
                'success': result.success,
                'duration': result.duration,
                'error_message': result.error_message,
                'thread_id': result.thread_id,
                'start_time': result.start_time,
                'end_time': result.end_time
            })
        
        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已生成: {output_path}")
        return output_path
