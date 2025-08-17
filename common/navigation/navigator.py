"""
导航管理器 - 提供统一的导航功能
"""
from typing import Optional, Dict, Any
from utils.logging.logger import logger
from utils.config.parser import get_merged_config


class NavigationManager:
    """导航管理器 - 管理页面导航和API端点路径"""
    
    def __init__(self, client_type: str, client=None):
        """
        初始化导航管理器
        
        Args:
            client_type: 客户端类型 ('web' 或 'api')
            client: 客户端实例
        """
        self.client_type = client_type.lower()
        self.client = client
        self.config = get_merged_config()
        
        # 获取导航配置
        if self.client_type == 'web':
            self.nav_config = self.config.get('web', {}).get('navigation', {})
        elif self.client_type == 'api':
            self.nav_config = self.config.get('api', {}).get('navigation', {})
        else:
            raise ValueError(f"不支持的客户端类型: {client_type}")
        
        logger.info(f"导航管理器初始化完成 - 类型: {self.client_type}")
    
    def navigate_to(self, target: str, **kwargs) -> bool:
        """
        导航到指定目标
        
        Args:
            target: 目标标识 (URL、页面名称或API端点)
            **kwargs: 额外参数
            
        Returns:
            导航是否成功
        """
        if self.client_type == 'web':
            return self._web_navigate(target, **kwargs)
        elif self.client_type == 'api':
            return self._api_navigate(target, **kwargs)
        
        return False
    
    def _web_navigate(self, target: str, wait_for_load: bool = True, **kwargs) -> bool:
        """
        Web端导航
        
        Args:
            target: 目标URL或页面名称
            wait_for_load: 是否等待页面加载完成
            **kwargs: 额外参数
            
        Returns:
            导航是否成功
        """
        if not self.client or not hasattr(self.client, 'page'):
            logger.error("Web客户端未初始化或无page对象")
            return False
        
        try:
            page = self.client.page
            
            # 解析目标URL
            url = self._resolve_web_target(target)
            if not url:
                logger.error(f"无法解析目标: {target}")
                return False
            
            logger.info(f"导航到: {url}")
            page.goto(url)
            
            if wait_for_load:
                page.wait_for_load_state('networkidle')
            
            logger.info(f"导航成功: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Web导航失败: {e}")
            return False
    
    def _api_navigate(self, target: str, **kwargs) -> bool:
        """
        API端导航 (设置基础路径)
        
        Args:
            target: 目标端点或基础路径
            **kwargs: 额外参数
            
        Returns:
            设置是否成功
        """
        if not self.client:
            logger.error("API客户端未初始化")
            return False
        
        try:
            # 解析目标端点
            endpoint = self._resolve_api_target(target)
            if not endpoint:
                logger.error(f"无法解析API目标: {target}")
                return False
            
            # 设置基础路径或当前端点
            if hasattr(self.client, 'set_base_path'):
                self.client.set_base_path(endpoint)
            
            logger.info(f"API导航设置成功: {endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"API导航失败: {e}")
            return False
    
    def _resolve_web_target(self, target: str) -> Optional[str]:
        """
        解析Web目标
        
        Args:
            target: 目标标识
            
        Returns:
            解析后的URL
        """
        # 如果是完整URL，直接返回
        if target.startswith(('http://', 'https://')):
            return target
        
        # 从配置中查找预定义的页面
        pages = self.nav_config.get('pages', {})
        if target in pages:
            return pages[target]
        
        # 尝试拼接基础URL
        base_url = self.config.get('web', {}).get('base_url', '')
        if base_url:
            return f"{base_url.rstrip('/')}/{target.lstrip('/')}"
        
        return None
    
    def _resolve_api_target(self, target: str) -> Optional[str]:
        """
        解析API目标
        
        Args:
            target: 目标标识
            
        Returns:
            解析后的端点路径
        """
        # 如果是完整URL，直接返回
        if target.startswith(('http://', 'https://')):
            return target
        
        # 从配置中查找预定义的端点
        endpoints = self.nav_config.get('endpoints', {})
        if target in endpoints:
            return endpoints[target]
        
        # 尝试拼接基础URL
        base_url = self.config.get('api', {}).get('base_url', '')
        if base_url:
            return f"{base_url.rstrip('/')}/{target.lstrip('/')}"
        
        return target  # 返回原始路径
    
    def get_current_location(self) -> Optional[str]:
        """
        获取当前位置
        
        Returns:
            当前URL或端点
        """
        if self.client_type == 'web':
            if self.client and hasattr(self.client, 'page') and self.client.page:
                return self.client.page.url
        elif self.client_type == 'api':
            if self.client and hasattr(self.client, 'base_url'):
                return self.client.base_url
        
        return None
    
    def is_at_target(self, target: str, pattern: str = None) -> bool:
        """
        检查是否在目标位置
        
        Args:
            target: 目标标识
            pattern: 匹配模式 (支持通配符)
            
        Returns:
            是否在目标位置
        """
        current = self.get_current_location()
        if not current:
            return False
        
        # 解析目标
        if self.client_type == 'web':
            resolved_target = self._resolve_web_target(target)
        else:
            resolved_target = self._resolve_api_target(target)
        
        if not resolved_target:
            return False
        
        # 精确匹配
        if current == resolved_target:
            return True
        
        # 模式匹配
        if pattern:
            import fnmatch
            return fnmatch.fnmatch(current, pattern)
        
        # 包含匹配
        return resolved_target in current
    
    def go_back(self) -> bool:
        """
        返回上一页 (仅Web端支持)
        
        Returns:
            操作是否成功
        """
        if self.client_type != 'web':
            logger.warning("API端不支持返回操作")
            return False
        
        if not self.client or not hasattr(self.client, 'page'):
            return False
        
        try:
            self.client.page.go_back()
            logger.info("返回上一页成功")
            return True
        except Exception as e:
            logger.error(f"返回上一页失败: {e}")
            return False
    
    def refresh(self) -> bool:
        """
        刷新当前页面 (仅Web端支持)
        
        Returns:
            操作是否成功
        """
        if self.client_type != 'web':
            logger.warning("API端不支持刷新操作")
            return False
        
        if not self.client or not hasattr(self.client, 'page'):
            return False
        
        try:
            self.client.page.reload()
            logger.info("页面刷新成功")
            return True
        except Exception as e:
            logger.error(f"页面刷新失败: {e}")
            return False
