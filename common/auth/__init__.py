"""
认证模块 - 提供统一的登录和会话管理功能
"""

from .global_login import GlobalLoginManager
from .session_manager import SessionManager

__all__ = [
    'GlobalLoginManager',
    'SessionManager'
]
