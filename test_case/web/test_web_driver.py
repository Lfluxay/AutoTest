import pytest
import allure
from pathlib import Path
from typing import Dict, Any
from utils.core.base.test_base import TestBase, DataDrivenTestBase
from utils.core.web.keywords import web_keywords
from utils.logging.logger import logger
from utils.config.parser import config


class WebTestBase(TestBase):
    """Web测试基类"""
    
    def setup_test(self):
        self.web_keywords = web_keywords
        logger.info("Web测试环境准备完成")
    
    def teardown_test(self):
        logger.info("Web测试环境清理完成")
    
    def _execute_case_logic(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行Web测试用例逻辑"""
        try:
            steps = test_case.get('steps', [])
            if not steps:
                raise ValueError("Web测试用例缺少steps配置")
            
            self.web_keywords.execute_steps(steps)
            
            assertions = test_case.get('assertions', [])
            if assertions:
                self.web_keywords.verify_response(assertions)
            
            extract_config = test_case.get('extract', [])
            extracted_data = {}
            if extract_config:
                extracted_data = self.web_keywords.extract_data(extract_config)
            
            return {
                'success': True,
                'extracted_data': extracted_data
            }
            
        except Exception as e:
            try:
                self.web_keywords.take_screenshot(f"failure_{test_case.get('case_name', 'unknown')}")
            except Exception:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }


@allure.feature("Web测试")
class TestWeb:
    """Web测试驱动类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, browser_manager, page, ensure_target_page):
        self.browser_manager = browser_manager
        self.page = page
        self.login_manager = ensure_target_page
        if not self.browser_manager or not self.page:
            pytest.skip("浏览器未初始化")
    
    @allure.story("页面功能测试")
    @pytest.mark.web
    @pytest.mark.smoke
    def test_web_page_cases(self, test_data_loader):
        """执行Web页面功能测试用例"""
        data_dir = config.get_data_dir() / "web"
        test_files = list(data_dir.rglob("*_cases.yaml"))
        
        if not test_files:
            pytest.skip("未找到Web测试用例文件")
        
        test_base = WebTestBase()
        test_base.setup_method(self.test_web_page_cases)
        
        try:
            for test_file in test_files:
                logger.info(f"执行Web测试文件: {test_file}")
                test_cases = test_data_loader(test_file)
                
                for test_case in test_cases:
                    with allure.step(f"执行用例: {test_case.get('case_name', 'Unknown')}"):
                        test_base.execute_test_case(test_case)
        
        finally:
            test_base.teardown_method(self.test_web_page_cases)


@allure.feature("数据驱动Web测试")
class TestDataDrivenWeb:
    """数据驱动Web测试驱动类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, browser_manager, page, ensure_target_page):
        self.browser_manager = browser_manager
        self.page = page
        self.login_manager = ensure_target_page
        if not self.browser_manager or not self.page:
            pytest.skip("浏览器未初始化")
    
    @allure.story("登录页面测试")
    @pytest.mark.web
    @pytest.mark.smoke
    def test_login_page_data_driven(self):
        """数据驱动登录页面测试"""
        data_file = config.get_data_dir() / "web" / "login" / "login_cases.yaml"
        
        if not data_file.exists():
            pytest.skip(f"测试数据文件不存在: {data_file}")
        
        test_base = DataDrivenTestBase()
        test_base.setup_method(self.test_login_page_data_driven)
        
        try:
            test_base.run_data_driven_tests(str(data_file))
            summary = test_base.get_test_summary()
            assert summary['total'] > 0, "没有执行任何测试用例"
            
            with allure.step("测试总结"):
                allure.attach(
                    f"总计: {summary['total']}, 通过: {summary['passed']}, "
                    f"失败: {summary['failed']}, 通过率: {summary['pass_rate']}%",
                    "测试总结",
                    allure.attachment_type.TEXT
                )
        
        finally:
            test_base.teardown_method(self.test_login_page_data_driven)
