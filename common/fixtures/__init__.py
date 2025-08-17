"""
通用Fixtures模块 - 提供可复用的pytest fixtures
"""

from .web_fixtures import *
from .api_fixtures import *

__all__ = [
    # Web fixtures
    'global_web_session',
    'web_login_manager',
    'web_navigator',
    'enterprise_ready_web_session',
    'universal_ready_web_session',

    # API fixtures
    'global_api_session',
    'api_login_manager',
    'api_navigator',
    'enterprise_ready_api_session',
    'universal_ready_api_session'
]
