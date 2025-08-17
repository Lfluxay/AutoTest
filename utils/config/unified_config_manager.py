#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理器
解决配置管理分散、重复加载、缺乏热重载等问题
"""

import os
import yaml
import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.logging.logger import logger
from utils.core.exceptions import ConfigException


class ConfigFileWatcher(FileSystemEventHandler):
    """配置文件监控器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.last_modified = {}
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix in ['.yaml', '.yml', '.json']:
            # 防止重复触发
            current_time = time.time()
            last_time = self.last_modified.get(str(file_path), 0)
            if current_time - last_time < 1:  # 1秒内的重复事件忽略
                return
            
            self.last_modified[str(file_path)] = current_time
            logger.info(f"检测到配置文件变更: {file_path}")
            self.config_manager._reload_config_file(file_path)


class UnifiedConfigManager:
    """
    统一配置管理器 - 单例模式
    
    功能特性:
    1. 统一的配置加载和访问接口
    2. 多环境配置支持
    3. 配置文件热重载
    4. 配置缓存和性能优化
    5. 配置验证和类型转换
    6. 配置变更通知机制
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        self.initialized = True
        self._config_cache: Dict[str, Any] = {}
        self._file_cache: Dict[str, Dict[str, Any]] = {}
        self._file_timestamps: Dict[str, float] = {}
        self._change_listeners: List[Callable[[str, Any, Any], None]] = []
        self._lock = threading.RLock()
        
        # 项目路径配置
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        
        # 环境配置
        self.current_env = os.environ.get('ENV', 'dev')
        
        # 文件监控
        self.observer = None
        self.watcher = None
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化配置管理器"""
        try:
            # 加载主配置文件
            self._load_main_config()

            # 加载测试设置配置
            self._load_test_settings_config()

            # 加载环境配置
            self._load_env_config()

            # 启动文件监控
            self._start_file_watcher()

            logger.info(f"统一配置管理器初始化完成，当前环境: {self.current_env}")

        except Exception as e:
            logger.error(f"配置管理器初始化失败: {e}")
            raise ConfigException(f"配置管理器初始化失败: {e}")
    
    def _load_main_config(self):
        """加载主配置文件"""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            self._load_config_file(config_file, 'main')
        else:
            logger.warning(f"主配置文件不存在: {config_file}")

    def _load_test_settings_config(self):
        """加载测试设置配置文件"""
        test_settings_file = self.config_dir / "test_settings.yaml"
        if test_settings_file.exists():
            self._load_config_file(test_settings_file, 'test_settings')
        else:
            logger.warning(f"测试设置配置文件不存在: {test_settings_file}")
    
    def _load_env_config(self):
        """加载环境配置文件"""
        env_files = [
            self.config_dir / f"environments.yaml",
            self.config_dir / f"env_{self.current_env}.yaml",
            self.config_dir / f"{self.current_env}.yaml"
        ]

        for env_file in env_files:
            if env_file.exists():
                # 加载环境配置文件
                env_data = self._load_config_file(env_file, f'env_{self.current_env}_raw')

                # 如果是environments.yaml，提取当前环境的配置
                if env_file.name == "environments.yaml" and env_data:
                    current_env_config = env_data.get(self.current_env, {})
                    self._file_cache[f'env_{self.current_env}'] = current_env_config
                    logger.debug(f"从environments.yaml提取{self.current_env}环境配置: {len(current_env_config)}项")
                else:
                    # 直接使用配置数据
                    self._file_cache[f'env_{self.current_env}'] = env_data or {}
                    logger.debug(f"直接加载环境配置: {len(env_data or {})}项")

                logger.info(f"环境配置加载完成: {env_file}, 环境: {self.current_env}")
                break
        else:
            logger.warning(f"未找到环境配置文件: {self.current_env}")
    
    def _load_config_file(self, file_path: Path, cache_key: str):
        """加载单个配置文件"""
        try:
            with self._lock:
                # 检查文件时间戳
                current_mtime = file_path.stat().st_mtime
                cached_mtime = self._file_timestamps.get(str(file_path), 0)
                
                if current_mtime <= cached_mtime and cache_key in self._file_cache:
                    return self._file_cache[cache_key]
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.suffix.lower() == '.json':
                        data = json.load(f)
                    else:
                        data = yaml.safe_load(f)
                
                # 更新缓存
                self._file_cache[cache_key] = data or {}
                self._file_timestamps[str(file_path)] = current_mtime
                
                logger.debug(f"加载配置文件: {file_path}")
                return data
                
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
            raise ConfigException(f"加载配置文件失败 {file_path}: {e}")
    
    def _start_file_watcher(self):
        """启动文件监控"""
        try:
            if self.observer is None:
                self.watcher = ConfigFileWatcher(self)
                self.observer = Observer()
                self.observer.schedule(self.watcher, str(self.config_dir), recursive=True)
                self.observer.start()
                logger.debug("配置文件监控已启动")
        except Exception as e:
            logger.warning(f"启动配置文件监控失败: {e}")
    
    def _reload_config_file(self, file_path: Path):
        """重新加载配置文件"""
        try:
            # 确定缓存键
            if file_path.name == 'config.yaml':
                cache_key = 'main'
            elif file_path.name == 'test_settings.yaml':
                cache_key = 'test_settings'
            elif 'env' in file_path.name or file_path.name == f'{self.current_env}.yaml':
                cache_key = f'env_{self.current_env}'
            else:
                cache_key = file_path.stem

            # 重新加载
            old_config = self._file_cache.get(cache_key, {}).copy()
            self._load_config_file(file_path, cache_key)
            new_config = self._file_cache.get(cache_key, {})

            # 通知变更监听器
            self._notify_config_change(cache_key, old_config, new_config)

            # 清除相关缓存
            self._clear_related_cache(cache_key)

        except Exception as e:
            logger.error(f"重新加载配置文件失败 {file_path}: {e}")
    
    def _notify_config_change(self, config_key: str, old_config: Dict, new_config: Dict):
        """通知配置变更"""
        for listener in self._change_listeners:
            try:
                listener(config_key, old_config, new_config)
            except Exception as e:
                logger.error(f"配置变更通知失败: {e}")
    
    def _clear_related_cache(self, config_key: str):
        """清除相关缓存"""
        with self._lock:
            # 清除合并配置缓存
            keys_to_remove = [k for k in self._config_cache.keys() if config_key in k]
            for key in keys_to_remove:
                del self._config_cache[key]
    
    def get_config(self, key_path: str, default: Any = None, env: Optional[str] = None) -> Any:
        """
        获取配置项
        
        Args:
            key_path: 配置路径，如 'api.base_url'
            default: 默认值
            env: 指定环境，为None时使用当前环境
            
        Returns:
            配置值
        """
        env = env or self.current_env
        cache_key = f"{env}:{key_path}"
        
        # 检查缓存
        with self._lock:
            if cache_key in self._config_cache:
                return self._config_cache[cache_key]
        
        # 获取合并配置
        merged_config = self.get_merged_config(env)
        
        # 解析路径
        value = self._get_nested_value(merged_config, key_path, default)
        
        # 缓存结果
        with self._lock:
            self._config_cache[cache_key] = value
        
        return value
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str, default: Any) -> Any:
        """获取嵌套字典值"""
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_merged_config(self, env: Optional[str] = None) -> Dict[str, Any]:
        """
        获取合并后的配置
        合并顺序：主配置 -> 测试设置配置 -> 环境配置

        Args:
            env: 环境名称

        Returns:
            合并后的配置字典
        """
        env = env or self.current_env
        cache_key = f"merged:{env}"

        with self._lock:
            if cache_key in self._config_cache:
                return self._config_cache[cache_key]

        # 获取主配置
        main_config = self._file_cache.get('main', {}).copy()

        # 获取测试设置配置
        test_settings_config = self._file_cache.get('test_settings', {})

        # 获取环境配置
        env_config = self._file_cache.get(f'env_{env}', {})

        # 深度合并：主配置 -> 测试设置 -> 环境配置
        merged = self._deep_merge(main_config, test_settings_config)
        merged = self._deep_merge(merged, env_config)

        # 缓存结果
        with self._lock:
            self._config_cache[cache_key] = merged

        return merged
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def set_config(self, key_path: str, value: Any, env: Optional[str] = None):
        """
        设置配置项（运行时）
        注意：这只会影响内存中的配置，不会写入文件
        
        Args:
            key_path: 配置路径
            value: 配置值
            env: 环境名称
        """
        env = env or self.current_env
        
        with self._lock:
            # 清除相关缓存
            cache_keys_to_remove = [k for k in self._config_cache.keys() if env in k]
            for key in cache_keys_to_remove:
                del self._config_cache[key]
            
            # 设置值到环境配置
            env_key = f'env_{env}'
            if env_key not in self._file_cache:
                self._file_cache[env_key] = {}
            
            self._set_nested_value(self._file_cache[env_key], key_path, value)
    
    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """设置嵌套字典值"""
        keys = key_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def add_change_listener(self, listener: Callable[[str, Any, Any], None]):
        """添加配置变更监听器"""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, Any, Any], None]):
        """移除配置变更监听器"""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
    
    def clear_cache(self):
        """清除所有缓存"""
        with self._lock:
            self._config_cache.clear()
            logger.debug("配置缓存已清除")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        with self._lock:
            return {
                'config_cache_size': len(self._config_cache),
                'file_cache_size': len(self._file_cache),
                'cached_files': list(self._file_timestamps.keys()),
                'current_env': self.current_env
            }
    
    def shutdown(self):
        """关闭配置管理器"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.debug("配置文件监控已停止")


# 全局配置管理器实例
unified_config = UnifiedConfigManager()

# 便捷函数
def get_config(key_path: str, default: Any = None, env: Optional[str] = None) -> Any:
    """获取配置项的便捷函数"""
    return unified_config.get_config(key_path, default, env)

def get_merged_config(env: Optional[str] = None) -> Dict[str, Any]:
    """获取合并配置的便捷函数"""
    return unified_config.get_merged_config(env)

def set_config(key_path: str, value: Any, env: Optional[str] = None):
    """设置配置项的便捷函数"""
    unified_config.set_config(key_path, value, env)

def add_config_listener(listener: Callable[[str, Any, Any], None]):
    """添加配置变更监听器的便捷函数"""
    unified_config.add_change_listener(listener)
