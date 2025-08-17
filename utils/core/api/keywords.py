from typing import Dict, Any, List
from utils.core.api.client import get_api_client
from utils.core.api.assertions import assert_multiple
from utils.logging.logger import logger, logger_manager
from utils.data.extractor import Extractor, variable_manager
from utils.core.base.keywords_base import KeywordsBase


class APIKeywords(KeywordsBase):
    """API关键字类 - 提供API测试的关键字操作"""
    
    def __init__(self):
        super().__init__()
        self.client = get_api_client()
    
    def execute(self, action: str, params: Dict[str, Any] = None) -> Any:
        """
        执行API关键字操作
        
        Args:
            action: 操作名称
            params: 操作参数
            
        Returns:
            操作结果
        """
        if params is None:
            params = {}
        
        self.log_action(action, f"参数: {params}")
        
        # 根据动作类型执行相应操作
        if action == "send_request":
            return self.send_request(params)
        elif action == "verify_response":
            response = params.get("response")
            assertions = params.get("assertions", [])
            return self.verify_response(response, assertions)
        elif action == "extract_data":
            response = params.get("response")
            extract_config = params.get("extract_config", [])
            return self.extract_data(response, extract_config)
        else:
            logger.warning(f"未知的API动作: {action}")
            return None
    
    def send_request(self, request_config: Dict[str, Any]) -> Any:
        """
        发送HTTP请求关键字
        
        Args:
            request_config: 请求配置
                {
                    "method": "POST",
                    "url": "/api/login",
                    "headers": {"Content-Type": "application/json"},
                    "params": {"page": 1},
                    "data": {"username": "admin"},
                    "json": {"username": "admin"},
                    "files": {"file": ("test.txt", "content")}
                }
        
        Returns:
            响应对象
        """
        method = request_config.get("method", "GET")
        url = request_config.get("url")
        
        if not url:
            raise ValueError("请求URL不能为空")
        
        # 准备请求参数
        kwargs = {}
        
        # 请求头
        if "headers" in request_config:
            kwargs["headers"] = request_config["headers"]
        
        # URL参数
        if "params" in request_config:
            kwargs["params"] = request_config["params"]
        
        # 请求体数据
        if "data" in request_config:
            kwargs["data"] = request_config["data"]
        
        # JSON数据
        if "json" in request_config:
            kwargs["json"] = request_config["json"]
        
        # 文件数据
        if "files" in request_config:
            kwargs["files"] = request_config["files"]
        
        # 超时时间
        if "timeout" in request_config:
            kwargs["timeout"] = request_config["timeout"]
        
        # 发送请求
        logger_manager.log_step(f"发送{method}请求", url)
        response = self.client.request(method, url, **kwargs)
        
        return response
    
    def get_request(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Any:
        """GET请求关键字"""
        request_config = {
            "method": "GET",
            "url": url
        }
        
        if params:
            request_config["params"] = params
        if headers:
            request_config["headers"] = headers
        
        return self.send_request(request_config)
    
    def post_request(self, url: str, json: Dict[str, Any] = None, data: Any = None, headers: Dict[str, str] = None) -> Any:
        """POST请求关键字"""
        request_config = {
            "method": "POST",
            "url": url
        }
        
        if json:
            request_config["json"] = json
        if data:
            request_config["data"] = data
        if headers:
            request_config["headers"] = headers
        
        return self.send_request(request_config)
    
    def put_request(self, url: str, json: Dict[str, Any] = None, data: Any = None, headers: Dict[str, str] = None) -> Any:
        """PUT请求关键字"""
        request_config = {
            "method": "PUT",
            "url": url
        }
        
        if json:
            request_config["json"] = json
        if data:
            request_config["data"] = data
        if headers:
            request_config["headers"] = headers
        
        return self.send_request(request_config)
    
    def delete_request(self, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Any:
        """DELETE请求关键字"""
        request_config = {
            "method": "DELETE",
            "url": url
        }
        
        if params:
            request_config["params"] = params
        if headers:
            request_config["headers"] = headers
        
        return self.send_request(request_config)
    
    def upload_file(self, url: str, file_path: str, file_field: str = "file", headers: Dict[str, str] = None) -> Any:
        """文件上传关键字"""
        from pathlib import Path
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {file_field: (file_path.name, f, 'application/octet-stream')}
            
            request_config = {
                "method": "POST",
                "url": url,
                "files": files
            }
            
            if headers:
                request_config["headers"] = headers
            
            logger_manager.log_step("上传文件", f"{file_path} -> {url}")
            return self.send_request(request_config)
    
    def verify_response(self, response: Any, assertions: List[Dict[str, Any]]):
        """验证响应关键字"""
        if not assertions:
            logger.warning("没有配置断言，跳过验证")
            return
        
        logger_manager.log_step("验证响应", f"{len(assertions)}个断言")
        assert_multiple(response, assertions)
        logger.info("响应验证通过")
    
    def extract_data(self, response: Any, extract_config: List[Dict[str, str]]) -> Dict[str, Any]:
        """提取数据关键字"""
        if not extract_config:
            logger.debug("没有配置数据提取")
            return {}
        
        logger_manager.log_step("提取数据", f"{len(extract_config)}个提取项")
        
        # 获取响应数据
        try:
            if hasattr(response, 'json'):
                response_data = response.json()
            else:
                response_data = response.text
        except Exception:
            response_data = response.text
        
        # 提取数据
        extracted_data = Extractor.extract_from_response(response_data, extract_config)
        
        # 更新变量管理器
        variable_manager.update_variables(extracted_data)
        
        logger.info(f"数据提取完成: {extracted_data}")
        return extracted_data
    
    def set_global_header(self, key: str, value: str):
        """设置全局请求头关键字"""
        self.client.session.headers[key] = value
        logger_manager.log_step("设置全局请求头", f"{key}: {value}")
    
    def remove_global_header(self, key: str):
        """删除全局请求头关键字"""
        if key in self.client.session.headers:
            del self.client.session.headers[key]
            logger_manager.log_step("删除全局请求头", key)
    
    def set_token(self, token: str):
        """设置认证token关键字"""
        self.client.set_token(token)
        logger_manager.log_step("设置认证token", f"{token[:20]}...")
    
    def clear_token(self):
        """清除认证token关键字"""
        self.client.clear_token()
        logger_manager.log_step("清除认证token", "")
    
    def login(self) -> bool:
        """执行登录关键字"""
        logger_manager.log_step("执行全局登录", "")
        result = self.client.login()
        
        if result:
            logger.info("登录成功")
        else:
            logger.error("登录失败")
        
        return result
    
    def wait(self, seconds: float):
        """等待关键字"""
        import time
        logger_manager.log_step("等待", f"{seconds}秒")
        time.sleep(seconds)
    
    def set_variable(self, name: str, value: Any):
        """设置变量关键字"""
        variable_manager.set_variable(name, value)
        logger_manager.log_step("设置变量", f"{name} = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量关键字"""
        value = variable_manager.get_variable(name, default)
        logger_manager.log_step("获取变量", f"{name} = {value}")
        return value
    
    def generate_test_data(self, template: Dict[str, str]) -> Dict[str, Any]:
        """生成测试数据关键字"""
        logger_manager.log_step("生成测试数据", str(template))

        try:
            from utils.faker_helper import faker_helper
            test_data = faker_helper.custom_data(template)
        except ImportError:
            logger.warning("faker_helper未找到，使用基础数据生成")
            test_data = self._generate_basic_test_data(template)

        # 将生成的数据保存到变量管理器
        variable_manager.update_variables(test_data)

        logger.info(f"测试数据生成完成: {test_data}")
        return test_data

    def _generate_basic_test_data(self, template: Dict[str, str]) -> Dict[str, Any]:
        """基础测试数据生成"""
        import time
        import random

        test_data = {}
        timestamp = str(int(time.time()))

        for key, value_template in template.items():
            if "{timestamp}" in value_template:
                test_data[key] = value_template.replace("{timestamp}", timestamp)
            elif "{random_number}" in value_template:
                random_num = str(random.randint(1000, 9999))
                test_data[key] = value_template.replace("{random_number}", random_num)
            else:
                test_data[key] = value_template

        return test_data
    
    def execute_sql(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行SQL关键字"""
        logger_manager.log_step("执行SQL查询", sql[:100])

        try:
            from utils.io.db_helper import get_db_helper
            db_helper = get_db_helper()
            result = db_helper.execute_query(sql, params)
            logger.info(f"SQL执行完成，返回{len(result)}条记录")
            return result
        except ImportError:
            logger.error("数据库助手未找到，无法执行SQL")
            return []
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            return []


# 全局API关键字实例
api_keywords = APIKeywords()

# 便捷函数
def send_api_request(request_config: Dict[str, Any]) -> Any:
    """发送API请求便捷函数"""
    return api_keywords.send_request(request_config)

def verify_api_response(response: Any, assertions: List[Dict[str, Any]]):
    """验证API响应便捷函数"""
    api_keywords.verify_response(response, assertions)

def extract_api_data(response: Any, extract_config: List[Dict[str, str]]) -> Dict[str, Any]:
    """提取API数据便捷函数"""
    return api_keywords.extract_data(response, extract_config)