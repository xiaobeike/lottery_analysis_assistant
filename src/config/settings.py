"""配置加载模块"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

_config: Optional[Dict[str, Any]] = None


def load_config(config_path: str = None) -> Dict[str, Any]:
    """加载配置文件（优先使用环境变量）"""
    global _config
    
    if _config is not None:
        return _config
    
    # 加载.env文件（本地开发环境）
    load_dotenv()
    
    # 基础配置模板
    base_config = {
        'ai': {
            'providers': {
                'gemini': {
                    'enabled': True,
                    'api_key': os.getenv('GEMINI_API_KEY', ''),
                    'model': 'gemini-1.5-flash',
                    'model_fallback': 'gemini-2.0-flash-exp',  # 备选模型
                    'request_delay': 2.0,  # 请求间隔（秒）
                    'max_retries': 5,  # 最大重试次数
                    'retry_delay': 5.0,  # 重试基础延时（秒）
                    'temperature': 0.7,
                    'max_output_tokens': 2048
                },
                'deepseek': {
                    'enabled': True,
                    'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                    'model': 'deepseek-chat',
                    'temperature': 0.7
                }
            },
            'primary_provider': 'gemini'
        },
        'lottery': {
            'ssq': {
                'name': '双色球',
                'type': 'ssq',
                'draw_days': [2, 4, 7],
                'draw_time': '21:15',
                'red_range': [1, 33],
                'blue_range': [1, 16],
                'red_count': 6,
                'blue_count': 1
            },
            'dlt': {
                'name': '大乐透',
                'type': 'dlt',
                'draw_days': [1, 3, 6],
                'draw_time': '21:25',
                'front_range': [1, 35],
                'back_range': [1, 12],
                'front_count': 5,
                'back_count': 2
            }
        },
        'data': {
            'api_base_url': 'http://api.huiniao.top/interface/home/lotteryHistory',
            'periods': 30,
            'cache': {
                'enabled': True,
                'ttl_hours': 24,
                'cache_dir': './data/cache'
            }
        },
        'analysis': {
            'use_ai': True,
            'ai_analysis_weight': 0.7,
            'traditional_analysis_weight': 0.3
        },
        'recommendation': {
            'count': 5,
            'top_count': 3
        },
        'notification': {
            'wechat': {
                'webhook_url': os.getenv('WECHAT_WEBHOOK_URL', ''),
                'rate_limit': 20,
                'message_type': 'markdown',
                'mentioned_list': []
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': './logs/lottery_analysis.log'
        }
    }
    
    # 尝试从配置文件补充配置（如果存在）
    if config_path is None:
        config_path = './config/config.yaml'
    
    config_file = Path(config_path)
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # 深度合并配置
                    base_config = _deep_merge(base_config, file_config)
        except Exception as e:
            print(f"警告: 加载配置文件失败 ({e}), 将使用环境变量和默认值")
    
    _config = base_config
    
    # 再次确保敏感信息从环境变量读取
    _config['ai']['providers']['gemini']['api_key'] = os.getenv('GEMINI_API_KEY', '')
    _config['ai']['providers']['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY', '')
    _config['notification']['wechat']['webhook_url'] = os.getenv('WECHAT_WEBHOOK_URL', '')
    
    return _config


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并配置"""
    for key, value in override.items():
        if key in base:
            if isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = _deep_merge(base[key], value)
            else:
                base[key] = value
        else:
            base[key] = value
    return base


def get_config() -> Dict[str, Any]:
    """获取已加载的配置"""
    global _config
    
    if _config is None:
        return load_config()
    
    return _config


def reset_config():
    """重置配置（用于测试）"""
    global _config
    _config = None
