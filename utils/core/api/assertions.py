import re
import json
from typing import Any, Dict, List, Union
from utils.logging.logger import logger, logger_manager
from utils.data.extractor import Extractor
from utils.io.db_helper import get_db_helper


class APIAssertions:
    """API断言类 - 提供各种断言方法"""
    
    @staticmethod
    def assert_status_code(response, expected: Union[int, List[int]], message: str = ""):
        """
        断言响应状态码
        
        Args:
            response: 响应对象
            expected: 期望的状态码，可以是单个值或列表
            message: 自定义错误消息
        """
        actual = response.status_code
        
        if isinstance(expected, list):
            success = actual in expected
            expected_str = f"in {expected}"
        else:
            success = actual == expected
            expected_str = str(expected)
        
        logger_manager.log_assertion("status_code", expected_str, str(actual), success)
        
        if not success:
            error_msg = message or f"状态码断言失败: 期望 {expected_str}, 实际 {actual}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_response_time(response, max_time: float, message: str = ""):
        """
        断言响应时间
        
        Args:
            response: 响应对象
            max_time: 最大响应时间（秒）
            message: 自定义错误消息
        """
        actual = response.elapsed.total_seconds()
        success = actual <= max_time
        
        logger_manager.log_assertion("response_time", f"<= {max_time}s", f"{actual:.3f}s", success)
        
        if not success:
            error_msg = message or f"响应时间断言失败: 期望 <= {max_time}s, 实际 {actual:.3f}s"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_json_path(response, json_path: str, expected: Any, operator: str = "eq", message: str = ""):
        """
        断言JSON路径值
        
        Args:
            response: 响应对象
            json_path: JSON路径表达式
            expected: 期望值
            operator: 比较操作符 (eq, ne, gt, ge, lt, le, contains, not_contains, in, not_in, empty, not_empty, regex)
            message: 自定义错误消息
        """
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            error_msg = message or f"响应不是有效的JSON格式"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        actual = Extractor.extract_by_jsonpath(response_json, json_path)
        
        success = APIAssertions._compare_values(actual, expected, operator)
        
        logger_manager.log_assertion(
            f"json_path[{json_path}] {operator}", 
            str(expected), 
            str(actual), 
            success
        )
        
        if not success:
            error_msg = message or f"JSON路径断言失败: {json_path} {operator} {expected}, 实际值: {actual}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_text_contains(response, text: str, case_sensitive: bool = True, message: str = ""):
        """
        断言响应文本包含指定内容
        
        Args:
            response: 响应对象
            text: 期望包含的文本
            case_sensitive: 是否区分大小写
            message: 自定义错误消息
        """
        response_text = response.text
        
        if case_sensitive:
            success = text in response_text
        else:
            success = text.lower() in response_text.lower()
        
        logger_manager.log_assertion("text_contains", text, "包含" if success else "不包含", success)
        
        if not success:
            error_msg = message or f"文本包含断言失败: 响应中不包含 '{text}'"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_text_not_contains(response, text: str, case_sensitive: bool = True, message: str = ""):
        """
        断言响应文本不包含指定内容
        
        Args:
            response: 响应对象
            text: 不应包含的文本
            case_sensitive: 是否区分大小写
            message: 自定义错误消息
        """
        response_text = response.text
        
        if case_sensitive:
            success = text not in response_text
        else:
            success = text.lower() not in response_text.lower()
        
        logger_manager.log_assertion("text_not_contains", f"不包含 {text}", "不包含" if success else "包含", success)
        
        if not success:
            error_msg = message or f"文本不包含断言失败: 响应中包含了不应该存在的 '{text}'"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_regex_match(response, pattern: str, message: str = ""):
        """
        断言响应文本匹配正则表达式
        
        Args:
            response: 响应对象
            pattern: 正则表达式模式
            message: 自定义错误消息
        """
        response_text = response.text
        success = bool(re.search(pattern, response_text, re.DOTALL))
        
        logger_manager.log_assertion("regex_match", pattern, "匹配" if success else "不匹配", success)
        
        if not success:
            error_msg = message or f"正则匹配断言失败: 响应不匹配模式 '{pattern}'"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_header_exists(response, header_name: str, message: str = ""):
        """
        断言响应头存在
        
        Args:
            response: 响应对象
            header_name: 请求头名称
            message: 自定义错误消息
        """
        success = header_name in response.headers
        
        logger_manager.log_assertion("header_exists", header_name, "存在" if success else "不存在", success)
        
        if not success:
            error_msg = message or f"响应头断言失败: 响应头 '{header_name}' 不存在"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_header_value(response, header_name: str, expected: str, operator: str = "eq", message: str = ""):
        """
        断言响应头值
        
        Args:
            response: 响应对象
            header_name: 请求头名称
            expected: 期望值
            operator: 比较操作符
            message: 自定义错误消息
        """
        actual = response.headers.get(header_name)
        
        if actual is None:
            error_msg = message or f"响应头 '{header_name}' 不存在"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        success = APIAssertions._compare_values(actual, expected, operator)
        
        logger_manager.log_assertion(f"header[{header_name}] {operator}", str(expected), str(actual), success)
        
        if not success:
            error_msg = message or f"响应头断言失败: {header_name} {operator} {expected}, 实际值: {actual}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_json_schema(response, schema: Dict[str, Any], message: str = ""):
        """
        断言JSON响应符合指定schema
        
        Args:
            response: 响应对象
            schema: JSON Schema
            message: 自定义错误消息
        """
        try:
            import jsonschema
            response_json = response.json()
            jsonschema.validate(response_json, schema)
            
            logger_manager.log_assertion("json_schema", "符合schema", "符合", True)
            return True
            
        except ImportError:
            logger.warning("jsonschema库未安装，跳过schema验证")
            return True
        except json.JSONDecodeError:
            error_msg = message or "响应不是有效的JSON格式"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        except jsonschema.ValidationError as e:
            error_msg = message or f"JSON Schema验证失败: {e.message}"
            logger.error(error_msg)
            logger_manager.log_assertion("json_schema", "符合schema", "不符合", False)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_database(sql: str, expected: Any, operator: str = "eq", message: str = ""):
        """
        断言数据库查询结果
        
        Args:
            sql: SQL查询语句
            expected: 期望值
            operator: 比较操作符
            message: 自定义错误消息
        """
        try:
            db_helper = get_db_helper()
            actual = db_helper.query_value(sql)
            
            success = APIAssertions._compare_values(actual, expected, operator)
            
            logger_manager.log_assertion(f"database {operator}", str(expected), str(actual), success)
            
            if not success:
                error_msg = message or f"数据库断言失败: {sql} 结果 {operator} {expected}, 实际值: {actual}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"数据库断言异常: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def _compare_values(actual: Any, expected: Any, operator: str) -> bool:
        """
        比较两个值
        
        Args:
            actual: 实际值
            expected: 期望值
            operator: 比较操作符
            
        Returns:
            比较结果
        """
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "gt":
                return actual > expected
            elif operator == "ge":
                return actual >= expected
            elif operator == "lt":
                return actual < expected
            elif operator == "le":
                return actual <= expected
            elif operator == "contains":
                return expected in str(actual)
            elif operator == "not_contains":
                return expected not in str(actual)
            elif operator == "in":
                return actual in expected
            elif operator == "not_in":
                return actual not in expected
            elif operator == "empty":
                return not actual or len(str(actual).strip()) == 0
            elif operator == "not_empty":
                return actual and len(str(actual).strip()) > 0
            elif operator == "regex":
                return bool(re.search(str(expected), str(actual), re.DOTALL))
            else:
                logger.warning(f"不支持的比较操作符: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"值比较异常: {e}")
            return False


def assert_api_response(response, assertion_config: Dict[str, Any]):
    """
    根据配置断言API响应
    
    Args:
        response: 响应对象
        assertion_config: 断言配置
    """
    assertion_type = assertion_config.get("type")
    
    if assertion_type == "status_code":
        expected = assertion_config.get("expected")
        message = assertion_config.get("message", "")
        APIAssertions.assert_status_code(response, expected, message)
        
    elif assertion_type == "response_time":
        max_time = assertion_config.get("max_time")
        message = assertion_config.get("message", "")
        APIAssertions.assert_response_time(response, max_time, message)
        
    elif assertion_type == "json_path":
        path = assertion_config.get("path")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        APIAssertions.assert_json_path(response, path, expected, operator, message)
        
    elif assertion_type == "text_contains":
        text = assertion_config.get("text")
        case_sensitive = assertion_config.get("case_sensitive", True)
        message = assertion_config.get("message", "")
        APIAssertions.assert_text_contains(response, text, case_sensitive, message)
        
    elif assertion_type == "regex":
        pattern = assertion_config.get("pattern")
        message = assertion_config.get("message", "")
        APIAssertions.assert_regex_match(response, pattern, message)
        
    elif assertion_type == "header":
        header_name = assertion_config.get("name")
        if "expected" in assertion_config:
            expected = assertion_config.get("expected")
            operator = assertion_config.get("operator", "eq")
            message = assertion_config.get("message", "")
            APIAssertions.assert_header_value(response, header_name, expected, operator, message)
        else:
            message = assertion_config.get("message", "")
            APIAssertions.assert_header_exists(response, header_name, message)
            
    elif assertion_type == "database":
        sql = assertion_config.get("sql")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        APIAssertions.assert_database(sql, expected, operator, message)
        
    else:
        logger.warning(f"不支持的断言类型: {assertion_type}")


def assert_multiple(response, assertions: List[Dict[str, Any]]):
    """
    执行多个断言
    
    Args:
        response: 响应对象
        assertions: 断言配置列表
    """
    for assertion in assertions:
        assert_api_response(response, assertion)