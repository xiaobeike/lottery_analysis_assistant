"""缓存管理模块"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(
        self,
        cache_dir: str = "./data/cache",
        ttl_hours: int = 24
    ):
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self._ensure_cache_dirs()
    
    def _ensure_cache_dirs(self):
        """确保缓存目录存在"""
        for lottery_type in ['ssq', 'dlt']:
            cache_path = self.cache_dir / lottery_type
            cache_path.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_file(self, lottery_type: str, cache_type: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / lottery_type / f"{cache_type}.json"
    
    def is_cache_valid(self, lottery_type: str, cache_type: str = "history") -> bool:
        """检查缓存是否有效"""
        cache_file = self._get_cache_file(lottery_type, cache_type)
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            timestamp_str = cache_data.get('timestamp')
            if not timestamp_str:
                return False
            
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            
            return (now - timestamp) < timedelta(hours=self.ttl_hours)
            
        except Exception as e:
            logger.warning(f"检查缓存失败: {e}")
            return False
    
    def save_cache(
        self,
        lottery_type: str,
        data: Any,
        cache_type: str = "history"
    ):
        """保存缓存"""
        cache_file = self._get_cache_file(lottery_type, cache_type)
        
        cache_data = {
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'cache_type': cache_type,
            'lottery_type': lottery_type
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"缓存已保存: {cache_file}")
    
    def load_cache(self, lottery_type: str, cache_type: str = "history") -> Optional[Any]:
        """加载缓存"""
        cache_file = self._get_cache_file(lottery_type, cache_type)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            return cache_data.get('data')
            
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return None
    
    def get_cache_info(self, lottery_type: str, cache_type: str = "history") -> Dict[str, Any]:
        """获取缓存信息"""
        cache_file = self._get_cache_file(lottery_type, cache_type)
        
        if not cache_file.exists():
            return {
                'exists': False,
                'valid': False,
                'file_path': str(cache_file)
            }
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            timestamp = datetime.fromisoformat(cache_data.get('timestamp', ''))
            now = datetime.now()
            is_valid = (now - timestamp) < timedelta(hours=self.ttl_hours)
            
            return {
                'exists': True,
                'valid': is_valid,
                'timestamp': cache_data.get('timestamp'),
                'age_hours': (now - timestamp).total_seconds() / 3600,
                'file_path': str(cache_file)
            }
            
        except Exception as e:
            return {
                'exists': True,
                'valid': False,
                'error': str(e),
                'file_path': str(cache_file)
            }
    
    def clear_expired_cache(self):
        """清理过期缓存"""
        for lottery_type in ['ssq', 'dlt']:
            for cache_type in ['latest', 'history', 'statistics']:
                cache_file = self._get_cache_file(lottery_type, cache_type)
                
                if cache_file.exists() and not self.is_cache_valid(lottery_type, cache_type):
                    cache_file.unlink()
                    logger.info(f"已清理过期缓存: {cache_file}")
    
    def clear_all_cache(self, lottery_type: str = None):
        """清理所有缓存"""
        if lottery_type:
            types_to_clear = ['latest', 'history', 'statistics']
            for cache_type in types_to_clear:
                cache_file = self._get_cache_file(lottery_type, cache_type)
                if cache_file.exists():
                    cache_file.unlink()
        else:
            for lt in ['ssq', 'dlt']:
                self.clear_all_cache(lt)
