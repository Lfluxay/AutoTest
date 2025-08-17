"""
工作流工厂 - 统一的工作流创建和管理入口
"""
from typing import Dict, Any, Optional
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from .universal_workflow import universal_workflow_manager


class WorkflowFactory:
    """工作流工厂 - 根据配置选择合适的工作流创建方式"""
    
    def __init__(self):
        self.config = get_merged_config()
        self.workflow_config = self.config.get('universal_workflow', {})
        self.strategy_config = self.workflow_config.get('workflow_strategy', {})
        
        # 默认策略
        self.default_strategy = self.strategy_config.get('default_strategy', 'config_driven')
        self.strategy_priority = self.strategy_config.get('strategy_priority', [
            'config_driven', 'template_based', 'plugin_based'
        ])
        
        logger.info(f"工作流工厂初始化完成，默认策略: {self.default_strategy}")
    
    def create_workflow(self, workflow_name: str, client_type: str, client=None, 
                       strategy: str = None, **kwargs):
        """
        创建工作流
        
        Args:
            workflow_name: 工作流名称
            client_type: 客户端类型 ('web' 或 'api')
            client: 客户端实例
            strategy: 指定使用的策略，为None时使用默认策略
            **kwargs: 工作流参数
            
        Returns:
            工作流实例或None
        """
        # 确定使用的策略
        if strategy:
            strategies = [strategy]
        else:
            strategies = self.strategy_priority
        
        # 按优先级尝试不同策略
        for strategy_name in strategies:
            workflow = self._try_create_with_strategy(
                workflow_name, client_type, client, strategy_name, **kwargs
            )
            
            if workflow:
                logger.info(f"使用策略 {strategy_name} 创建工作流成功: {workflow_name}")
                return workflow
        
        logger.error(f"所有策略都无法创建工作流: {workflow_name}")
        return None
    
    def _try_create_with_strategy(self, workflow_name: str, client_type: str, 
                                client, strategy: str, **kwargs):
        """尝试使用指定策略创建工作流"""
        try:
            if strategy == 'config_driven':
                return self._create_config_driven_workflow(
                    workflow_name, client_type, client, **kwargs
                )
            elif strategy == 'template_based':
                return self._create_template_based_workflow(
                    workflow_name, client_type, client, **kwargs
                )
            elif strategy == 'plugin_based':
                return self._create_plugin_based_workflow(
                    workflow_name, client_type, client, **kwargs
                )
            else:
                logger.warning(f"未知的工作流策略: {strategy}")
                return None
                
        except Exception as e:
            logger.debug(f"策略 {strategy} 创建工作流失败: {e}")
            return None
    
    def _create_config_driven_workflow(self, workflow_name: str, client_type: str, 
                                     client, **kwargs):
        """创建配置驱动的工作流"""
        # 尝试从配置文件加载
        workflow_def = universal_workflow_manager.load_workflow_from_config(workflow_name)
        
        if workflow_def:
            return universal_workflow_manager._create_workflow_from_config(
                workflow_name, workflow_def, client_type, client, **kwargs
            )
        
        return None
    
    def _create_template_based_workflow(self, workflow_name: str, client_type: str, 
                                      client, **kwargs):
        """创建模板驱动的工作流"""
        # 检查是否有对应的模板
        if workflow_name in universal_workflow_manager.template_registry:
            return universal_workflow_manager._create_workflow_from_template(
                workflow_name, client_type, client, **kwargs
            )
        
        # 尝试智能匹配模板
        matched_template = self._match_template_by_keywords(workflow_name)
        if matched_template:
            logger.info(f"智能匹配模板: {workflow_name} -> {matched_template}")
            return universal_workflow_manager._create_workflow_from_template(
                matched_template, client_type, client, **kwargs
            )
        
        return None
    
    def _create_plugin_based_workflow(self, workflow_name: str, client_type: str, 
                                    client, **kwargs):
        """创建插件驱动的工作流"""
        return universal_workflow_manager._load_plugin_workflow(
            workflow_name, client_type, client, **kwargs
        )
    
    def _match_template_by_keywords(self, workflow_name: str) -> Optional[str]:
        """根据关键词智能匹配模板"""
        keyword_mapping = {
            'saas': 'saas_platform',
            'tenant': 'saas_platform',
            'erp': 'erp_system',
            'company': 'erp_system',
            'crm': 'crm_system',
            'customer': 'crm_system',
            'api': 'api_service',
            'service': 'api_service'
        }
        
        workflow_lower = workflow_name.lower()
        
        for keyword, template in keyword_mapping.items():
            if keyword in workflow_lower:
                if template in universal_workflow_manager.template_registry:
                    return template
        
        return None
    
    def execute_workflow(self, workflow_name: str, client_type: str, client=None,
                        strategy: str = None, force_refresh: bool = False, **kwargs) -> bool:
        """
        执行工作流
        
        Args:
            workflow_name: 工作流名称
            client_type: 客户端类型
            client: 客户端实例
            strategy: 指定策略
            force_refresh: 是否强制刷新
            **kwargs: 工作流参数
            
        Returns:
            执行是否成功
        """
        workflow = self.create_workflow(workflow_name, client_type, client, strategy, **kwargs)
        
        if not workflow:
            return False
        
        return workflow.execute(force_refresh)
    
    def get_available_workflows(self) -> Dict[str, Any]:
        """获取所有可用的工作流"""
        return {
            'strategies': self.strategy_priority,
            'default_strategy': self.default_strategy,
            'workflows': universal_workflow_manager.get_available_workflows()
        }
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """获取工作流信息"""
        info = {
            'name': workflow_name,
            'available_strategies': [],
            'recommended_strategy': None,
            'description': None
        }
        
        # 检查各种策略的可用性
        for strategy in self.strategy_priority:
            if self._try_create_with_strategy(workflow_name, 'web', None, strategy):
                info['available_strategies'].append(strategy)
        
        # 推荐策略
        if info['available_strategies']:
            info['recommended_strategy'] = info['available_strategies'][0]
        
        # 获取描述信息
        workflow_def = universal_workflow_manager.load_workflow_from_config(workflow_name)
        if workflow_def:
            info['description'] = workflow_def.get('description')
        
        return info
    
    def validate_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """验证工作流配置"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # 尝试创建工作流进行验证
            workflow = self.create_workflow(workflow_name, 'web', None)
            
            if not workflow:
                validation_result['valid'] = False
                validation_result['errors'].append(f"无法创建工作流: {workflow_name}")
            else:
                # 检查步骤配置
                for step in workflow.steps:
                    step_name = step['name']
                    step_func = step['func']
                    
                    if not step_func:
                        validation_result['errors'].append(f"步骤 {step_name} 缺少执行函数")
                    
                    if not step.get('cache_key'):
                        validation_result['warnings'].append(f"步骤 {step_name} 未设置缓存键")
                
                # 性能建议
                if len(workflow.steps) > 10:
                    validation_result['suggestions'].append("工作流步骤较多，建议考虑拆分")
                
                if all(step.get('skip_if_cached', True) for step in workflow.steps):
                    validation_result['suggestions'].append("所有步骤都启用了缓存，可能影响数据实时性")
        
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"验证异常: {e}")
        
        return validation_result


# 全局工厂实例
workflow_factory = WorkflowFactory()
