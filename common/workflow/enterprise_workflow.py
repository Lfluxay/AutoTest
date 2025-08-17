"""
企业工作流 - 实现"登录-选择企业-进入工作台-选择模块-进入首页"的完整流程
"""
from typing import Dict, Any, Optional
import time
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from .step_chain import StepChain
from .workflow_cache import WorkflowCache
from common.auth.global_login import GlobalLoginManager


class EnterpriseWorkflow:
    """企业工作流管理器"""
    
    def __init__(self, client_type: str, client=None, **kwargs):
        """
        初始化企业工作流
        
        Args:
            client_type: 客户端类型 ('web' 或 'api')
            client: 客户端实例
            **kwargs: 工作流参数
        """
        self.client_type = client_type
        self.client = client
        self.config = get_merged_config()
        self.workflow_config = self.config.get('workflow', {}).get('enterprise', {})
        
        # 工作流参数
        self.enterprise_id = kwargs.get('enterprise_id', self.workflow_config.get('default_enterprise_id'))
        self.module_name = kwargs.get('module_name', self.workflow_config.get('default_module'))
        self.target_page = kwargs.get('target_page', self.workflow_config.get('default_target_page', '/home'))
        
        # 创建步骤链
        self.step_chain = StepChain('enterprise_workflow', client_type, client)
        self.cache = WorkflowCache('enterprise_workflow')
        
        # 初始化步骤链
        self._setup_workflow_steps()
        
        logger.info(f"企业工作流初始化完成: {client_type}")
    
    def _setup_workflow_steps(self):
        """设置工作流步骤"""
        if self.client_type == 'web':
            self._setup_web_workflow()
        elif self.client_type == 'api':
            self._setup_api_workflow()
    
    def _setup_web_workflow(self):
        """设置Web工作流步骤"""
        # 步骤1: 登录
        self.step_chain.add_step(
            step_name="登录",
            step_func=self._web_login_step,
            cache_key="web_login",
            skip_if_cached=True
        )
        
        # 步骤2: 选择企业
        self.step_chain.add_step(
            step_name="选择企业",
            step_func=self._web_select_enterprise_step,
            cache_key=f"web_enterprise_{self.enterprise_id}",
            skip_if_cached=True,
            enterprise_id=self.enterprise_id
        )
        
        # 步骤3: 进入工作台
        self.step_chain.add_step(
            step_name="进入工作台",
            step_func=self._web_enter_workspace_step,
            cache_key="web_workspace",
            skip_if_cached=True
        )
        
        # 步骤4: 选择模块
        self.step_chain.add_step(
            step_name="选择模块",
            step_func=self._web_select_module_step,
            cache_key=f"web_module_{self.module_name}",
            skip_if_cached=True,
            module_name=self.module_name
        )
        
        # 步骤5: 进入首页
        self.step_chain.add_step(
            step_name="进入首页",
            step_func=self._web_enter_homepage_step,
            cache_key=f"web_homepage_{self.target_page}",
            skip_if_cached=False,  # 首页每次都要确认
            target_page=self.target_page
        )
    
    def _setup_api_workflow(self):
        """设置API工作流步骤"""
        # 步骤1: 登录获取Token
        self.step_chain.add_step(
            step_name="API登录",
            step_func=self._api_login_step,
            cache_key="api_login",
            skip_if_cached=True
        )
        
        # 步骤2: 选择企业上下文
        self.step_chain.add_step(
            step_name="设置企业上下文",
            step_func=self._api_set_enterprise_context_step,
            cache_key=f"api_enterprise_{self.enterprise_id}",
            skip_if_cached=True,
            enterprise_id=self.enterprise_id
        )
        
        # 步骤3: 设置模块权限
        self.step_chain.add_step(
            step_name="设置模块权限",
            step_func=self._api_set_module_permission_step,
            cache_key=f"api_module_{self.module_name}",
            skip_if_cached=True,
            module_name=self.module_name
        )
        
        # 步骤4: 初始化API端点
        self.step_chain.add_step(
            step_name="初始化API端点",
            step_func=self._api_init_endpoints_step,
            cache_key="api_endpoints",
            skip_if_cached=False  # 每次都要确认端点可用
        )
    
    # ============ Web工作流步骤实现 ============
    
    def _web_login_step(self, client=None, context=None, **kwargs) -> bool:
        """Web登录步骤"""
        try:
            # 检查是否已有有效的登录状态
            cached_session = self.cache.get_cached_session('web')
            if cached_session and self._verify_web_login_state(cached_session):
                logger.info("Web登录状态有效，跳过登录")
                context['login_verified'] = True
                return True
            
            # 执行登录
            login_manager = GlobalLoginManager('web', client)
            success = login_manager.login()
            
            if success:
                # 缓存登录状态
                session_data = {
                    'login_time': time.time(),
                    'current_url': client.page.url if client and client.page else '',
                    'login_verified': True
                }
                self.cache.cache_session('web', session_data)
                context['login_verified'] = True
                
                logger.info("Web登录成功")
                return True
            else:
                logger.error("Web登录失败")
                return False
                
        except Exception as e:
            logger.error(f"Web登录步骤异常: {e}")
            return False
    
    def _web_select_enterprise_step(self, client=None, context=None, enterprise_id=None, **kwargs) -> bool:
        """Web选择企业步骤"""
        try:
            if not client or not client.page:
                logger.error("Web客户端未初始化")
                return False
            
            page = client.page
            
            # 检查是否已在正确的企业
            current_enterprise = self._get_current_enterprise(page)
            if current_enterprise == enterprise_id:
                logger.info(f"已在目标企业: {enterprise_id}")
                context['enterprise_id'] = enterprise_id
                return True
            
            # 查找企业选择器
            enterprise_selector = self.workflow_config.get('selectors', {}).get('enterprise_selector', '.enterprise-selector')
            
            if not page.is_visible(enterprise_selector):
                # 可能需要先点击企业切换按钮
                enterprise_switch_btn = self.workflow_config.get('selectors', {}).get('enterprise_switch_btn', '.enterprise-switch')
                if page.is_visible(enterprise_switch_btn):
                    page.click(enterprise_switch_btn)
                    page.wait_for_selector(enterprise_selector, timeout=5000)
            
            # 选择企业
            enterprise_option = f"{enterprise_selector} [data-enterprise-id='{enterprise_id}']"
            if page.is_visible(enterprise_option):
                page.click(enterprise_option)
                
                # 等待企业切换完成
                page.wait_for_load_state('networkidle')
                
                # 验证企业切换成功
                if self._get_current_enterprise(page) == enterprise_id:
                    context['enterprise_id'] = enterprise_id
                    logger.info(f"企业选择成功: {enterprise_id}")
                    return True
                else:
                    logger.error(f"企业选择失败: {enterprise_id}")
                    return False
            else:
                logger.error(f"未找到企业选项: {enterprise_id}")
                return False
                
        except Exception as e:
            logger.error(f"Web选择企业步骤异常: {e}")
            return False
    
    def _web_enter_workspace_step(self, client=None, context=None, **kwargs) -> bool:
        """Web进入工作台步骤"""
        try:
            if not client or not client.page:
                return False
            
            page = client.page
            workspace_url = self.workflow_config.get('urls', {}).get('workspace_url', '/workspace')
            
            # 检查是否已在工作台
            if workspace_url in page.url:
                logger.info("已在工作台页面")
                context['in_workspace'] = True
                return True
            
            # 导航到工作台
            page.goto(workspace_url)
            page.wait_for_load_state('networkidle')
            
            # 验证是否成功进入工作台
            workspace_indicator = self.workflow_config.get('selectors', {}).get('workspace_indicator', '.workspace-container')
            if page.is_visible(workspace_indicator):
                context['in_workspace'] = True
                logger.info("成功进入工作台")
                return True
            else:
                logger.error("进入工作台失败")
                return False
                
        except Exception as e:
            logger.error(f"Web进入工作台步骤异常: {e}")
            return False
    
    def _web_select_module_step(self, client=None, context=None, module_name=None, **kwargs) -> bool:
        """Web选择模块步骤"""
        try:
            if not client or not client.page:
                return False
            
            page = client.page
            
            # 查找模块选择器
            module_selector = f".module-item[data-module='{module_name}']"
            
            if page.is_visible(module_selector):
                page.click(module_selector)
                page.wait_for_load_state('networkidle')
                
                # 验证模块选择成功
                active_module = page.get_attribute('.module-item.active', 'data-module')
                if active_module == module_name:
                    context['selected_module'] = module_name
                    logger.info(f"模块选择成功: {module_name}")
                    return True
                else:
                    logger.error(f"模块选择失败: {module_name}")
                    return False
            else:
                logger.error(f"未找到模块: {module_name}")
                return False
                
        except Exception as e:
            logger.error(f"Web选择模块步骤异常: {e}")
            return False
    
    def _web_enter_homepage_step(self, client=None, context=None, target_page=None, **kwargs) -> bool:
        """Web进入首页步骤"""
        try:
            if not client or not client.page:
                return False
            
            page = client.page
            
            # 导航到目标页面
            page.goto(target_page)
            page.wait_for_load_state('networkidle')
            
            # 验证页面加载成功
            if target_page in page.url:
                context['current_page'] = target_page
                logger.info(f"成功进入目标页面: {target_page}")
                return True
            else:
                logger.error(f"进入目标页面失败: {target_page}")
                return False
                
        except Exception as e:
            logger.error(f"Web进入首页步骤异常: {e}")
            return False
    
    # ============ API工作流步骤实现 ============
    
    def _api_login_step(self, client=None, context=None, **kwargs) -> bool:
        """API登录步骤"""
        try:
            # 检查是否已有有效的Token
            cached_token = self.cache.get_cached_token('api')
            if cached_token:
                token = cached_token.get('token')
                if token and self._verify_api_token(client, token):
                    logger.info("API Token有效，跳过登录")
                    context['token'] = token
                    return True
            
            # 执行API登录
            login_manager = GlobalLoginManager('api', client)
            success = login_manager.login()
            
            if success:
                token = login_manager.get_manager().token
                if token:
                    # 缓存Token
                    token_data = {
                        'token': token,
                        'login_time': time.time(),
                        'expires_at': time.time() + 7200  # 假设2小时过期
                    }
                    self.cache.cache_token('api', token_data)
                    context['token'] = token
                    
                    logger.info("API登录成功")
                    return True
            
            logger.error("API登录失败")
            return False
            
        except Exception as e:
            logger.error(f"API登录步骤异常: {e}")
            return False
    
    def _api_set_enterprise_context_step(self, client=None, context=None, enterprise_id=None, **kwargs) -> bool:
        """API设置企业上下文步骤"""
        try:
            if not client:
                return False
            
            # 设置企业上下文
            response = client.post('/api/context/enterprise', json={
                'enterprise_id': enterprise_id
            })
            
            if response.status_code == 200:
                context['enterprise_context'] = enterprise_id
                logger.info(f"API企业上下文设置成功: {enterprise_id}")
                return True
            else:
                logger.error(f"API企业上下文设置失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"API设置企业上下文步骤异常: {e}")
            return False
    
    def _api_set_module_permission_step(self, client=None, context=None, module_name=None, **kwargs) -> bool:
        """API设置模块权限步骤"""
        try:
            if not client:
                return False
            
            # 设置模块权限
            response = client.post('/api/permissions/module', json={
                'module': module_name
            })
            
            if response.status_code == 200:
                context['module_permission'] = module_name
                logger.info(f"API模块权限设置成功: {module_name}")
                return True
            else:
                logger.error(f"API模块权限设置失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"API设置模块权限步骤异常: {e}")
            return False
    
    def _api_init_endpoints_step(self, client=None, context=None, **kwargs) -> bool:
        """API初始化端点步骤"""
        try:
            if not client:
                return False
            
            # 获取可用端点
            response = client.get('/api/endpoints')
            
            if response.status_code == 200:
                endpoints = response.json().get('data', {}).get('endpoints', [])
                context['available_endpoints'] = endpoints
                logger.info(f"API端点初始化成功，可用端点数: {len(endpoints)}")
                return True
            else:
                logger.error(f"API端点初始化失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"API初始化端点步骤异常: {e}")
            return False
    
    # ============ 辅助方法 ============
    
    def _verify_web_login_state(self, session_data: Dict[str, Any]) -> bool:
        """验证Web登录状态"""
        # 这里可以添加更复杂的验证逻辑
        return session_data.get('login_verified', False)
    
    def _verify_api_token(self, client, token: str) -> bool:
        """验证API Token"""
        try:
            if not client:
                return False
            
            # 设置Token并测试
            original_auth = client.session.headers.get('Authorization')
            client.session.headers['Authorization'] = f'Bearer {token}'
            
            response = client.get('/api/user/profile')
            
            # 恢复原始认证头
            if original_auth:
                client.session.headers['Authorization'] = original_auth
            else:
                client.session.headers.pop('Authorization', None)
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _get_current_enterprise(self, page) -> Optional[str]:
        """获取当前选中的企业ID"""
        try:
            enterprise_indicator = self.workflow_config.get('selectors', {}).get('current_enterprise', '.current-enterprise')
            if page.is_visible(enterprise_indicator):
                return page.get_attribute(enterprise_indicator, 'data-enterprise-id')
        except Exception:
            pass
        return None
    
    def execute(self, force_refresh: bool = False) -> bool:
        """执行企业工作流"""
        return self.step_chain.execute(force_refresh)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return self.step_chain.get_execution_summary()


# 注册企业工作流到工作流管理器
def create_enterprise_workflow(client_type: str, client=None, **kwargs) -> EnterpriseWorkflow:
    """企业工作流工厂函数"""
    return EnterpriseWorkflow(client_type, client, **kwargs)


# 自动注册
from .step_chain import WorkflowManager
WorkflowManager.register_workflow('enterprise', create_enterprise_workflow)
