"""
Common模块 - 提供测试用例执行前的通用功能

包含：
- 全局登录管理
- 导航管理  
- 会话管理
- 通用fixtures
"""

__version__ = "1.0.0"
__author__ = "Auto Test Framework"

# 导出主要类
from .auth.global_login import GlobalLoginManager
from .navigation.navigator import NavigationManager
from .auth.session_manager import SessionManager

__all__ = [
    'GlobalLoginManager',
    'NavigationManager', 
    'SessionManager'
]
