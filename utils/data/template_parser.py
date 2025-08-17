"""
模板解析器
支持模板+数据集的数据驱动测试方式，大幅减少重复代码
"""
import os
import re
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from copy import deepcopy
from utils.logging.logger import logger
from utils.core.exceptions import AutoTestException


class TemplateParser:
    """模板解析器"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化模板解析器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.templates_cache: Dict[str, Dict[str, Any]] = {}
        self.datasets_cache: Dict[str, Dict[str, Any]] = {}
        self.context_file: Optional[str] = None

    def set_context_file(self, file_path: str):
        """设置上下文文件路径"""
        self.context_file = file_path
        
    def load_template(self, template_path: str, context_file: Optional[str] = None) -> Dict[str, Any]:
        """
        加载模板文件，支持文件内模板和外部模板

        Args:
            template_path: 模板路径，格式为 "file_path#template_name" 或 "#template_name"（文件内模板）
            context_file: 上下文文件路径，用于解析文件内模板

        Returns:
            模板内容
        """
        if '#' not in template_path:
            raise AutoTestException(f"模板路径格式错误，应为 'file_path#template_name' 或 '#template_name': {template_path}", "INVALID_TEMPLATE_PATH")

        file_path, template_name = template_path.split('#', 1)

        # 处理文件内模板（以#开头）
        if not file_path:
            if not context_file:
                raise AutoTestException(f"文件内模板需要提供上下文文件: {template_path}", "MISSING_CONTEXT_FILE")
            file_path = context_file

        # 检查缓存
        cache_key = f"{file_path}#{template_name}"
        if cache_key in self.templates_cache:
            return self.templates_cache[cache_key]

        # 处理简化路径格式（如 api.auth.login#standard_login）
        if '.' in file_path and not file_path.endswith('.yaml'):
            file_path = self._resolve_simplified_path(file_path)

        # 构建完整文件路径
        full_path = self.project_root / file_path
        if not full_path.exists():
            raise AutoTestException(f"模板文件不存在: {full_path}", "TEMPLATE_FILE_NOT_FOUND")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)

            if 'templates' not in template_data:
                raise AutoTestException(f"模板文件格式错误，缺少 'templates' 节点: {full_path}", "INVALID_TEMPLATE_FORMAT")

            if template_name not in template_data['templates']:
                available_templates = list(template_data['templates'].keys())
                raise AutoTestException(
                    f"模板 '{template_name}' 不存在，可用模板: {available_templates}",
                    "TEMPLATE_NOT_FOUND"
                )

            template = template_data['templates'][template_name]

            # 缓存模板
            self.templates_cache[cache_key] = template

            logger.debug(f"加载模板成功: {template_path}")
            return template

        except yaml.YAMLError as e:
            raise AutoTestException(f"解析模板文件失败: {full_path}, 错误: {e}", "TEMPLATE_PARSE_ERROR")
        except Exception as e:
            raise AutoTestException(f"加载模板文件失败: {full_path}, 错误: {e}", "TEMPLATE_LOAD_ERROR")

    def _resolve_simplified_path(self, simplified_path: str) -> str:
        """
        解析简化路径格式

        Args:
            simplified_path: 简化路径，如 "api.auth.login"

        Returns:
            完整路径，如 "data/templates/api/auth/login.yaml"
        """
        parts = simplified_path.split('.')
        if len(parts) < 2:
            raise AutoTestException(f"简化路径格式错误: {simplified_path}", "INVALID_SIMPLIFIED_PATH")

        # 第一部分是类型（api/web/workflow）
        template_type = parts[0]

        # 其余部分是路径
        path_parts = parts[1:]

        # 构建路径
        path = f"data/templates/{template_type}/" + "/".join(path_parts) + ".yaml"

        return path
    
    def load_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """
        加载数据集
        
        Args:
            dataset_path: 数据集路径，格式为 "file_path#dataset_name"
            
        Returns:
            数据集列表
        """
        if '#' not in dataset_path:
            raise AutoTestException(f"数据集路径格式错误，应为 'file_path#dataset_name': {dataset_path}", "INVALID_DATASET_PATH")
        
        file_path, dataset_name = dataset_path.split('#', 1)
        
        # 检查缓存
        cache_key = f"{file_path}#{dataset_name}"
        if cache_key in self.datasets_cache:
            return self.datasets_cache[cache_key]
        
        # 构建完整文件路径
        full_path = self.project_root / file_path
        if not full_path.exists():
            raise AutoTestException(f"数据集文件不存在: {full_path}", "DATASET_FILE_NOT_FOUND")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                dataset_data = yaml.safe_load(f)
            
            if 'datasets' not in dataset_data:
                raise AutoTestException(f"数据集文件格式错误，缺少 'datasets' 节点: {full_path}", "INVALID_DATASET_FORMAT")
            
            if dataset_name not in dataset_data['datasets']:
                available_datasets = list(dataset_data['datasets'].keys())
                raise AutoTestException(
                    f"数据集 '{dataset_name}' 不存在，可用数据集: {available_datasets}", 
                    "DATASET_NOT_FOUND"
                )
            
            dataset = dataset_data['datasets'][dataset_name]
            
            # 缓存数据集
            self.datasets_cache[cache_key] = dataset
            
            logger.debug(f"加载数据集成功: {dataset_path}, 数据条数: {len(dataset)}")
            return dataset
            
        except yaml.YAMLError as e:
            raise AutoTestException(f"解析数据集文件失败: {full_path}, 错误: {e}", "DATASET_PARSE_ERROR")
        except Exception as e:
            raise AutoTestException(f"加载数据集文件失败: {full_path}, 错误: {e}", "DATASET_LOAD_ERROR")
    
    def substitute_variables(self, template: Any, variables: Dict[str, Any]) -> Any:
        """
        替换模板中的变量
        
        Args:
            template: 模板内容（可以是字典、列表、字符串等）
            variables: 变量字典
            
        Returns:
            替换后的内容
        """
        if isinstance(template, str):
            return self._substitute_string_variables(template, variables)
        elif isinstance(template, dict):
            result = {}
            for key, value in template.items():
                # 键也可能包含变量
                new_key = self.substitute_variables(key, variables)
                new_value = self.substitute_variables(value, variables)
                result[new_key] = new_value
            return result
        elif isinstance(template, list):
            return [self.substitute_variables(item, variables) for item in template]
        else:
            return template
    
    def _substitute_string_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """
        替换字符串中的变量
        
        Args:
            text: 包含变量的字符串
            variables: 变量字典
            
        Returns:
            替换后的字符串
        """
        if not isinstance(text, str):
            return text
        
        # 匹配 ${variable_name} 格式的变量
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            
            # 支持嵌套属性访问，如 ${test_data.username}
            if '.' in var_name:
                parts = var_name.split('.')
                value = variables
                try:
                    for part in parts:
                        value = value[part]
                    return str(value)
                except (KeyError, TypeError):
                    logger.warning(f"变量 '{var_name}' 未找到，保持原样")
                    return match.group(0)
            else:
                # 简单变量访问
                if var_name in variables:
                    return str(variables[var_name])
                else:
                    logger.warning(f"变量 '{var_name}' 未找到，保持原样")
                    return match.group(0)
        
        return re.sub(pattern, replace_var, text)
    
    def evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """
        评估条件表达式
        
        Args:
            condition: 条件表达式，如 "${expected_code} == 0"
            variables: 变量字典
            
        Returns:
            条件是否为真
        """
        if not condition:
            return True
        
        try:
            # 先替换变量
            condition_str = self.substitute_variables(condition, variables)
            
            # 简单的条件评估（安全起见，只支持基本操作）
            # 支持的操作符：==, !=, >, <, >=, <=, and, or, not
            
            # 处理布尔值
            condition_str = condition_str.replace('True', 'true').replace('False', 'false')
            
            # 简单的表达式评估
            if condition_str.lower() in ['true', '1']:
                return True
            elif condition_str.lower() in ['false', '0']:
                return False
            elif condition_str.startswith('not '):
                return not self.evaluate_condition(condition_str[4:], variables)
            elif ' == ' in condition_str:
                left, right = condition_str.split(' == ', 1)
                return self._compare_values(left.strip(), right.strip())
            elif ' != ' in condition_str:
                left, right = condition_str.split(' != ', 1)
                return not self._compare_values(left.strip(), right.strip())
            elif ' >= ' in condition_str:
                left, right = condition_str.split(' >= ', 1)
                return self._numeric_compare(left.strip(), right.strip(), '>=')
            elif ' <= ' in condition_str:
                left, right = condition_str.split(' <= ', 1)
                return self._numeric_compare(left.strip(), right.strip(), '<=')
            elif ' > ' in condition_str:
                left, right = condition_str.split(' > ', 1)
                return self._numeric_compare(left.strip(), right.strip(), '>')
            elif ' < ' in condition_str:
                left, right = condition_str.split(' < ', 1)
                return self._numeric_compare(left.strip(), right.strip(), '<')
            else:
                # 默认返回True
                logger.warning(f"无法解析条件表达式: {condition}, 默认返回True")
                return True
                
        except Exception as e:
            logger.error(f"评估条件表达式失败: {condition}, 错误: {e}, 默认返回True")
            return True
    
    def _compare_values(self, left: str, right: str) -> bool:
        """比较两个值是否相等"""
        # 去除引号
        left = left.strip('\'"')
        right = right.strip('\'"')
        
        # 尝试数值比较
        try:
            return float(left) == float(right)
        except ValueError:
            # 字符串比较
            return left == right
    
    def _numeric_compare(self, left: str, right: str, operator: str) -> bool:
        """数值比较"""
        try:
            left_val = float(left)
            right_val = float(right)
            
            if operator == '>':
                return left_val > right_val
            elif operator == '<':
                return left_val < right_val
            elif operator == '>=':
                return left_val >= right_val
            elif operator == '<=':
                return left_val <= right_val
            else:
                return False
        except ValueError:
            logger.warning(f"无法进行数值比较: {left} {operator} {right}")
            return False
    
    def filter_by_condition(self, items: List[Dict[str, Any]], variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据条件过滤项目
        
        Args:
            items: 项目列表
            variables: 变量字典
            
        Returns:
            过滤后的项目列表
        """
        filtered_items = []
        
        for item in items:
            condition = item.get('condition')
            if condition is None or self.evaluate_condition(condition, variables):
                # 移除condition字段，避免传递给后续处理
                filtered_item = {k: v for k, v in item.items() if k != 'condition'}
                filtered_items.append(filtered_item)
        
        return filtered_items
    
    def generate_test_cases(self, case_config: Dict[str, Any], context_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据用例配置生成完整的测试用例

        Args:
            case_config: 用例配置，包含template、dataset等信息
            context_file: 上下文文件路径，用于解析文件内模板

        Returns:
            生成的测试用例列表
        """
        template_path = case_config.get('template')
        dataset_path = case_config.get('dataset')
        test_data = case_config.get('test_data')
        override_config = case_config.get('override', {})

        if not template_path:
            raise AutoTestException("用例配置缺少template字段", "MISSING_TEMPLATE")

        # 加载模板
        template = self.load_template(template_path, context_file or self.context_file)
        
        # 获取测试数据
        if dataset_path:
            # 从数据集文件加载
            test_data_list = self.load_dataset(dataset_path)
        elif test_data:
            # 直接使用配置中的数据
            test_data_list = test_data if isinstance(test_data, list) else [test_data]
        else:
            raise AutoTestException("用例配置缺少dataset或test_data字段", "MISSING_TEST_DATA")
        
        generated_cases = []
        
        for i, data_item in enumerate(test_data_list):
            # 创建变量字典
            variables = deepcopy(data_item)
            
            # 生成用例
            test_case = deepcopy(template)
            
            # 替换变量
            test_case = self.substitute_variables(test_case, variables)
            
            # 应用覆盖配置
            if override_config:
                test_case = self._apply_override(test_case, override_config, variables)
            
            # 过滤条件项目
            if 'assertions' in test_case:
                test_case['assertions'] = self.filter_by_condition(test_case['assertions'], variables)
            if 'extract' in test_case:
                test_case['extract'] = self.filter_by_condition(test_case['extract'], variables)
            if 'steps' in test_case:
                test_case['steps'] = self.filter_by_condition(test_case['steps'], variables)
            
            # 添加用例元信息
            test_case['case_name'] = f"{case_config.get('case_name', 'Generated Case')} - {data_item.get('name', f'Data {i+1}')}"
            test_case['description'] = case_config.get('description', template.get('description', ''))
            test_case['tags'] = case_config.get('tags', []) + data_item.get('tags', [])
            test_case['severity'] = case_config.get('severity', 'normal')
            
            generated_cases.append(test_case)
        
        logger.info(f"生成测试用例成功: {len(generated_cases)} 个用例")
        return generated_cases
    
    def _apply_override(self, test_case: Dict[str, Any], override_config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用覆盖配置
        
        Args:
            test_case: 测试用例
            override_config: 覆盖配置
            variables: 变量字典
            
        Returns:
            应用覆盖后的测试用例
        """
        for key, value in override_config.items():
            if key in test_case:
                if isinstance(value, dict) and isinstance(test_case[key], dict):
                    # 字典合并
                    test_case[key].update(self.substitute_variables(value, variables))
                elif isinstance(value, list):
                    # 列表替换
                    test_case[key] = self.substitute_variables(value, variables)
                else:
                    # 直接替换
                    test_case[key] = self.substitute_variables(value, variables)
            else:
                # 新增字段
                test_case[key] = self.substitute_variables(value, variables)
        
        return test_case
    
    def clear_cache(self):
        """清除缓存"""
        self.templates_cache.clear()
        self.datasets_cache.clear()
        logger.debug("模板和数据集缓存已清除")


# 全局模板解析器实例
template_parser = TemplateParser()
