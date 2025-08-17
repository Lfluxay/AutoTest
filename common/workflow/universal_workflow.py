"""
通用工作流系统 - 支持配置驱动、插件化、模板化三种方案
"""
from typing import Dict, Any, List, Callable, Optional, Union
import yaml
import json
import importlib
from pathlib import Path
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from .workflow_cache import WorkflowCache
from .step_chain import StepChain


class UniversalWorkflowManager:
    """通用工作流管理器 - 支持多种工作流定义方式"""
    
    def __init__(self):
        self.config = get_merged_config()
        self.workflow_config = self.config.get('universal_workflow', {})
        self.step_registry = {}
        self.template_registry = {}
        self.workflow_cache = {}
        
        # 初始化内置步骤和模板
        self._register_builtin_steps()
        self._register_builtin_templates()
        
        logger.info("通用工作流管理器初始化完成")
    
    def _register_builtin_steps(self):
        """注册内置步骤"""
        # 登录步骤
        self.register_step('login', self._builtin_login_step)
        self.register_step('api_login', self._builtin_api_login_step)
        
        # 导航步骤
        self.register_step('navigate', self._builtin_navigate_step)
        self.register_step('select_option', self._builtin_select_option_step)
        self.register_step('click_element', self._builtin_click_element_step)
        self.register_step('fill_input', self._builtin_fill_input_step)
        
        # 验证步骤
        self.register_step('verify_element', self._builtin_verify_element_step)
        self.register_step('verify_url', self._builtin_verify_url_step)
        self.register_step('verify_api_response', self._builtin_verify_api_response_step)
        
        # 等待步骤
        self.register_step('wait_for_element', self._builtin_wait_for_element_step)
        self.register_step('wait_for_url', self._builtin_wait_for_url_step)

        # 导入并注册额外的内置步骤
        from .builtin_steps import BUILTIN_STEPS
        for step_name, step_func in BUILTIN_STEPS.items():
            self.register_step(step_name, step_func)
        
        logger.debug("内置步骤注册完成")
    
    def _register_builtin_templates(self):
        """注册内置模板"""
        # SaaS平台模板
        self.register_template('saas_platform', [
            {'name': '登录', 'type': 'login'},
            {'name': '选择租户', 'type': 'select_option', 'params': {'selector': '.tenant-selector'}},
            {'name': '进入工作区', 'type': 'navigate', 'params': {'target': '/workspace'}},
            {'name': '验证工作区', 'type': 'verify_element', 'params': {'selector': '.workspace-container'}}
        ])
        
        # ERP系统模板
        self.register_template('erp_system', [
            {'name': '登录', 'type': 'login'},
            {'name': '选择公司', 'type': 'select_option', 'params': {'selector': '.company-selector'}},
            {'name': '进入模块', 'type': 'click_element', 'params': {'selector': '.module-item'}},
            {'name': '验证模块页面', 'type': 'verify_url', 'params': {'pattern': '*/module/*'}}
        ])
        
        # CRM系统模板
        self.register_template('crm_system', [
            {'name': '登录', 'type': 'login'},
            {'name': '选择组织', 'type': 'select_option', 'params': {'selector': '.org-selector'}},
            {'name': '选择销售管道', 'type': 'click_element', 'params': {'selector': '.pipeline-item'}},
            {'name': '验证管道页面', 'type': 'verify_element', 'params': {'selector': '.pipeline-dashboard'}}
        ])
        
        # API服务模板
        self.register_template('api_service', [
            {'name': 'API登录', 'type': 'api_login'},
            {'name': '设置上下文', 'type': 'api_set_context'},
            {'name': '验证权限', 'type': 'verify_api_response', 'params': {'endpoint': '/api/user/permissions'}}
        ])
        
        logger.debug("内置模板注册完成")
    
    def register_step(self, step_type: str, step_func: Callable):
        """注册步骤函数"""
        self.step_registry[step_type] = step_func
        logger.debug(f"步骤已注册: {step_type}")
    
    def register_template(self, template_name: str, template_steps: List[Dict[str, Any]]):
        """注册工作流模板"""
        self.template_registry[template_name] = template_steps
        logger.debug(f"模板已注册: {template_name}")
    
    def load_workflow_from_config(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """从配置文件加载工作流定义"""
        workflow_config_path = self.workflow_config.get('config_path', 'config/workflows.yaml')
        
        try:
            config_file = Path(workflow_config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.suffix.lower() == '.yaml':
                        workflows = yaml.safe_load(f)
                    else:
                        workflows = json.load(f)
                
                return workflows.get('workflows', {}).get(workflow_name)
        except Exception as e:
            logger.error(f"加载工作流配置失败: {e}")
        
        return None
    
    def create_workflow(self, workflow_name: str, client_type: str, client=None, **kwargs) -> Optional[StepChain]:
        """创建工作流实例"""
        # 1. 尝试从配置文件加载
        workflow_def = self.load_workflow_from_config(workflow_name)
        
        if workflow_def:
            return self._create_workflow_from_config(workflow_name, workflow_def, client_type, client, **kwargs)
        
        # 2. 尝试从模板创建
        if workflow_name in self.template_registry:
            return self._create_workflow_from_template(workflow_name, client_type, client, **kwargs)
        
        # 3. 尝试加载插件工作流
        plugin_workflow = self._load_plugin_workflow(workflow_name, client_type, client, **kwargs)
        if plugin_workflow:
            return plugin_workflow
        
        logger.error(f"未找到工作流定义: {workflow_name}")
        return None
    
    def _create_workflow_from_config(self, workflow_name: str, workflow_def: Dict[str, Any], 
                                   client_type: str, client=None, **kwargs) -> StepChain:
        """从配置创建工作流"""
        logger.info(f"从配置创建工作流: {workflow_name}")
        
        chain = StepChain(workflow_name, client_type, client)
        
        # 处理全局参数
        global_params = workflow_def.get('global_params', {})
        global_params.update(kwargs)
        
        # 添加步骤
        for step_def in workflow_def.get('steps', []):
            step_name = step_def['name']
            step_type = step_def['type']
            step_params = step_def.get('params', {})
            
            # 合并参数
            merged_params = {**global_params, **step_params}
            
            # 参数替换
            merged_params = self._replace_variables(merged_params, global_params)
            
            # 获取步骤函数
            step_func = self.step_registry.get(step_type)
            if not step_func:
                logger.error(f"未找到步骤类型: {step_type}")
                continue
            
            # 添加到步骤链
            cache_key = step_def.get('cache_key', f"{step_type}_{step_name}")
            skip_if_cached = step_def.get('skip_if_cached', True)
            
            chain.add_step(
                step_name=step_name,
                step_func=step_func,
                cache_key=cache_key,
                skip_if_cached=skip_if_cached,
                **merged_params
            )
        
        return chain
    
    def _create_workflow_from_template(self, template_name: str, client_type: str, 
                                     client=None, **kwargs) -> StepChain:
        """从模板创建工作流"""
        logger.info(f"从模板创建工作流: {template_name}")
        
        template_steps = self.template_registry[template_name]
        chain = StepChain(template_name, client_type, client)
        
        for step_def in template_steps:
            step_name = step_def['name']
            step_type = step_def['type']
            step_params = step_def.get('params', {})
            
            # 合并参数
            merged_params = {**step_params, **kwargs}
            
            # 获取步骤函数
            step_func = self.step_registry.get(step_type)
            if not step_func:
                logger.error(f"未找到步骤类型: {step_type}")
                continue
            
            # 添加到步骤链
            cache_key = f"{template_name}_{step_type}_{step_name}"
            
            chain.add_step(
                step_name=step_name,
                step_func=step_func,
                cache_key=cache_key,
                skip_if_cached=True,
                **merged_params
            )
        
        return chain
    
    def _load_plugin_workflow(self, workflow_name: str, client_type: str, 
                            client=None, **kwargs) -> Optional[StepChain]:
        """加载插件工作流"""
        try:
            # 尝试导入插件模块
            plugin_module_path = f"plugins.workflows.{workflow_name}"
            plugin_module = importlib.import_module(plugin_module_path)
            
            # 查找工作流创建函数
            create_func_name = f"create_{workflow_name}_workflow"
            if hasattr(plugin_module, create_func_name):
                create_func = getattr(plugin_module, create_func_name)
                logger.info(f"从插件创建工作流: {workflow_name}")
                return create_func(client_type, client, **kwargs)
        
        except ImportError:
            logger.debug(f"未找到插件工作流: {workflow_name}")
        except Exception as e:
            logger.error(f"加载插件工作流失败: {workflow_name} - {e}")
        
        return None
    
    def _replace_variables(self, params: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """替换参数中的变量"""
        result = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                result[key] = variables.get(var_name, value)
            elif isinstance(value, dict):
                result[key] = self._replace_variables(value, variables)
            else:
                result[key] = value
        
        return result
    
    def execute_workflow(self, workflow_name: str, client_type: str, client=None, 
                        force_refresh: bool = False, **kwargs) -> bool:
        """执行工作流"""
        workflow = self.create_workflow(workflow_name, client_type, client, **kwargs)
        
        if not workflow:
            return False
        
        return workflow.execute(force_refresh)
    
    def get_available_workflows(self) -> Dict[str, List[str]]:
        """获取可用的工作流列表"""
        result = {
            'templates': list(self.template_registry.keys()),
            'configs': [],
            'plugins': []
        }
        
        # 扫描配置文件中的工作流
        workflow_config_path = self.workflow_config.get('config_path', 'config/workflows.yaml')
        try:
            config_file = Path(workflow_config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.suffix.lower() == '.yaml':
                        workflows = yaml.safe_load(f)
                    else:
                        workflows = json.load(f)
                
                result['configs'] = list(workflows.get('workflows', {}).keys())
        except Exception:
            pass
        
        # 扫描插件目录
        try:
            plugins_dir = Path('plugins/workflows')
            if plugins_dir.exists():
                for plugin_file in plugins_dir.glob('*.py'):
                    if plugin_file.name != '__init__.py':
                        result['plugins'].append(plugin_file.stem)
        except Exception:
            pass
        
        return result

    # ============ 内置步骤实现 ============

    def _builtin_login_step(self, client=None, context=None, username=None, password=None, **kwargs):
        """内置登录步骤"""
        try:
            from common.auth.global_login import GlobalLoginManager

            if not client:
                logger.error("客户端未初始化")
                return False

            login_manager = GlobalLoginManager('web', client)
            success = login_manager.login(username, password)

            if success:
                context['logged_in'] = True
                logger.info("登录步骤执行成功")
                return True
            else:
                logger.error("登录步骤执行失败")
                return False

        except Exception as e:
            logger.error(f"登录步骤异常: {e}")
            return False

    def _builtin_api_login_step(self, client=None, context=None, username=None, password=None, **kwargs):
        """内置API登录步骤"""
        try:
            from common.auth.global_login import GlobalLoginManager

            if not client:
                logger.error("API客户端未初始化")
                return False

            login_manager = GlobalLoginManager('api', client)
            success = login_manager.login(username, password)

            if success:
                context['api_logged_in'] = True
                context['api_token'] = getattr(login_manager.get_manager(), 'token', None)
                logger.info("API登录步骤执行成功")
                return True
            else:
                logger.error("API登录步骤执行失败")
                return False

        except Exception as e:
            logger.error(f"API登录步骤异常: {e}")
            return False

    def _builtin_navigate_step(self, client=None, context=None, target=None, **kwargs):
        """内置导航步骤"""
        try:
            if not client or not hasattr(client, 'page'):
                logger.error("Web客户端未初始化")
                return False

            page = client.page
            page.goto(target)
            page.wait_for_load_state('networkidle')

            context['current_url'] = page.url
            logger.info(f"导航步骤执行成功: {target}")
            return True

        except Exception as e:
            logger.error(f"导航步骤异常: {e}")
            return False

    def _builtin_select_option_step(self, client=None, context=None, selector=None, value=None, **kwargs):
        """内置选择选项步骤"""
        try:
            if not client or not hasattr(client, 'page'):
                logger.error("Web客户端未初始化")
                return False

            page = client.page

            # 等待元素可见
            page.wait_for_selector(selector, timeout=10000)

            # 选择选项
            if value:
                page.select_option(selector, value)
            else:
                page.click(selector)

            context[f'selected_{selector}'] = value
            logger.info(f"选择选项步骤执行成功: {selector} = {value}")
            return True

        except Exception as e:
            logger.error(f"选择选项步骤异常: {e}")
            return False

    def _builtin_click_element_step(self, client=None, context=None, selector=None, **kwargs):
        """内置点击元素步骤"""
        try:
            if not client or not hasattr(client, 'page'):
                logger.error("Web客户端未初始化")
                return False

            page = client.page
            page.wait_for_selector(selector, timeout=10000)
            page.click(selector)

            context[f'clicked_{selector}'] = True
            logger.info(f"点击元素步骤执行成功: {selector}")
            return True

        except Exception as e:
            logger.error(f"点击元素步骤异常: {e}")
            return False
