"""
全局登录管理器 - 提供统一的登录入口，兼容现有的Web和API登录管理器
"""
from typing import Optional, Dict, Any, Union
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from utils.core.auth.login_manager import WebLoginManager, APILoginManager


class GlobalLoginManager:
    """全局登录管理器 - 统一入口，内部委托给具体的登录管理器"""
    
    def __init__(self, client_type: str, client=None):
        """
        初始化全局登录管理器
        
        Args:
            client_type: 客户端类型 ('web' 或 'api')
            client: 客户端实例 (browser_manager 或 api_client)
        """
        self.client_type = client_type.lower()
        self.client = client
        self.manager = None
        self.config = get_merged_config()
        
        # 根据类型创建对应的管理器
        if self.client_type == 'web':
            self.manager = WebLoginManager(client)
        elif self.client_type == 'api':
            self.manager = APILoginManager(client)
        else:
            raise ValueError(f"不支持的客户端类型: {client_type}")
        
        logger.info(f"全局登录管理器初始化完成 - 类型: {self.client_type}")
    
    def login(self, username: str = None, password: str = None, **kwargs) -> bool:
        """
        执行登录 - 委托给具体的登录管理器
        
        Args:
            username: 用户名
            password: 密码
            **kwargs: 其他参数
            
        Returns:
            登录是否成功
        """
        if not self.manager:
            logger.error("登录管理器未初始化")
            return False
        
        try:
            # 获取默认用户凭据
            if not username or not password:
                users = self.config.get('test_data', {}).get('users', {})
                user_data = users.get('admin', {})
                username = username or user_data.get('username')
                password = password or user_data.get('password')
            
            # 委托给具体管理器执行登录
            success = self.manager.login(username=username, password=password)
            
            if success:
                logger.info(f"{self.client_type.upper()}全局登录成功 - 用户: {username}")
            else:
                logger.warning(f"{self.client_type.upper()}全局登录失败 - 用户: {username}")
            
            return success
            
        except Exception as e:
            logger.error(f"{self.client_type.upper()}全局登录异常: {e}")
            return False
    
    def navigate_to_target_page(self, target_url: str = None) -> bool:
        """
        导航到目标页面 (仅Web端支持)
        
        Args:
            target_url: 目标页面URL
            
        Returns:
            导航是否成功
        """
        if self.client_type != 'web':
            logger.warning("API端不支持页面导航")
            return True
        
        if not self.manager:
            logger.error("Web登录管理器未初始化")
            return False
        
        try:
            success = self.manager.navigate_to_target_page(target_url)
            if success:
                logger.info("导航到目标页面成功")
            else:
                logger.warning("导航到目标页面失败")
            return success
            
        except Exception as e:
            logger.error(f"导航到目标页面异常: {e}")
            return False
    
    def ensure_on_target_page(self, target_url: str = None, url_pattern: str = None) -> bool:
        """
        确保在目标页面 (仅Web端支持)
        
        Args:
            target_url: 目标页面URL
            url_pattern: URL匹配模式
            
        Returns:
            是否在目标页面
        """
        if self.client_type != 'web':
            return True
        
        if not self.manager:
            return False
        
        try:
            return self.manager.ensure_on_target_page(target_url, url_pattern)
        except Exception as e:
            logger.error(f"检查目标页面异常: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        if not self.manager:
            return False
        return getattr(self.manager, 'is_logged_in', False)
    
    def logout(self):
        """登出"""
        if self.manager:
            try:
                self.manager.logout()
                logger.info(f"{self.client_type.upper()}登出完成")
            except Exception as e:
                logger.warning(f"{self.client_type.upper()}登出异常: {e}")
    
    def set_custom_login(self, login_func):
        """设置自定义登录函数"""
        if self.manager and hasattr(self.manager, 'set_custom_login'):
            self.manager.set_custom_login(login_func)
            logger.info(f"已设置{self.client_type.upper()}自定义登录函数")
    
    def set_custom_navigate(self, navigate_func):
        """设置自定义导航函数 (仅Web端支持)"""
        if self.client_type == 'web' and self.manager and hasattr(self.manager, 'set_custom_navigate'):
            self.manager.set_custom_navigate(navigate_func)
            logger.info("已设置Web自定义导航函数")
    
    def get_manager(self):
        """获取底层管理器实例 - 用于高级用法"""
        return self.manager


def create_global_login_manager(client_type: str, client=None) -> GlobalLoginManager:
    """
    工厂函数 - 创建全局登录管理器
    
    Args:
        client_type: 客户端类型 ('web' 或 'api')
        client: 客户端实例
        
    Returns:
        GlobalLoginManager实例
    """
    return GlobalLoginManager(client_type, client)
