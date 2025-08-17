from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import pytest
import allure
from utils.logging.logger import logger
from utils.logging.test_step_logger import TestStepLogger
from utils.logging.logger import logger_manager
from utils.config.parser import get_merged_config
from utils.data.parser import DataParser
from utils.data.extractor import variable_manager
from utils.core.exceptions import AutoTestException


class TestBase(ABC):
    """测试基类 - 提供测试的基础功能"""
    
    def __init__(self) -> None:
        self.config: Dict[str, Any] = get_merged_config()
        self.data_parser: DataParser = DataParser()
        self.test_data: Dict[str, Any] = {}
        self.test_results: List[Dict[str, Any]] = []
        self.step_logger: TestStepLogger = TestStepLogger()
        
    def setup_method(self, method: Any) -> None:
        """测试方法前置操作"""
        logger.info(f"开始执行测试: {method.__name__}")
        self.step_logger.start_test(method.__name__)

        # 清理变量管理器
        variable_manager.clear_variables()

        # 执行子类的前置操作
        self.setup_test()

    def teardown_method(self, method: Any) -> None:
        """测试方法后置操作"""
        logger.info(f"测试执行完成: {method.__name__}")
        logger_manager.end_test()

        # 执行子类的后置操作
        self.teardown_test()
    
    @abstractmethod
    def setup_test(self) -> None:
        """子类实现的测试前置操作"""
        pass

    @abstractmethod
    def teardown_test(self) -> None:
        """子类实现的测试后置操作"""
        pass
    
    def load_test_data(self, data_file: str) -> Dict[str, Any]:
        """
        加载测试数据
        
        Args:
            data_file: 数据文件路径
            
        Returns:
            测试数据字典
        """
        try:
            test_data = self.data_parser.load_test_data(data_file)
            self.test_data.update(test_data)
            logger.info(f"测试数据加载成功: {data_file}")
            return test_data
        except Exception as e:
            logger.error(f"测试数据加载失败: {e}")
            raise
    
    def get_test_cases(self, data_file: str, case_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取测试用例
        
        Args:
            data_file: 数据文件路径
            case_filter: 用例过滤条件
            
        Returns:
            测试用例列表
        """
        try:
            test_cases = self.data_parser.get_test_cases(data_file, case_filter)
            logger.info(f"获取到 {len(test_cases)} 个测试用例")
            return test_cases
        except Exception as e:
            logger.error(f"获取测试用例失败: {e}")
            raise
    
    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例数据
            
        Returns:
            测试结果
        """
        case_name = test_case.get('case_name', 'Unknown')
        test_description = test_case.get('description', '')

        # 开始详细日志记录
        self.step_logger.start_test(case_name, test_description)

        try:
            # 记录测试用例初始化步骤
            self.step_logger.start_step("测试用例初始化", "准备测试环境和数据")
            self.step_logger.log_action("加载测试用例配置", {
                'case_name': case_name,
                'test_type': test_case.get('type', 'unknown'),
                'priority': test_case.get('priority', 'normal')
            })

            logger.info(f"执行测试用例: {case_name}")

            # 添加Allure标签
            self._add_allure_labels(test_case)
            self.step_logger.end_step("passed")

            # 执行具体的测试逻辑
            self.step_logger.start_step("执行测试逻辑", "执行主要测试步骤")
            result = self._execute_case_logic(test_case)
            self.step_logger.end_step("passed")
            
            # 记录测试结果
            test_result = {
                'case_name': case_name,
                'status': 'PASS' if result.get('success', False) else 'FAIL',
                'result': result,
                'error': result.get('error')
            }
            
            self.test_results.append(test_result)

            # 记录测试结果步骤
            self.step_logger.start_step("测试结果验证", "验证测试执行结果")
            self.step_logger.log_assertion(
                "测试状态检查",
                "PASS",
                test_result['status'],
                test_result['status'] == 'PASS',
                f"测试用例 {case_name} 执行结果"
            )
            self.step_logger.end_step("passed")

            if test_result['status'] == 'PASS':
                logger.info(f"测试用例执行成功: {case_name}")
            else:
                logger.error(f"测试用例执行失败: {case_name}, 错误: {test_result['error']}")

            # 结束详细日志记录
            test_summary = {
                '测试结果': test_result['status'],
                '错误信息': test_result.get('error', '无')
            }

            self.step_logger.end_test(
                status="passed" if test_result['status'] == 'PASS' else "failed",
                summary=test_summary
            )

            return test_result
            
        except Exception as e:
            error_msg = f"测试用例执行异常: {case_name}, 错误: {str(e)}"
            logger.error(error_msg)

            # 记录错误信息
            if self.step_logger.current_step:
                self.step_logger.end_step("failed", str(e))

            test_result = {
                'case_name': case_name,
                'status': 'ERROR',
                'result': None,
                'error': str(e)
            }

            self.test_results.append(test_result)

            # 结束详细日志记录（错误情况）
            error_summary = {
                '测试结果': 'ERROR',
                '错误信息': str(e)
            }

            self.step_logger.end_test(status="failed", summary=error_summary)
            raise
    
    @abstractmethod
    def _execute_case_logic(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行具体的测试用例逻辑 - 由子类实现
        
        Args:
            test_case: 测试用例数据
            
        Returns:
            执行结果
        """
        pass
    
    def _add_allure_labels(self, test_case: Dict[str, Any]):
        """添加Allure标签"""
        case_name = test_case.get('case_name', 'Unknown')
        description = test_case.get('description', '')
        tags = test_case.get('tags', [])
        
        # 设置用例标题和描述
        allure.dynamic.title(case_name)
        if description:
            allure.dynamic.description(description)
        
        # 设置标签
        for tag in tags:
            allure.dynamic.tag(tag)
        
        # 设置严重程度
        severity = test_case.get('severity', 'normal')
        if severity == 'blocker':
            allure.dynamic.severity(allure.severity_level.BLOCKER)
        elif severity == 'critical':
            allure.dynamic.severity(allure.severity_level.CRITICAL)
        elif severity == 'normal':
            allure.dynamic.severity(allure.severity_level.NORMAL)
        elif severity == 'minor':
            allure.dynamic.severity(allure.severity_level.MINOR)
        elif severity == 'trivial':
            allure.dynamic.severity(allure.severity_level.TRIVIAL)
    
    def get_test_summary(self) -> Dict[str, Any]:
        """
        获取测试总结
        
        Returns:
            测试总结信息
        """
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        summary = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'error': error,
            'pass_rate': round(passed / total * 100, 2) if total > 0 else 0,
            'results': self.test_results
        }
        
        logger.info(f"测试总结: 总计{total}, 通过{passed}, 失败{failed}, 错误{error}, 通过率{summary['pass_rate']}%")
        
        return summary
    
    def assert_test_result(self, condition: bool, message: str = ""):
        """
        断言测试结果
        
        Args:
            condition: 断言条件
            message: 错误消息
        """
        if not condition:
            error_msg = message or "测试断言失败"
            logger.error(error_msg)
            pytest.fail(error_msg)
    
    def skip_test(self, reason: str = ""):
        """
        跳过测试
        
        Args:
            reason: 跳过原因
        """
        skip_msg = reason or "测试被跳过"
        logger.warning(skip_msg)
        pytest.skip(skip_msg)
    
    def mark_test_as_expected_failure(self, reason: str = ""):
        """
        标记测试为预期失败
        
        Args:
            reason: 失败原因
        """
        fail_msg = reason or "预期失败的测试"
        logger.warning(fail_msg)
        pytest.xfail(fail_msg)


class DataDrivenTestBase(TestBase):
    """数据驱动测试基类"""
    
    def __init__(self):
        super().__init__()
        self.current_case_data = None
    
    def setup_test(self):
        """数据驱动测试前置操作 - 默认实现"""
        logger.debug("数据驱动测试前置操作")
    
    def teardown_test(self):
        """数据驱动测试后置操作 - 默认实现"""
        logger.debug("数据驱动测试后置操作")
    
    def _execute_case_logic(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据驱动测试用例逻辑 - 默认实现

        Args:
            test_case: 测试用例数据

        Returns:
            执行结果
        """
        case_name = test_case.get('case_name', 'Unknown')

        # 记录测试数据准备步骤
        self.step_logger.start_step("测试数据准备", "准备测试所需的数据")
        self.step_logger.log_action("设置当前测试用例数据", case_name)
        self.current_case_data = test_case
        self.step_logger.end_step("passed")

        # 记录前置操作步骤
        self.step_logger.start_step("前置操作", "执行测试前的准备工作")
        self.setup_test()
        self.step_logger.log_action("前置操作完成")
        self.step_logger.end_step("passed")

        # 子类可以重写此方法来实现具体的测试逻辑
        logger.info(f"执行数据驱动测试用例: {case_name}")

        # 记录后置操作步骤
        self.step_logger.start_step("后置操作", "执行测试后的清理工作")
        self.teardown_test()
        self.step_logger.log_action("后置操作完成")
        self.step_logger.end_step("passed")

        # 默认返回成功结果
        return {
            'success': True,
            'message': '数据驱动测试用例执行完成'
        }
    
    def run_data_driven_tests(self, data_file: str, case_filter: Dict[str, Any] = None):
        """
        运行数据驱动测试
        
        Args:
            data_file: 数据文件路径
            case_filter: 用例过滤条件
        """
        test_cases = self.get_test_cases(data_file, case_filter)
        
        for test_case in test_cases:
            self.current_case_data = test_case
            try:
                self.execute_test_case(test_case)
            except Exception as e:
                # 记录错误但继续执行其他用例
                logger.error(f"数据驱动测试用例失败: {test_case.get('case_name', 'Unknown')}, 错误: {e}")
                continue
    
    def get_current_case_data(self) -> Optional[Dict[str, Any]]:
        """获取当前执行的用例数据"""
        return self.current_case_data


class ParametrizedTestBase(TestBase):
    """参数化测试基类"""
    
    @staticmethod
    def parametrize_from_file(data_file: str, case_filter: Dict[str, Any] = None):
        """
        从文件生成参数化测试数据
        
        Args:
            data_file: 数据文件路径
            case_filter: 用例过滤条件
            
        Returns:
            pytest参数化装饰器
        """
        data_parser = DataParser()
        test_cases = data_parser.get_test_cases(data_file, case_filter)
        
        # 生成参数化数据
        case_names = [case.get('case_name', f'case_{i}') for i, case in enumerate(test_cases)]
        
        return pytest.mark.parametrize('test_case', test_cases, ids=case_names)
