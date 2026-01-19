"""配置加载模块"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

_config: Optional[Dict[str, Any]] = None


def load_config(config_path: str = None) -> Dict[str, Any]:
    """加载配置文件"""
    global _config
    
    if _config is not None:
        return _config
    
    # 加载环境变量
    load_dotenv()
    
    # 确定配置文件路径
    if config_path is None:
        config_path = os.getenv('CONFIG_PATH', './config/config.yaml')
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)
    
    # 替换环境变量占位符
    _config = _replace_env_placeholders(_config)
    
    return _config


def get_config() -> Dict[str, Any]:
    """获取已加载的配置"""
    global _config
    
    if _config is None:
        return load_config()
    
    return _config


def _replace_env_placeholders(config: Dict[str, Any]) -> Dict[str, Any]:
    """递归替换配置中的环境变量占位符"""
    if isinstance(config, dict):
        return {key: _replace_env_placeholders(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [_replace_env_placeholders(item) for item in config]
    elif isinstance(config, str):
        # 替换 {{ENV_NAME}} 格式的环境变量
        if config.startswith('YOUR_') or config.startswith('your_'):
            env_key = config.upper()
            env_value = os.getenv(env_key)
            if env_value:
                return env_value
        return config
    return config


def reset_config():
    """重置配置（用于测试）"""
    global _config
    _config = None
