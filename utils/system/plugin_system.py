"""
插件系统
提供插件化架构，支持动态加载和扩展功能
"""
import os
import sys
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from utils.logging.logger import logger
from utils.exceptions import AutoTestException


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    dependencies: List[str]
    enabled: bool = True


class IPlugin(ABC):
    """插件接口"""
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """插件信息"""
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件"""
        pass


class IKeywordPlugin(IPlugin):
    """关键字插件接口"""
    
    @abstractmethod
    def get_keywords(self) -> Dict[str, Callable]:
        """获取关键字映射"""
        pass


class IAssertionPlugin(IPlugin):
    """断言插件接口"""
    
    @abstractmethod
    def get_assertions(self) -> Dict[str, Callable]:
        """获取断言映射"""
        pass


class IReportPlugin(IPlugin):
    """报告插件接口"""
    
    @abstractmethod
    def generate_report(self, test_results: List[Dict[str, Any]], output_path: str) -> None:
        """生成报告"""
        pass


class INotificationPlugin(IPlugin):
    """通知插件接口"""
    
    @abstractmethod
    def send_notification(self, message: str, data: Dict[str, Any]) -> bool:
        """发送通知"""
        pass


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        初始化插件管理器
        
        Args:
            plugin_dirs: 插件目录列表
        """
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, IPlugin] = {}
        self.plugin_types: Dict[str, List[IPlugin]] = {
            'keyword': [],
            'assertion': [],
            'report': [],
            'notification': []
        }
        self._initialized = False
        
        # 添加默认插件目录
        project_root = Path(__file__).parent.parent
        default_plugin_dir = project_root / "plugins"
        if default_plugin_dir.exists():
            self.plugin_dirs.append(str(default_plugin_dir))
    
    def discover_plugins(self) -> List[str]:
        """发现插件"""
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                logger.warning(f"插件目录不存在: {plugin_dir}")
                continue
            
            # 添加到Python路径
            if str(plugin_path) not in sys.path:
                sys.path.insert(0, str(plugin_path))
            
            # 扫描Python文件
            for py_file in plugin_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                try:
                    # 构建模块名
                    relative_path = py_file.relative_to(plugin_path)
                    module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
                    
                    # 导入模块
                    module = importlib.import_module(module_name)
                    
                    # 查找插件类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, IPlugin) and 
                            obj != IPlugin and 
                            not inspect.isabstract(obj)):
                            discovered_plugins.append(f"{module_name}.{name}")
                            logger.debug(f"发现插件: {module_name}.{name}")
                
                except Exception as e:
                    logger.error(f"加载插件文件失败: {py_file}, 错误: {e}")
        
        return discovered_plugins
    
    def load_plugin(self, plugin_class_path: str) -> bool:
        """
        加载插件
        
        Args:
            plugin_class_path: 插件类路径，格式为 "module.ClassName"
            
        Returns:
            是否加载成功
        """
        try:
            # 解析模块和类名
            module_name, class_name = plugin_class_path.rsplit(".", 1)
            
            # 导入模块
            module = importlib.import_module(module_name)
            
            # 获取插件类
            plugin_class = getattr(module, class_name)
            
            # 创建插件实例
            plugin_instance = plugin_class()
            
            # 验证插件接口
            if not isinstance(plugin_instance, IPlugin):
                raise AutoTestException(f"插件必须实现IPlugin接口: {plugin_class_path}", "INVALID_PLUGIN")
            
            # 获取插件信息
            plugin_info = plugin_instance.info
            
            # 检查依赖
            if not self._check_dependencies(plugin_info.dependencies):
                logger.error(f"插件依赖检查失败: {plugin_info.name}")
                return False
            
            # 注册插件
            self.plugins[plugin_info.name] = plugin_instance
            
            # 按类型分类
            if isinstance(plugin_instance, IKeywordPlugin):
                self.plugin_types['keyword'].append(plugin_instance)
            if isinstance(plugin_instance, IAssertionPlugin):
                self.plugin_types['assertion'].append(plugin_instance)
            if isinstance(plugin_instance, IReportPlugin):
                self.plugin_types['report'].append(plugin_instance)
            if isinstance(plugin_instance, INotificationPlugin):
                self.plugin_types['notification'].append(plugin_instance)
            
            logger.info(f"插件加载成功: {plugin_info.name} v{plugin_info.version}")
            return True
            
        except Exception as e:
            logger.error(f"加载插件失败: {plugin_class_path}, 错误: {e}")
            return False
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查插件依赖"""
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.error(f"缺少依赖: {dep}")
                return False
        return True
    
    def initialize_plugins(self, context: Optional[Dict[str, Any]] = None) -> None:
        """初始化所有插件"""
        if self._initialized:
            return
        
        context = context or {}
        
        for plugin_name, plugin in self.plugins.items():
            try:
                if plugin.info.enabled:
                    plugin.initialize(context)
                    logger.debug(f"插件初始化成功: {plugin_name}")
            except Exception as e:
                logger.error(f"插件初始化失败: {plugin_name}, 错误: {e}")
        
        self._initialized = True
    
    def cleanup_plugins(self) -> None:
        """清理所有插件"""
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                logger.debug(f"插件清理完成: {plugin_name}")
            except Exception as e:
                logger.error(f"插件清理失败: {plugin_name}, 错误: {e}")
        
        self._initialized = False
    
    def get_plugins_by_type(self, plugin_type: str) -> List[IPlugin]:
        """根据类型获取插件"""
        return self.plugin_types.get(plugin_type, [])
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """根据名称获取插件"""
        return self.plugins.get(plugin_name)
    
    def get_all_keywords(self) -> Dict[str, Callable]:
        """获取所有关键字"""
        keywords = {}
        for plugin in self.get_plugins_by_type('keyword'):
            if isinstance(plugin, IKeywordPlugin):
                plugin_keywords = plugin.get_keywords()
                keywords.update(plugin_keywords)
        return keywords
    
    def get_all_assertions(self) -> Dict[str, Callable]:
        """获取所有断言"""
        assertions = {}
        for plugin in self.get_plugins_by_type('assertion'):
            if isinstance(plugin, IAssertionPlugin):
                plugin_assertions = plugin.get_assertions()
                assertions.update(plugin_assertions)
        return assertions
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.info.enabled = True
            logger.info(f"插件已启用: {plugin_name}")
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.info.enabled = False
            logger.info(f"插件已禁用: {plugin_name}")
            return True
        return False
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """获取所有插件信息"""
        return [
            {
                "name": plugin.info.name,
                "version": plugin.info.version,
                "description": plugin.info.description,
                "author": plugin.info.author,
                "plugin_type": plugin.info.plugin_type,
                "enabled": plugin.info.enabled,
                "dependencies": plugin.info.dependencies
            }
            for plugin in self.plugins.values()
        ]


# 全局插件管理器实例
plugin_manager = PluginManager()


# 便捷函数
def discover_plugins() -> List[str]:
    """发现插件的便捷函数"""
    return plugin_manager.discover_plugins()


def load_plugin(plugin_class_path: str) -> bool:
    """加载插件的便捷函数"""
    return plugin_manager.load_plugin(plugin_class_path)


def initialize_plugins(context: Optional[Dict[str, Any]] = None) -> None:
    """初始化插件的便捷函数"""
    plugin_manager.initialize_plugins(context)


def cleanup_plugins() -> None:
    """清理插件的便捷函数"""
    plugin_manager.cleanup_plugins()


def get_all_keywords() -> Dict[str, Callable]:
    """获取所有关键字的便捷函数"""
    return plugin_manager.get_all_keywords()


def get_all_assertions() -> Dict[str, Callable]:
    """获取所有断言的便捷函数"""
    return plugin_manager.get_all_assertions()
