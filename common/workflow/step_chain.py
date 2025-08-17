"""
步骤链模块 - 提供可配置的步骤执行链
"""
from typing import Dict, Any, List, Callable, Optional
import time
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from .workflow_cache import WorkflowCache


class StepChain:
    """步骤链 - 管理一系列有序的执行步骤"""
    
    def __init__(self, name: str, client_type: str, client=None):
        """
        初始化步骤链
        
        Args:
            name: 步骤链名称
            client_type: 客户端类型 ('web' 或 'api')
            client: 客户端实例
        """
        self.name = name
        self.client_type = client_type
        self.client = client
        self.steps = []
        self.current_step_index = 0
        self.execution_context = {}
        self.cache = WorkflowCache(name)
        
        logger.info(f"步骤链初始化: {name} ({client_type})")
    
    def add_step(self, step_name: str, step_func: Callable, 
                 cache_key: str = None, skip_if_cached: bool = True, **kwargs):
        """
        添加步骤
        
        Args:
            step_name: 步骤名称
            step_func: 步骤执行函数
            cache_key: 缓存键，用于判断是否可以跳过
            skip_if_cached: 如果已缓存是否跳过
            **kwargs: 步骤参数
        """
        step = {
            'name': step_name,
            'func': step_func,
            'cache_key': cache_key or step_name,
            'skip_if_cached': skip_if_cached,
            'kwargs': kwargs,
            'executed': False,
            'result': None,
            'execution_time': 0
        }
        self.steps.append(step)
        logger.debug(f"添加步骤: {step_name}")
    
    def execute(self, force_refresh: bool = False) -> bool:
        """
        执行步骤链
        
        Args:
            force_refresh: 是否强制刷新，忽略缓存
            
        Returns:
            执行是否成功
        """
        start_time = time.time()
        logger.info(f"开始执行步骤链: {self.name}")
        
        try:
            # 检查是否可以从缓存恢复
            if not force_refresh:
                cached_state = self.cache.get_workflow_state(self.client_type)
                if cached_state and self._is_cache_valid(cached_state):
                    logger.info(f"从缓存恢复工作流状态: {self.name}")
                    self._restore_from_cache(cached_state)
                    return True
            
            # 执行所有步骤
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                
                if not self._execute_step(step, force_refresh):
                    logger.error(f"步骤执行失败: {step['name']}")
                    return False
            
            # 保存最终状态到缓存
            self._save_to_cache()
            
            total_time = time.time() - start_time
            logger.info(f"步骤链执行完成: {self.name} (耗时: {total_time:.2f}s)")
            return True
            
        except Exception as e:
            logger.error(f"步骤链执行异常: {self.name} - {e}")
            return False
    
    def _execute_step(self, step: Dict[str, Any], force_refresh: bool = False) -> bool:
        """执行单个步骤"""
        step_start_time = time.time()
        step_name = step['name']
        
        logger.info(f"执行步骤: {step_name}")
        
        # 检查是否可以跳过（基于缓存）
        if not force_refresh and step['skip_if_cached']:
            if self.cache.is_step_cached(step['cache_key'], self.client_type):
                logger.info(f"步骤已缓存，跳过执行: {step_name}")
                step['executed'] = True
                step['result'] = True
                return True
        
        try:
            # 准备步骤参数
            step_kwargs = step['kwargs'].copy()
            step_kwargs.update({
                'client': self.client,
                'context': self.execution_context
            })
            
            # 执行步骤
            result = step['func'](**step_kwargs)
            
            # 记录执行结果
            step['executed'] = True
            step['result'] = result
            step['execution_time'] = time.time() - step_start_time
            
            if result:
                logger.info(f"步骤执行成功: {step_name} (耗时: {step['execution_time']:.2f}s)")
                # 缓存成功的步骤
                self.cache.cache_step_result(step['cache_key'], self.client_type, {
                    'step_name': step_name,
                    'result': result,
                    'timestamp': time.time(),
                    'context': self.execution_context.copy()
                })
                return True
            else:
                logger.error(f"步骤执行失败: {step_name}")
                return False
                
        except Exception as e:
            logger.error(f"步骤执行异常: {step_name} - {e}")
            step['executed'] = True
            step['result'] = False
            step['execution_time'] = time.time() - step_start_time
            return False
    
    def _is_cache_valid(self, cached_state: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        cache_time = cached_state.get('timestamp', 0)
        current_time = time.time()
        cache_timeout = self.cache.get_cache_timeout()
        
        if current_time - cache_time > cache_timeout:
            logger.debug("缓存已过期")
            return False
        
        # 检查关键状态是否匹配
        required_steps = [step['cache_key'] for step in self.steps]
        cached_steps = cached_state.get('completed_steps', [])
        
        return all(step in cached_steps for step in required_steps)
    
    def _restore_from_cache(self, cached_state: Dict[str, Any]):
        """从缓存恢复状态"""
        self.execution_context.update(cached_state.get('context', {}))
        
        # 标记所有步骤为已执行
        for step in self.steps:
            step['executed'] = True
            step['result'] = True
        
        logger.info("工作流状态已从缓存恢复")
    
    def _save_to_cache(self):
        """保存当前状态到缓存"""
        workflow_state = {
            'workflow_name': self.name,
            'client_type': self.client_type,
            'completed_steps': [step['cache_key'] for step in self.steps if step['result']],
            'context': self.execution_context.copy(),
            'timestamp': time.time()
        }
        
        self.cache.save_workflow_state(self.client_type, workflow_state)
        logger.debug(f"工作流状态已保存到缓存: {self.name}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        total_time = sum(step.get('execution_time', 0) for step in self.steps)
        executed_steps = [step for step in self.steps if step['executed']]
        successful_steps = [step for step in executed_steps if step['result']]
        
        return {
            'workflow_name': self.name,
            'total_steps': len(self.steps),
            'executed_steps': len(executed_steps),
            'successful_steps': len(successful_steps),
            'total_execution_time': total_time,
            'success_rate': len(successful_steps) / len(self.steps) if self.steps else 0
        }


class WorkflowManager:
    """工作流管理器 - 管理多个工作流的执行和缓存"""
    
    _workflows = {}  # 类级别的工作流缓存
    
    @classmethod
    def register_workflow(cls, name: str, workflow_factory: Callable) -> None:
        """注册工作流工厂函数"""
        cls._workflows[name] = workflow_factory
        logger.info(f"工作流已注册: {name}")
    
    @classmethod
    def execute_workflow(cls, name: str, client_type: str, client=None, 
                        force_refresh: bool = False, **kwargs) -> bool:
        """
        执行指定的工作流
        
        Args:
            name: 工作流名称
            client_type: 客户端类型
            client: 客户端实例
            force_refresh: 是否强制刷新
            **kwargs: 工作流参数
            
        Returns:
            执行是否成功
        """
        if name not in cls._workflows:
            logger.error(f"未找到工作流: {name}")
            return False
        
        try:
            # 创建工作流实例
            workflow_factory = cls._workflows[name]
            workflow = workflow_factory(client_type, client, **kwargs)
            
            # 执行工作流
            return workflow.execute(force_refresh)
            
        except Exception as e:
            logger.error(f"工作流执行异常: {name} - {e}")
            return False
    
    @classmethod
    def get_workflow_status(cls, name: str, client_type: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        cache = WorkflowCache(name)
        return cache.get_workflow_state(client_type)
    
    @classmethod
    def clear_workflow_cache(cls, name: str = None, client_type: str = None):
        """清除工作流缓存"""
        if name:
            cache = WorkflowCache(name)
            if client_type:
                cache.clear_cache(client_type)
            else:
                cache.clear_all_cache()
        else:
            # 清除所有工作流缓存
            WorkflowCache.clear_global_cache()
        
        logger.info(f"工作流缓存已清除: {name or 'all'}")
