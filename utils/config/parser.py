import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logging.logger import logger


class ConfigParser:
    """配置文件解析器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self._config = None
        self._env_config = None
        
    def load_config(self) -> Dict[str, Any]:
        """加载主配置文件"""
        if self._config is None:
            config_file = self.config_dir / "config.yaml"
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                logger.info(f"加载配置文件成功: {config_file}")
            except FileNotFoundError:
                logger.error(f"配置文件不存在: {config_file}")
                raise
            except yaml.YAMLError as e:
                logger.error(f"配置文件格式错误: {e}")
                raise
        return self._config
    
    def load_env_config(self, env: Optional[str] = None) -> Dict[str, Any]:
        """加载环境配置文件"""
        if env is None:
            env = os.getenv('ENV', 'dev')
            
        env_config_file = self.config_dir / "env_config.yaml"
        try:
            with open(env_config_file, 'r', encoding='utf-8') as f:
                all_env_config = yaml.safe_load(f)
            
            if env not in all_env_config:
                logger.warning(f"环境配置 {env} 不存在，使用默认环境 dev")
                env = 'dev'
            
            self._env_config = all_env_config.get(env, {})
            logger.info(f"加载环境配置成功: {env}")
            return self._env_config
            
        except FileNotFoundError:
            logger.warning(f"环境配置文件不存在: {env_config_file}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"环境配置文件格式错误: {e}")
            return {}
    
    def get_config(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key_path: 配置路径，如 'api.base_url'
            default: 默认值
            
        Returns:
            配置值
        """
        if not key_path:
            logger.warning("配置键路径不能为空")
            return default

        try:
            config = self.load_config()
            keys = key_path.split('.')

            value = config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    logger.debug(f"配置键 '{key_path}' 不存在，返回默认值: {default}")
                    return default

            return value
        except Exception as e:
            logger.error(f"获取配置项失败: {key_path}, 错误: {e}")
            return default
    
    def get_env_config(self, key_path: str, default: Any = None, env: Optional[str] = None) -> Any:
        """
        获取环境配置项
        
        Args:
            key_path: 配置路径，如 'api.base_url'
            default: 默认值
            env: 环境名称
            
        Returns:
            配置值
        """
        env_config = self.load_env_config(env)
        keys = key_path.split('.')
        
        value = env_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def merge_config(self, env: Optional[str] = None) -> Dict[str, Any]:
        """
        合并主配置和环境配置
        环境配置会覆盖主配置中的相同项
        
        Args:
            env: 环境名称
            
        Returns:
            合并后的配置
        """
        main_config = self.load_config().copy()
        env_config = self.load_env_config(env)
        
        return self._deep_merge(main_config, env_config)
    
    def _deep_merge(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                base_dict[key] = self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
        return base_dict
    
    def get_project_root(self) -> Path:
        """获取项目根目录"""
        return self.project_root
    
    def get_reports_dir(self) -> Path:
        """获取报告目录"""
        return self.project_root / "reports"
    
    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        return self.project_root / "logs"
    
    def get_screenshots_dir(self) -> Path:
        """获取截图目录"""
        return self.project_root / "screenshots"
    
    def get_temp_dir(self) -> Path:
        """获取临时文件目录"""
        return self.project_root / "temp"
    
    def get_data_dir(self) -> Path:
        """获取数据目录"""
        return self.project_root / "data"


# 全局配置实例
config = ConfigParser()


def get_config(key_path: str, default: Any = None) -> Any:
    """获取配置项的便捷函数"""
    return config.get_config(key_path, default)


def get_env_config(key_path: str, default: Any = None, env: Optional[str] = None) -> Any:
    """获取环境配置项的便捷函数"""
    return config.get_env_config(key_path, default, env)


def get_merged_config(env: Optional[str] = None) -> Dict[str, Any]:
    """获取合并配置的便捷函数"""
    return config.merge_config(env)