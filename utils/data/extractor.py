import re
import json
from typing import Any, Dict, List, Union, Optional
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.ext import parse as jsonpath_ext_parse
from utils.logging.logger import logger
from utils.core.exceptions import (
    DataParsingException,
    VariableException,
    handle_exceptions,
    retry_on_exception
)


class Extractor:
    """数据提取器 - 支持JSONPath和正则表达式提取"""
    
    @staticmethod
    def extract_by_jsonpath(data: Union[Dict, List, str], jsonpath: str) -> Any:
        """
        使用JSONPath提取数据
        
        Args:
            data: 源数据，可以是字典、列表或JSON字符串
            jsonpath: JSONPath表达式
            
        Returns:
            提取的数据，如果未找到返回None
        """
        try:
            # 如果是字符串，先转换为Python对象
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"JSON解析失败: {data[:100]}...")
                    return None
            
            # 使用扩展的JSONPath解析器，支持更多功能
            try:
                jsonpath_expr = jsonpath_ext_parse(jsonpath)
            except Exception:
                # 如果扩展解析器失败，使用基础解析器
                jsonpath_expr = jsonpath_parse(jsonpath)
            
            matches = jsonpath_expr.find(data)
            
            if not matches:
                logger.debug(f"JSONPath未找到匹配项: {jsonpath}")
                return None
            
            # 如果只有一个匹配项，直接返回值
            if len(matches) == 1:
                result = matches[0].value
                logger.debug(f"JSONPath提取成功: {jsonpath} -> {result}")
                return result
            
            # 如果有多个匹配项，返回列表
            result = [match.value for match in matches]
            logger.debug(f"JSONPath提取成功: {jsonpath} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"JSONPath提取失败: {jsonpath}, 错误: {e}")
            return None
    
    @staticmethod
    def extract_by_regex(text: str, pattern: str, group: int = 1) -> Any:
        """
        使用正则表达式提取数据
        
        Args:
            text: 源文本
            pattern: 正则表达式模式
            group: 提取的分组，0表示整个匹配，1表示第一个分组
            
        Returns:
            提取的数据，如果未找到返回None
        """
        try:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                if group == 0:
                    result = match.group()
                else:
                    result = match.group(group) if group <= match.lastindex else None
                
                logger.debug(f"正则提取成功: {pattern} -> {result}")
                return result
            else:
                logger.debug(f"正则未找到匹配项: {pattern}")
                return None
                
        except re.error as e:
            logger.error(f"正则表达式错误: {pattern}, 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"正则提取失败: {pattern}, 错误: {e}")
            return None
    
    @staticmethod
    def extract_all_by_regex(text: str, pattern: str, group: int = 1) -> List[str]:
        """
        使用正则表达式提取所有匹配项
        
        Args:
            text: 源文本
            pattern: 正则表达式模式
            group: 提取的分组
            
        Returns:
            提取的数据列表
        """
        try:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                logger.debug(f"正则提取所有匹配: {pattern} -> {len(matches)}个匹配项")
                return matches
            else:
                logger.debug(f"正则未找到匹配项: {pattern}")
                return []
                
        except re.error as e:
            logger.error(f"正则表达式错误: {pattern}, 错误: {e}")
            return []
        except Exception as e:
            logger.error(f"正则提取失败: {pattern}, 错误: {e}")
            return []
    
    @staticmethod
    def extract_from_response(response_data: Any, extract_config: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        从响应数据中提取多个值
        
        Args:
            response_data: 响应数据
            extract_config: 提取配置列表，格式为:
                [
                    {"name": "token", "type": "jsonpath", "path": "$.data.token"},
                    {"name": "user_id", "type": "regex", "pattern": r"user_id:(\d+)", "group": 1}
                ]
                
        Returns:
            提取的数据字典
        """
        extracted_data = {}
        
        for config in extract_config:
            name = config.get('name')
            extract_type = config.get('type', 'jsonpath')
            
            if extract_type == 'jsonpath':
                path = config.get('path')
                if path:
                    value = Extractor.extract_by_jsonpath(response_data, path)
                    extracted_data[name] = value
                    
            elif extract_type == 'regex':
                pattern = config.get('pattern')
                group = config.get('group', 1)
                if pattern:
                    # 如果响应数据不是字符串，先转换
                    if not isinstance(response_data, str):
                        text = json.dumps(response_data) if isinstance(response_data, (dict, list)) else str(response_data)
                    else:
                        text = response_data
                    
                    value = Extractor.extract_by_regex(text, pattern, group)
                    extracted_data[name] = value
            
            else:
                logger.warning(f"不支持的提取类型: {extract_type}")
        
        logger.info(f"数据提取完成: {extracted_data}")
        return extracted_data
    
    @staticmethod
    def extract_from_header(headers: Dict[str, str], header_name: str) -> Optional[str]:
        """
        从HTTP头中提取数据
        
        Args:
            headers: HTTP头字典
            header_name: 头名称
            
        Returns:
            头值
        """
        # 头名称不区分大小写
        for key, value in headers.items():
            if key.lower() == header_name.lower():
                logger.debug(f"从头部提取数据: {header_name} -> {value}")
                return value
        
        logger.debug(f"未找到头部: {header_name}")
        return None
    
    @staticmethod
    def extract_cookies(response) -> Dict[str, str]:
        """
        从响应中提取Cookie
        
        Args:
            response: HTTP响应对象
            
        Returns:
            Cookie字典
        """
        try:
            cookies = {}
            if hasattr(response, 'cookies'):
                for cookie in response.cookies:
                    cookies[cookie.name] = cookie.value
            
            logger.debug(f"提取Cookies: {cookies}")
            return cookies
            
        except Exception as e:
            logger.error(f"提取Cookies失败: {e}")
            return {}


class VariableManager:
    """变量管理器 - 管理测试过程中的动态变量"""
    
    def __init__(self):
        self.variables = {}
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
        logger.debug(f"设置变量: {name} = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        value = self.variables.get(name, default)
        logger.debug(f"获取变量: {name} = {value}")
        return value
    
    def update_variables(self, new_variables: Dict[str, Any]):
        """批量更新变量"""
        self.variables.update(new_variables)
        logger.debug(f"批量更新变量: {new_variables}")
    
    def remove_variable(self, name: str):
        """删除变量"""
        if name in self.variables:
            del self.variables[name]
            logger.debug(f"删除变量: {name}")
    
    def clear_variables(self):
        """清空所有变量"""
        self.variables.clear()
        logger.debug("清空所有变量")
    
    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        return self.variables.copy()
    
    def replace_variables(self, data: Any) -> Any:
        """
        替换数据中的变量占位符
        支持格式: ${variable_name}
        
        Args:
            data: 要替换的数据
            
        Returns:
            替换后的数据
        """
        if isinstance(data, str):
            # 替换字符串中的变量
            for name, value in self.variables.items():
                placeholder = f"${{{name}}}"
                if placeholder in data:
                    data = data.replace(placeholder, str(value))
                    logger.debug(f"替换变量: {placeholder} -> {value}")
            return data
        
        elif isinstance(data, dict):
            # 递归处理字典
            return {key: self.replace_variables(value) for key, value in data.items()}
        
        elif isinstance(data, list):
            # 递归处理列表
            return [self.replace_variables(item) for item in data]
        
        else:
            # 其他类型直接返回
            return data


# 全局变量管理器实例
variable_manager = VariableManager()

# 便捷函数
def extract_jsonpath(data: Any, path: str) -> Any:
    """JSONPath提取便捷函数"""
    return Extractor.extract_by_jsonpath(data, path)

def extract_regex(text: str, pattern: str, group: int = 1) -> Any:
    """正则提取便捷函数"""
    return Extractor.extract_by_regex(text, pattern, group)

def set_variable(name: str, value: Any):
    """设置变量便捷函数"""
    variable_manager.set_variable(name, value)

def get_variable(name: str, default: Any = None) -> Any:
    """获取变量便捷函数"""
    return variable_manager.get_variable(name, default)

def replace_variables(data: Any) -> Any:
    """替换变量便捷函数"""
    return variable_manager.replace_variables(data)