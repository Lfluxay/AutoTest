from typing import Any, Dict, List, Union, Optional
import re
import json
from jsonpath_ng import parse
from utils.logging.logger import logger


class AssertionHelper:
    """断言辅助工具类"""
    
    @staticmethod
    def compare_values(actual: Any, expected: Any, operator: str = "eq") -> bool:
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
            if operator == "eq" or operator == "==":
                return actual == expected
            elif operator == "ne" or operator == "!=":
                return actual != expected
            elif operator == "gt" or operator == ">":
                return float(actual) > float(expected)
            elif operator == "ge" or operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "lt" or operator == "<":
                return float(actual) < float(expected)
            elif operator == "le" or operator == "<=":
                return float(actual) <= float(expected)
            elif operator == "in":
                return str(expected) in str(actual)
            elif operator == "not_in":
                return str(expected) not in str(actual)
            elif operator == "contains":
                return str(expected) in str(actual)
            elif operator == "not_contains":
                return str(expected) not in str(actual)
            elif operator == "startswith":
                return str(actual).startswith(str(expected))
            elif operator == "endswith":
                return str(actual).endswith(str(expected))
            elif operator == "regex" or operator == "match":
                return bool(re.search(str(expected), str(actual)))
            elif operator == "not_regex" or operator == "not_match":
                return not bool(re.search(str(expected), str(actual)))
            elif operator == "empty":
                return not actual or actual == "" or actual == [] or actual == {}
            elif operator == "not_empty":
                return bool(actual) and actual != "" and actual != [] and actual != {}
            elif operator == "null" or operator == "none":
                return actual is None
            elif operator == "not_null" or operator == "not_none":
                return actual is not None
            elif operator == "type":
                return type(actual).__name__ == str(expected)
            elif operator == "length":
                return len(actual) == int(expected)
            elif operator == "length_gt":
                return len(actual) > int(expected)
            elif operator == "length_ge":
                return len(actual) >= int(expected)
            elif operator == "length_lt":
                return len(actual) < int(expected)
            elif operator == "length_le":
                return len(actual) <= int(expected)
            else:
                logger.warning(f"不支持的比较操作符: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"值比较异常: {e}")
            return False
    
    @staticmethod
    def extract_json_path(data: Union[str, dict], path: str) -> Any:
        """
        使用JSONPath提取数据
        
        Args:
            data: JSON数据
            path: JSONPath表达式
            
        Returns:
            提取的值
        """
        try:
            if isinstance(data, str):
                data = json.loads(data)
            
            jsonpath_expr = parse(path)
            matches = jsonpath_expr.find(data)
            
            if matches:
                if len(matches) == 1:
                    return matches[0].value
                else:
                    return [match.value for match in matches]
            else:
                return None
                
        except Exception as e:
            logger.error(f"JSONPath提取失败: {path}, 错误: {e}")
            return None
    
    @staticmethod
    def extract_regex(text: str, pattern: str, group: int = 0) -> Optional[str]:
        """
        使用正则表达式提取数据
        
        Args:
            text: 源文本
            pattern: 正则表达式
            group: 捕获组索引
            
        Returns:
            提取的值
        """
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(group)
            else:
                return None
                
        except Exception as e:
            logger.error(f"正则表达式提取失败: {pattern}, 错误: {e}")
            return None
    
    @staticmethod
    def validate_json_schema(data: Union[str, dict], schema: dict) -> bool:
        """
        验证JSON Schema
        
        Args:
            data: JSON数据
            schema: JSON Schema
            
        Returns:
            验证结果
        """
        try:
            import jsonschema
            
            if isinstance(data, str):
                data = json.loads(data)
            
            jsonschema.validate(data, schema)
            return True
            
        except ImportError:
            logger.warning("jsonschema库未安装，跳过Schema验证")
            return True
        except Exception as e:
            logger.error(f"JSON Schema验证失败: {e}")
            return False
    
    @staticmethod
    def assert_response_structure(response_data: dict, expected_keys: List[str], 
                                strict: bool = False) -> bool:
        """
        断言响应结构
        
        Args:
            response_data: 响应数据
            expected_keys: 期望的键列表
            strict: 是否严格模式（只能包含期望的键）
            
        Returns:
            断言结果
        """
        try:
            actual_keys = set(response_data.keys())
            expected_keys_set = set(expected_keys)
            
            # 检查是否包含所有期望的键
            missing_keys = expected_keys_set - actual_keys
            if missing_keys:
                logger.error(f"响应缺少必需的键: {missing_keys}")
                return False
            
            # 严格模式下检查是否有多余的键
            if strict:
                extra_keys = actual_keys - expected_keys_set
                if extra_keys:
                    logger.error(f"响应包含多余的键: {extra_keys}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"响应结构断言失败: {e}")
            return False
    
    @staticmethod
    def assert_list_contains(actual_list: List[Any], expected_item: Any, 
                           key: str = None) -> bool:
        """
        断言列表包含指定项
        
        Args:
            actual_list: 实际列表
            expected_item: 期望项
            key: 如果列表项是字典，指定比较的键
            
        Returns:
            断言结果
        """
        try:
            if not isinstance(actual_list, list):
                logger.error(f"实际值不是列表: {type(actual_list)}")
                return False
            
            if key:
                # 在字典列表中查找
                for item in actual_list:
                    if isinstance(item, dict) and item.get(key) == expected_item:
                        return True
                return False
            else:
                # 直接查找
                return expected_item in actual_list
                
        except Exception as e:
            logger.error(f"列表包含断言失败: {e}")
            return False
    
    @staticmethod
    def assert_list_length(actual_list: List[Any], expected_length: int, 
                          operator: str = "eq") -> bool:
        """
        断言列表长度
        
        Args:
            actual_list: 实际列表
            expected_length: 期望长度
            operator: 比较操作符
            
        Returns:
            断言结果
        """
        try:
            if not isinstance(actual_list, list):
                logger.error(f"实际值不是列表: {type(actual_list)}")
                return False
            
            actual_length = len(actual_list)
            return AssertionHelper.compare_values(actual_length, expected_length, operator)
            
        except Exception as e:
            logger.error(f"列表长度断言失败: {e}")
            return False
    
    @staticmethod
    def assert_dict_subset(actual_dict: dict, expected_subset: dict) -> bool:
        """
        断言字典包含子集
        
        Args:
            actual_dict: 实际字典
            expected_subset: 期望的子集
            
        Returns:
            断言结果
        """
        try:
            if not isinstance(actual_dict, dict):
                logger.error(f"实际值不是字典: {type(actual_dict)}")
                return False
            
            for key, expected_value in expected_subset.items():
                if key not in actual_dict:
                    logger.error(f"字典缺少键: {key}")
                    return False
                
                actual_value = actual_dict[key]
                if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                    # 递归检查嵌套字典
                    if not AssertionHelper.assert_dict_subset(actual_value, expected_value):
                        return False
                elif actual_value != expected_value:
                    logger.error(f"字典值不匹配: {key}, 期望: {expected_value}, 实际: {actual_value}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"字典子集断言失败: {e}")
            return False
    
    @staticmethod
    def assert_numeric_range(actual: Union[int, float], min_value: Union[int, float] = None,
                           max_value: Union[int, float] = None, inclusive: bool = True) -> bool:
        """
        断言数值范围
        
        Args:
            actual: 实际值
            min_value: 最小值
            max_value: 最大值
            inclusive: 是否包含边界值
            
        Returns:
            断言结果
        """
        try:
            actual = float(actual)
            
            if min_value is not None:
                min_value = float(min_value)
                if inclusive:
                    if actual < min_value:
                        logger.error(f"数值小于最小值: {actual} < {min_value}")
                        return False
                else:
                    if actual <= min_value:
                        logger.error(f"数值小于等于最小值: {actual} <= {min_value}")
                        return False
            
            if max_value is not None:
                max_value = float(max_value)
                if inclusive:
                    if actual > max_value:
                        logger.error(f"数值大于最大值: {actual} > {max_value}")
                        return False
                else:
                    if actual >= max_value:
                        logger.error(f"数值大于等于最大值: {actual} >= {max_value}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"数值范围断言失败: {e}")
            return False
    
    @staticmethod
    def format_assertion_message(assertion_type: str, expected: Any, actual: Any, 
                               operator: str = "eq", custom_message: str = "") -> str:
        """
        格式化断言错误消息
        
        Args:
            assertion_type: 断言类型
            expected: 期望值
            actual: 实际值
            operator: 操作符
            custom_message: 自定义消息
            
        Returns:
            格式化的错误消息
        """
        if custom_message:
            return custom_message
        
        if operator == "eq":
            return f"{assertion_type}断言失败: 期望 {expected}, 实际 {actual}"
        elif operator == "ne":
            return f"{assertion_type}断言失败: 期望不等于 {expected}, 实际 {actual}"
        elif operator in ["gt", "ge", "lt", "le"]:
            op_map = {"gt": ">", "ge": ">=", "lt": "<", "le": "<="}
            return f"{assertion_type}断言失败: 期望 {actual} {op_map[operator]} {expected}"
        elif operator in ["in", "contains"]:
            return f"{assertion_type}断言失败: 期望 {actual} 包含 {expected}"
        elif operator in ["not_in", "not_contains"]:
            return f"{assertion_type}断言失败: 期望 {actual} 不包含 {expected}"
        else:
            return f"{assertion_type}断言失败: 期望 {expected} ({operator}), 实际 {actual}"


# 便捷函数
def compare_values(actual: Any, expected: Any, operator: str = "eq") -> bool:
    """比较值的便捷函数"""
    return AssertionHelper.compare_values(actual, expected, operator)

def extract_json_path(data: Union[str, dict], path: str) -> Any:
    """JSONPath提取的便捷函数"""
    return AssertionHelper.extract_json_path(data, path)

def extract_regex(text: str, pattern: str, group: int = 0) -> Optional[str]:
    """正则提取的便捷函数"""
    return AssertionHelper.extract_regex(text, pattern, group)
