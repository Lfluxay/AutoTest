"""
工作流缓存模块 - 管理工作流执行状态和Token缓存
"""
from typing import Dict, Any, Optional
import time
import json
from utils.logging.logger import logger
from utils.config.parser import get_merged_config


class WorkflowCache:
    """工作流缓存管理器"""
    
    # 类级别的缓存存储
    _workflow_cache = {}  # 工作流状态缓存
    _step_cache = {}      # 步骤结果缓存
    _token_cache = {}     # Token缓存
    _session_cache = {}   # 会话缓存
    
    def __init__(self, workflow_name: str):
        """
        初始化工作流缓存
        
        Args:
            workflow_name: 工作流名称
        """
        self.workflow_name = workflow_name
        self.config = get_merged_config()
        self.cache_config = self.config.get('workflow', {}).get('cache', {})
        
    def get_cache_timeout(self) -> int:
        """获取缓存超时时间（秒）"""
        return self.cache_config.get('timeout', 3600)  # 默认1小时
    
    def is_cache_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self.cache_config.get('enabled', True)
    
    # ============ 工作流状态缓存 ============
    
    def save_workflow_state(self, client_type: str, state_data: Dict[str, Any]):
        """
        保存工作流状态
        
        Args:
            client_type: 客户端类型
            state_data: 状态数据
        """
        if not self.is_cache_enabled():
            return
        
        cache_key = f"{self.workflow_name}_{client_type}"
        state_data['cached_at'] = time.time()
        
        self._workflow_cache[cache_key] = state_data
        logger.debug(f"工作流状态已缓存: {cache_key}")
    
    def get_workflow_state(self, client_type: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        
        Args:
            client_type: 客户端类型
            
        Returns:
            状态数据或None
        """
        if not self.is_cache_enabled():
            return None
        
        cache_key = f"{self.workflow_name}_{client_type}"
        state_data = self._workflow_cache.get(cache_key)
        
        if state_data and self._is_cache_valid(state_data):
            logger.debug(f"获取到有效的工作流状态: {cache_key}")
            return state_data
        
        if state_data:
            logger.debug(f"工作流状态已过期: {cache_key}")
            self._workflow_cache.pop(cache_key, None)
        
        return None
    
    # ============ 步骤结果缓存 ============
    
    def cache_step_result(self, step_key: str, client_type: str, result_data: Dict[str, Any]):
        """
        缓存步骤执行结果
        
        Args:
            step_key: 步骤键
            client_type: 客户端类型
            result_data: 结果数据
        """
        if not self.is_cache_enabled():
            return
        
        cache_key = f"{self.workflow_name}_{step_key}_{client_type}"
        result_data['cached_at'] = time.time()
        
        self._step_cache[cache_key] = result_data
        logger.debug(f"步骤结果已缓存: {cache_key}")
    
    def get_step_result(self, step_key: str, client_type: str) -> Optional[Dict[str, Any]]:
        """
        获取步骤执行结果
        
        Args:
            step_key: 步骤键
            client_type: 客户端类型
            
        Returns:
            结果数据或None
        """
        if not self.is_cache_enabled():
            return None
        
        cache_key = f"{self.workflow_name}_{step_key}_{client_type}"
        result_data = self._step_cache.get(cache_key)
        
        if result_data and self._is_cache_valid(result_data):
            return result_data
        
        if result_data:
            self._step_cache.pop(cache_key, None)
        
        return None
    
    def is_step_cached(self, step_key: str, client_type: str) -> bool:
        """
        检查步骤是否已缓存
        
        Args:
            step_key: 步骤键
            client_type: 客户端类型
            
        Returns:
            是否已缓存
        """
        return self.get_step_result(step_key, client_type) is not None
    
    # ============ Token缓存 ============
    
    def cache_token(self, client_type: str, token_data: Dict[str, Any]):
        """
        缓存Token信息
        
        Args:
            client_type: 客户端类型
            token_data: Token数据 (包含token, expires_at等)
        """
        if not self.is_cache_enabled():
            return
        
        cache_key = f"{self.workflow_name}_{client_type}_token"
        token_data['cached_at'] = time.time()
        
        self._token_cache[cache_key] = token_data
        logger.debug(f"Token已缓存: {cache_key}")
    
    def get_cached_token(self, client_type: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的Token
        
        Args:
            client_type: 客户端类型
            
        Returns:
            Token数据或None
        """
        if not self.is_cache_enabled():
            return None
        
        cache_key = f"{self.workflow_name}_{client_type}_token"
        token_data = self._token_cache.get(cache_key)
        
        if token_data and self._is_token_valid(token_data):
            return token_data
        
        if token_data:
            logger.debug(f"Token已过期: {cache_key}")
            self._token_cache.pop(cache_key, None)
        
        return None
    
    def _is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """检查Token是否有效"""
        # 检查缓存时间
        if not self._is_cache_valid(token_data):
            return False
        
        # 检查Token过期时间
        expires_at = token_data.get('expires_at')
        if expires_at and time.time() > expires_at:
            logger.debug("Token已过期")
            return False
        
        return True
    
    # ============ 会话缓存 ============
    
    def cache_session(self, client_type: str, session_data: Dict[str, Any]):
        """
        缓存会话信息
        
        Args:
            client_type: 客户端类型
            session_data: 会话数据
        """
        if not self.is_cache_enabled():
            return
        
        cache_key = f"{self.workflow_name}_{client_type}_session"
        session_data['cached_at'] = time.time()
        
        # 特殊处理不同类型的会话数据
        if client_type == 'web':
            # Web端缓存cookies、页面状态等
            session_data.setdefault('cookies', [])
            session_data.setdefault('current_url', '')
            session_data.setdefault('page_state', {})
        elif client_type == 'api':
            # API端缓存headers、token等
            session_data.setdefault('headers', {})
            session_data.setdefault('token', '')
        
        self._session_cache[cache_key] = session_data
        logger.debug(f"会话已缓存: {cache_key}")
    
    def get_cached_session(self, client_type: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的会话
        
        Args:
            client_type: 客户端类型
            
        Returns:
            会话数据或None
        """
        if not self.is_cache_enabled():
            return None
        
        cache_key = f"{self.workflow_name}_{client_type}_session"
        session_data = self._session_cache.get(cache_key)
        
        if session_data and self._is_cache_valid(session_data):
            return session_data
        
        if session_data:
            self._session_cache.pop(cache_key, None)
        
        return None
    
    # ============ 缓存管理 ============
    
    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        cached_at = cache_data.get('cached_at', 0)
        current_time = time.time()
        timeout = self.get_cache_timeout()
        
        return (current_time - cached_at) <= timeout
    
    def clear_cache(self, client_type: str = None):
        """
        清除缓存
        
        Args:
            client_type: 客户端类型，为None时清除所有类型
        """
        prefix = f"{self.workflow_name}_"
        if client_type:
            prefix += f"{client_type}_"
        
        # 清除工作流状态缓存
        keys_to_remove = [k for k in self._workflow_cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            self._workflow_cache.pop(key, None)
        
        # 清除步骤缓存
        keys_to_remove = [k for k in self._step_cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            self._step_cache.pop(key, None)
        
        # 清除Token缓存
        keys_to_remove = [k for k in self._token_cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            self._token_cache.pop(key, None)
        
        # 清除会话缓存
        keys_to_remove = [k for k in self._session_cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            self._session_cache.pop(key, None)
        
        logger.info(f"缓存已清除: {prefix}")
    
    def clear_all_cache(self):
        """清除当前工作流的所有缓存"""
        self.clear_cache()
    
    @classmethod
    def clear_global_cache(cls):
        """清除全局缓存"""
        cls._workflow_cache.clear()
        cls._step_cache.clear()
        cls._token_cache.clear()
        cls._session_cache.clear()
        logger.info("全局缓存已清除")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        prefix = f"{self.workflow_name}_"
        
        workflow_count = len([k for k in self._workflow_cache.keys() if k.startswith(prefix)])
        step_count = len([k for k in self._step_cache.keys() if k.startswith(prefix)])
        token_count = len([k for k in self._token_cache.keys() if k.startswith(prefix)])
        session_count = len([k for k in self._session_cache.keys() if k.startswith(prefix)])
        
        return {
            'workflow_name': self.workflow_name,
            'workflow_states': workflow_count,
            'cached_steps': step_count,
            'cached_tokens': token_count,
            'cached_sessions': session_count,
            'total_cache_items': workflow_count + step_count + token_count + session_count
        }
