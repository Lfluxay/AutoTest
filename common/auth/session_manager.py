"""
会话管理器 - 管理登录会话的复用和状态
"""
from typing import Dict, Any, Optional
from utils.logging.logger import logger
from utils.config.parser import get_merged_config


class SessionManager:
    """会话管理器 - 支持会话复用，避免重复登录"""
    
    _sessions = {}  # 类级别的会话缓存
    
    def __init__(self, session_key: str = "default"):
        """
        初始化会话管理器
        
        Args:
            session_key: 会话标识，用于区分不同的会话
        """
        self.session_key = session_key
        self.config = get_merged_config()
        
    def get_session(self, client_type: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            client_type: 客户端类型 ('web' 或 'api')
            
        Returns:
            会话信息字典或None
        """
        session_id = f"{self.session_key}_{client_type}"
        return self._sessions.get(session_id)
    
    def save_session(self, client_type: str, session_data: Dict[str, Any]):
        """
        保存会话信息
        
        Args:
            client_type: 客户端类型
            session_data: 会话数据
        """
        session_id = f"{self.session_key}_{client_type}"
        self._sessions[session_id] = session_data
        logger.debug(f"会话已保存: {session_id}")
    
    def clear_session(self, client_type: str = None):
        """
        清除会话信息
        
        Args:
            client_type: 客户端类型，为None时清除所有相关会话
        """
        if client_type:
            session_id = f"{self.session_key}_{client_type}"
            self._sessions.pop(session_id, None)
            logger.debug(f"会话已清除: {session_id}")
        else:
            # 清除所有相关会话
            keys_to_remove = [k for k in self._sessions.keys() if k.startswith(f"{self.session_key}_")]
            for key in keys_to_remove:
                self._sessions.pop(key, None)
            logger.debug(f"所有会话已清除: {self.session_key}")
    
    def is_session_valid(self, client_type: str) -> bool:
        """
        检查会话是否有效
        
        Args:
            client_type: 客户端类型
            
        Returns:
            会话是否有效
        """
        session = self.get_session(client_type)
        if not session:
            return False
        
        # 检查会话是否过期
        import time
        current_time = time.time()
        session_time = session.get('timestamp', 0)
        session_timeout = self.config.get('session', {}).get('timeout', 3600)  # 默认1小时
        
        if current_time - session_time > session_timeout:
            logger.debug(f"会话已过期: {client_type}")
            self.clear_session(client_type)
            return False
        
        return True
    
    def update_session_timestamp(self, client_type: str):
        """
        更新会话时间戳
        
        Args:
            client_type: 客户端类型
        """
        session = self.get_session(client_type)
        if session:
            import time
            session['timestamp'] = time.time()
            self.save_session(client_type, session)
    
    @classmethod
    def clear_all_sessions(cls):
        """清除所有会话"""
        cls._sessions.clear()
        logger.info("所有会话已清除")
    
    def create_session_data(self, client_type: str, login_manager, **extra_data) -> Dict[str, Any]:
        """
        创建会话数据
        
        Args:
            client_type: 客户端类型
            login_manager: 登录管理器实例
            **extra_data: 额外的会话数据
            
        Returns:
            会话数据字典
        """
        import time
        
        session_data = {
            'client_type': client_type,
            'timestamp': time.time(),
            'is_logged_in': getattr(login_manager, 'is_logged_in', False),
            **extra_data
        }
        
        # Web端特有数据
        if client_type == 'web':
            if hasattr(login_manager, 'browser_manager') and login_manager.browser_manager:
                session_data.update({
                    'current_url': getattr(login_manager.browser_manager.page, 'url', '') if login_manager.browser_manager.page else '',
                    'browser_type': getattr(login_manager.browser_manager, 'browser_type', '')
                })
        
        # API端特有数据
        elif client_type == 'api':
            session_data.update({
                'token': getattr(login_manager, 'token', None),
                'api_base_url': getattr(login_manager.api_client, 'base_url', '') if hasattr(login_manager, 'api_client') else ''
            })
        
        return session_data
