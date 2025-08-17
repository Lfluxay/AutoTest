"""
依赖注入容器
提供依赖注入和控制反转功能，提高代码的可测试性和可维护性
"""
import inspect
from typing import Dict, Any, Type, TypeVar, Callable, Optional, Union, get_type_hints
from abc import ABC, abstractmethod
from enum import Enum
from utils.exceptions import AutoTestException

T = TypeVar('T')


class LifetimeScope(Enum):
    """生命周期作用域"""
    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 瞬态
    SCOPED = "scoped"       # 作用域


class ServiceDescriptor:
    """服务描述符"""
    
    def __init__(self, service_type: Type, implementation: Union[Type, Callable], 
                 lifetime: LifetimeScope = LifetimeScope.TRANSIENT):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance = None


class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._building_stack: set = set()
    
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> 'DIContainer':
        """注册单例服务"""
        self._services[service_type] = ServiceDescriptor(service_type, implementation, LifetimeScope.SINGLETON)
        return self
    
    def register_transient(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> 'DIContainer':
        """注册瞬态服务"""
        self._services[service_type] = ServiceDescriptor(service_type, implementation, LifetimeScope.TRANSIENT)
        return self
    
    def register_scoped(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> 'DIContainer':
        """注册作用域服务"""
        self._services[service_type] = ServiceDescriptor(service_type, implementation, LifetimeScope.SCOPED)
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """注册实例"""
        self._singletons[service_type] = instance
        self._services[service_type] = ServiceDescriptor(service_type, lambda: instance, LifetimeScope.SINGLETON)
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """解析服务"""
        if service_type in self._building_stack:
            raise AutoTestException(f"检测到循环依赖: {service_type}", "CIRCULAR_DEPENDENCY")
        
        if service_type not in self._services:
            raise AutoTestException(f"服务未注册: {service_type}", "SERVICE_NOT_REGISTERED")
        
        descriptor = self._services[service_type]
        
        # 单例模式
        if descriptor.lifetime == LifetimeScope.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            instance = self._create_instance(descriptor)
            self._singletons[service_type] = instance
            return instance
        
        # 作用域模式
        elif descriptor.lifetime == LifetimeScope.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]
            
            instance = self._create_instance(descriptor)
            self._scoped_instances[service_type] = instance
            return instance
        
        # 瞬态模式
        else:
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建实例"""
        implementation = descriptor.implementation
        service_type = descriptor.service_type
        
        self._building_stack.add(service_type)
        
        try:
            # 如果是工厂函数
            if callable(implementation) and not inspect.isclass(implementation):
                return implementation()
            
            # 如果是类
            if inspect.isclass(implementation):
                # 获取构造函数参数
                constructor = implementation.__init__
                sig = inspect.signature(constructor)
                
                # 解析依赖
                dependencies = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    # 获取参数类型
                    param_type = param.annotation
                    if param_type == inspect.Parameter.empty:
                        # 尝试从类型提示获取
                        type_hints = get_type_hints(constructor)
                        param_type = type_hints.get(param_name)
                    
                    if param_type and param_type != inspect.Parameter.empty:
                        # 递归解析依赖
                        dependencies[param_name] = self.resolve(param_type)
                    elif param.default != inspect.Parameter.empty:
                        # 使用默认值
                        dependencies[param_name] = param.default
                    else:
                        raise AutoTestException(
                            f"无法解析参数 {param_name} 的类型，请添加类型注解", 
                            "MISSING_TYPE_ANNOTATION"
                        )
                
                return implementation(**dependencies)
            
            else:
                raise AutoTestException(f"不支持的实现类型: {type(implementation)}", "UNSUPPORTED_IMPLEMENTATION")
        
        finally:
            self._building_stack.discard(service_type)
    
    def clear_scoped(self) -> None:
        """清除作用域实例"""
        self._scoped_instances.clear()
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services
    
    def get_registered_services(self) -> Dict[Type, ServiceDescriptor]:
        """获取所有已注册的服务"""
        return self._services.copy()


# 全局容器实例
container = DIContainer()


# 装饰器
def injectable(lifetime: LifetimeScope = LifetimeScope.TRANSIENT):
    """可注入装饰器"""
    def decorator(cls):
        # 自动注册到容器
        if lifetime == LifetimeScope.SINGLETON:
            container.register_singleton(cls, cls)
        elif lifetime == LifetimeScope.SCOPED:
            container.register_scoped(cls, cls)
        else:
            container.register_transient(cls, cls)
        
        return cls
    return decorator


def singleton(cls):
    """单例装饰器"""
    return injectable(LifetimeScope.SINGLETON)(cls)


def transient(cls):
    """瞬态装饰器"""
    return injectable(LifetimeScope.TRANSIENT)(cls)


def scoped(cls):
    """作用域装饰器"""
    return injectable(LifetimeScope.SCOPED)(cls)


# 便捷函数
def resolve(service_type: Type[T]) -> T:
    """解析服务的便捷函数"""
    return container.resolve(service_type)


def register_singleton(service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> DIContainer:
    """注册单例服务的便捷函数"""
    return container.register_singleton(service_type, implementation)


def register_transient(service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> DIContainer:
    """注册瞬态服务的便捷函数"""
    return container.register_transient(service_type, implementation)


def register_scoped(service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> DIContainer:
    """注册作用域服务的便捷函数"""
    return container.register_scoped(service_type, implementation)


def register_instance(service_type: Type[T], instance: T) -> DIContainer:
    """注册实例的便捷函数"""
    return container.register_instance(service_type, instance)


# 抽象基类
class IConfigService(ABC):
    """配置服务接口"""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        pass
    
    @abstractmethod
    def get_merged_config(self) -> Dict[str, Any]:
        pass


class ILoggerService(ABC):
    """日志服务接口"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        pass


class IDataParserService(ABC):
    """数据解析服务接口"""
    
    @abstractmethod
    def load_test_data(self, file_path: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_test_cases(self, file_path: str, case_filter: Optional[Dict[str, Any]] = None) -> list:
        pass


class IAPIClientService(ABC):
    """API客户端服务接口"""
    
    @abstractmethod
    def request(self, method: str, url: str, **kwargs) -> Any:
        pass
    
    @abstractmethod
    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        pass


class IWebBrowserService(ABC):
    """Web浏览器服务接口"""
    
    @abstractmethod
    def start_browser(self, browser_type: Optional[str] = None, headless: Optional[bool] = None) -> None:
        pass
    
    @abstractmethod
    def get_page(self) -> Any:
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        pass


# 服务注册函数
def register_core_services() -> None:
    """注册核心服务"""
    from utils.config_parser import ConfigParser
    from utils.enhanced_logger import EnhancedLogger
    from utils.data_parser import DataParser
    from core.api.client import APIClient
    from core.web.browser import BrowserManager
    
    # 注册配置服务
    container.register_singleton(IConfigService, ConfigParser)
    
    # 注册日志服务
    container.register_singleton(ILoggerService, EnhancedLogger)
    
    # 注册数据解析服务
    container.register_transient(IDataParserService, DataParser)
    
    # 注册API客户端服务
    container.register_scoped(IAPIClientService, APIClient)
    
    # 注册Web浏览器服务
    container.register_scoped(IWebBrowserService, BrowserManager)
