"""
API专用并发执行器
专门针对API测试优化的并发执行器
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from pathlib import Path

from utils.logging.logger import logger
from utils.config.parser import config
from .test_executor import TestCase, TestResult, TestType


class APIConcurrentExecutor:
    """API专用并发执行器"""
    
    def __init__(self, max_workers: int = None, timeout: int = None):
        """
        初始化API并发执行器
        
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
        
        logger.info(f"API并发执行器初始化: {self.max_workers} 个工作线程, 超时 {self.timeout} 秒")
    
    def _load_config(self):
        """加载API并发配置"""
        try:
            concurrent_config = config.get('concurrent', {})
            api_config = concurrent_config.get('api', {})
            
            self.config_enabled = api_config.get('enabled', True)
            self.config_max_workers = api_config.get('max_workers', 3)
            self.config_timeout = api_config.get('timeout', 120)
            
            if not self.config_enabled:
                logger.warning("API并发执行已在配置中禁用")
                
        except Exception as e:
            logger.warning(f"加载API并发配置失败，使用默认值: {e}")
            self.config_enabled = True
            self.config_max_workers = 3
            self.config_timeout = 120
    
    def load_api_cases(self, test_files: List[str]) -> List[TestCase]:
        """
        加载API测试用例
        
        Args:
            test_files: 测试文件路径列表
            
        Returns:
            API测试用例列表
        """
        import yaml
        
        test_cases = []
        
        for file_path in test_files:
            try:
                file_path = Path(file_path)
                if not file_path.exists():
                    logger.warning(f"测试文件不存在: {file_path}")
                    continue
                
                # 只处理API相关文件
                if "api" not in str(file_path).lower():
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if 'test_cases' in data:
                    for i, case_data in enumerate(data['test_cases']):
                        test_case = TestCase(
                            id=f"{file_path.stem}_{i}",
                            name=case_data.get('case_name', f'API_Case_{i}'),
                            type=TestType.API,
                            data=case_data,
                            file_path=str(file_path),
                            priority=case_data.get('priority', 1)
                        )
                        test_cases.append(test_case)
                        
            except Exception as e:
                logger.error(f"加载API测试文件失败 {file_path}: {e}")
        
        logger.info(f"成功加载 {len(test_cases)} 个API测试用例")
        return test_cases
    
    def execute_api_case(self, test_case: TestCase) -> TestResult:
        """
        执行单个API测试用例
        
        Args:
            test_case: API测试用例
            
        Returns:
            测试结果
        """
        thread_id = threading.get_ident()
        start_time = time.time()
        
        logger.info(f"[API线程{thread_id}] 开始执行: {test_case.name}")
        
        try:
            from utils.core.api.client import APIClient
            from utils.core.api.assertions import APIAssertions
            
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
            
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = TestResult(
                test_case=test_case,
                success=all_passed,
                duration=duration,
                response_data={
                    'response': {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'body': response.text[:500] if response.text else None  # 限制响应体长度
                    },
                    'assertions': assertion_results
                },
                thread_id=thread_id,
                start_time=start_time,
                end_time=end_time
            )
            
            status = "✅ 成功" if test_result.success else "❌ 失败"
            logger.info(f"[API线程{thread_id}] {status}: {test_case.name} ({duration:.2f}s)")
            
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
            
            logger.error(f"[API线程{thread_id}] ❌ 异常: {test_case.name} - {e}")
            return test_result
    
    def run_concurrent(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        并发执行API测试用例
        
        Args:
            test_cases: API测试用例列表
            
        Returns:
            测试结果列表
        """
        if not test_cases:
            logger.warning("没有API测试用例需要执行")
            return []
        
        if not self.config_enabled:
            logger.warning("API并发执行已禁用，将顺序执行")
            return self._run_sequential(test_cases)
        
        self.start_time = time.time()
        logger.info(f"开始并发执行 {len(test_cases)} 个API测试用例，使用 {self.max_workers} 个线程")
        
        # 按优先级排序
        test_cases.sort(key=lambda x: x.priority, reverse=True)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_case = {
                executor.submit(self.execute_api_case, case): case 
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
        """顺序执行API测试用例"""
        results = []
        for case in test_cases:
            result = self.execute_api_case(case)
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
        logger.info("📊 API并发执行统计报告")
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
