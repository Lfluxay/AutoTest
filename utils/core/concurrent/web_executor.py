"""
Web专用并发执行器
专门针对Web测试优化的并发执行器
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from pathlib import Path

from utils.logging.logger import logger
from utils.config.parser import config
from .test_executor import TestCase, TestResult, TestType


class WebConcurrentExecutor:
    """Web专用并发执行器"""
    
    def __init__(self, max_workers: int = None, timeout: int = None):
        """
        初始化Web并发执行器
        
        Args:
            max_workers: 最大工作线程数
            timeout: 超时时间
        """
        self._load_config()
        
        self.max_workers = max_workers or self.config_max_workers
        self.timeout = timeout or self.config_timeout
        
        self.results = []
        self.failed_cases = []
        self.success_cases = []
        self.start_time = None
        self.end_time = None
        
        logger.info(f"Web并发执行器初始化: {self.max_workers} 个工作线程, 超时 {self.timeout} 秒, 无头模式: {self.config_headless}")
    
    def _load_config(self):
        """加载Web并发配置"""
        try:
            concurrent_config = config.get('concurrent', {})
            web_config = concurrent_config.get('web', {})
            
            self.config_enabled = web_config.get('enabled', True)
            self.config_max_workers = web_config.get('max_workers', 2)
            self.config_timeout = web_config.get('timeout', 300)
            self.config_headless = web_config.get('headless', True)
            
            if not self.config_enabled:
                logger.warning("Web并发执行已在配置中禁用")
                
        except Exception as e:
            logger.warning(f"加载Web并发配置失败，使用默认值: {e}")
            self.config_enabled = True
            self.config_max_workers = 2
            self.config_timeout = 300
            self.config_headless = True
    
    def load_web_cases(self, test_files: List[str]) -> List[TestCase]:
        """
        加载Web测试用例
        
        Args:
            test_files: 测试文件路径列表
            
        Returns:
            Web测试用例列表
        """
        import yaml
        
        test_cases = []
        
        for file_path in test_files:
            try:
                file_path = Path(file_path)
                if not file_path.exists():
                    logger.warning(f"测试文件不存在: {file_path}")
                    continue
                
                # 只处理Web相关文件
                if "web" not in str(file_path).lower():
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if 'test_cases' in data:
                    for i, case_data in enumerate(data['test_cases']):
                        test_case = TestCase(
                            id=f"{file_path.stem}_{i}",
                            name=case_data.get('case_name', f'Web_Case_{i}'),
                            type=TestType.WEB,
                            data=case_data,
                            file_path=str(file_path),
                            priority=case_data.get('priority', 1)
                        )
                        test_cases.append(test_case)
                        
            except Exception as e:
                logger.error(f"加载Web测试文件失败 {file_path}: {e}")
        
        logger.info(f"成功加载 {len(test_cases)} 个Web测试用例")
        return test_cases
    
    def execute_web_case(self, test_case: TestCase) -> TestResult:
        """
        执行单个Web测试用例
        
        Args:
            test_case: Web测试用例
            
        Returns:
            测试结果
        """
        thread_id = threading.get_ident()
        start_time = time.time()
        
        logger.info(f"[Web线程{thread_id}] 开始执行: {test_case.name}")
        
        try:
            from utils.core.web.browser import BrowserManager
            from utils.core.web.web_actions import WebActions
            
            # 创建线程独立的浏览器管理器
            browser_manager = BrowserManager()
            browser_manager.start_browser(headless=self.config_headless)
            
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
                elif action == 'wait_for_element':
                    web_actions.wait_for_element(step.get('selector'))
                elif action == 'select_option':
                    web_actions.select_option(step.get('selector'), step.get('value'))
                elif action == 'check':
                    web_actions.check(step.get('selector'))
                elif action == 'uncheck':
                    web_actions.uncheck(step.get('selector'))
                elif action == 'hover':
                    web_actions.hover(step.get('selector'))
                elif action == 'double_click':
                    web_actions.double_click(step.get('selector'))
                elif action == 'scroll_to':
                    web_actions.scroll_to(step.get('selector'))
                # 可以添加更多操作类型
            
            # 执行断言
            assertions = case_data.get('assertions', [])
            assertion_results = []
            
            for assertion in assertions:
                assertion_type = assertion.get('type')
                try:
                    if assertion_type == 'element_visible':
                        selector = assertion.get('selector')
                        result = web_actions.is_element_visible(selector)
                        assertion_results.append({'passed': result, 'type': assertion_type})
                    elif assertion_type == 'page_title':
                        expected = assertion.get('expected')
                        title = browser_manager.page.title()
                        result = expected in title if expected else True
                        assertion_results.append({'passed': result, 'type': assertion_type})
                    elif assertion_type == 'element_text':
                        selector = assertion.get('selector')
                        expected = assertion.get('expected')
                        actual_text = web_actions.get_text(selector)
                        result = expected in actual_text if expected and actual_text else False
                        assertion_results.append({'passed': result, 'type': assertion_type})
                    elif assertion_type == 'element_enabled':
                        selector = assertion.get('selector')
                        result = web_actions.is_element_enabled(selector)
                        assertion_results.append({'passed': result, 'type': assertion_type})
                    else:
                        assertion_results.append({'passed': False, 'type': assertion_type, 'error': f'不支持的断言类型: {assertion_type}'})
                except Exception as e:
                    assertion_results.append({'passed': False, 'type': assertion_type, 'error': str(e)})
            
            # 清理浏览器
            browser_manager.stop_browser()
            
            # 判断是否所有断言都通过
            all_passed = all(result.get('passed', False) for result in assertion_results)
            
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = TestResult(
                test_case=test_case,
                success=all_passed,
                duration=duration,
                response_data={
                    'assertions': assertion_results,
                    'browser_info': {
                        'headless': self.config_headless,
                        'thread_id': thread_id
                    }
                },
                thread_id=thread_id,
                start_time=start_time,
                end_time=end_time
            )
            
            status = "✅ 成功" if test_result.success else "❌ 失败"
            logger.info(f"[Web线程{thread_id}] {status}: {test_case.name} ({duration:.2f}s)")
            
            return test_result
            
        except Exception as e:
            # 确保浏览器被清理
            try:
                if 'browser_manager' in locals():
                    browser_manager.stop_browser()
            except:
                pass
            
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
            
            logger.error(f"[Web线程{thread_id}] ❌ 异常: {test_case.name} - {e}")
            return test_result
    
    def run_concurrent(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        并发执行Web测试用例
        
        Args:
            test_cases: Web测试用例列表
            
        Returns:
            测试结果列表
        """
        if not test_cases:
            logger.warning("没有Web测试用例需要执行")
            return []
        
        if not self.config_enabled:
            logger.warning("Web并发执行已禁用，将顺序执行")
            return self._run_sequential(test_cases)
        
        self.start_time = time.time()
        logger.info(f"开始并发执行 {len(test_cases)} 个Web测试用例，使用 {self.max_workers} 个线程")
        
        # 按优先级排序
        test_cases.sort(key=lambda x: x.priority, reverse=True)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_case = {
                executor.submit(self.execute_web_case, case): case 
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
    
    def _run_sequential(self, test_cases: List[TestCase]) -> List[TestResult]:
        """顺序执行Web测试用例"""
        results = []
        for case in test_cases:
            result = self.execute_web_case(case)
            results.append(result)
            if result.success:
                self.success_cases.append(result)
            else:
                self.failed_cases.append(result)
        return results
    
    def _print_execution_summary(self):
        """打印执行统计信息"""
        total_duration = self.end_time - self.start_time
        total_cases = len(self.results)
        success_count = len(self.success_cases)
        failed_count = len(self.failed_cases)
        success_rate = (success_count / total_cases * 100) if total_cases > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 Web并发执行统计报告")
        logger.info("=" * 60)
        logger.info(f"总执行时间: {total_duration:.2f} 秒")
        logger.info(f"总用例数: {total_cases}")
        logger.info(f"成功数: {success_count}")
        logger.info(f"失败数: {failed_count}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"平均执行时间: {total_duration/total_cases:.2f} 秒/用例")
        logger.info(f"并发线程数: {self.max_workers}")
        logger.info(f"无头模式: {self.config_headless}")
        
        if self.failed_cases:
            logger.info("\n❌ 失败用例:")
            for result in self.failed_cases:
                logger.info(f"  - {result.test_case.name}: {result.error_message}")
        
        logger.info("=" * 60)
