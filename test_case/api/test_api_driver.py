import pytest
import allure
from pathlib import Path
from typing import Dict, Any
from utils.core.base.test_base import TestBase, DataDrivenTestBase
from utils.core.api.keywords import api_keywords
from utils.logging.logger import logger
from utils.config.parser import config


class APITestBase(TestBase):
    """API测试基类"""
    
    def setup_test(self):
        self.api_keywords = api_keywords
        logger.info("API测试环境准备完成")
    
    def teardown_test(self):
        logger.info("API测试环境清理完成")
    
    def _execute_case_logic(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行API测试用例逻辑"""
        try:
            request_config = test_case.get('request', {})
            if not request_config:
                raise ValueError("测试用例缺少request配置")
            
            response = self.api_keywords.send_request(request_config)
            
            assertions = test_case.get('assertions', [])
            if assertions:
                self.api_keywords.verify_response(response, assertions)
            
            extract_config = test_case.get('extract', [])
            extracted_data = {}
            if extract_config:
                extracted_data = self.api_keywords.extract_data(response, extract_config)
            
            return {
                'success': True,
                'response': response,
                'extracted_data': extracted_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


@allure.feature("API测试")
class TestAPI:
    """API测试驱动类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        self.api_client = api_client
        if not self.api_client:
            pytest.skip("API客户端未初始化")
    
    @allure.story("单接口测试")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_single_api_cases(self, test_data_loader):
        """执行单接口测试用例"""
        data_dir = config.get_data_dir() / "api"
        test_files = list(data_dir.rglob("*_cases.yaml"))
        
        if not test_files:
            pytest.skip("未找到API测试用例文件")
        
        test_base = APITestBase()
        test_base.setup_method(self.test_single_api_cases)
        
        try:
            for test_file in test_files:
                logger.info(f"执行测试文件: {test_file}")
                test_cases = test_data_loader(test_file)
                
                for test_case in test_cases:
                    if test_case.get('type') == 'workflow':
                        continue
                    
                    with allure.step(f"执行用例: {test_case.get('case_name', 'Unknown')}"):
                        test_base.execute_test_case(test_case)
        
        finally:
            test_base.teardown_method(self.test_single_api_cases)


@allure.feature("数据驱动API测试") 
class TestDataDrivenAPI:
    """数据驱动API测试驱动类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        self.api_client = api_client
        if not self.api_client:
            pytest.skip("API客户端未初始化")
    
    @allure.story("登录接口测试")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_login_api_data_driven(self):
        """数据驱动登录接口测试"""
        data_file = config.get_data_dir() / "api" / "login" / "login_cases.yaml"
        
        if not data_file.exists():
            pytest.skip(f"测试数据文件不存在: {data_file}")
        
        test_base = DataDrivenTestBase()
        test_base.setup_method(self.test_login_api_data_driven)
        
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
            test_base.teardown_method(self.test_login_api_data_driven)
