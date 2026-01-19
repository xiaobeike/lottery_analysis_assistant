"""数据获取模块"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .cache_manager import CacheManager
from .api_client import LotteryAPIClient

logger = logging.getLogger(__name__)


class LotteryDataFetcher:
    """彩票数据获取器"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        cache_manager: CacheManager = None,
        api_client: LotteryAPIClient = None
    ):
        self.config = config
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.get('data', {}).get('cache', {}).get('cache_dir', './data/cache'),
            ttl_hours=config.get('data', {}).get('cache', {}).get('ttl_hours', 24)
        )
        self.api_client = api_client or LotteryAPIClient(
            base_url=config.get('data', {}).get('api_base_url', 
            'http://api.huiniao.top/interface/home/lotteryHistory')
        )
        
        self.periods = config.get('data', {}).get('periods', 30)
    
    def fetch_data(
        self,
        lottery_type: str,
        periods: int = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取彩票数据（带缓存）
        
        Args:
            lottery_type: 彩票类型 (ssq/dlt)
            periods: 获取期数
        
        Returns:
            彩票数据列表
        """
        periods = periods or self.periods
        
        cache_key = f"history_{periods}"
        
        # 1. 尝试从缓存获取
        if self.cache_manager.is_cache_valid(lottery_type, cache_key):
            cached_data = self.cache_manager.load_cache(lottery_type, cache_key)
            if cached_data and len(cached_data) >= periods:
                logger.info(f"使用缓存数据: {lottery_type}, {len(cached_data)} 条")
                return cached_data[:periods]
        
        # 2. 调用API获取
        logger.info(f"调用API获取数据: {lottery_type}")
        api_data = self.api_client.fetch_data(lottery_type, periods)
        
        if not api_data:
            # API失败，尝试使用过期缓存
            cached_data = self.cache_manager.load_cache(lottery_type, cache_key)
            if cached_data:
                logger.warning("API调用失败，使用过期缓存数据")
                return cached_data[:periods] if len(cached_data) >= periods else cached_data
            
            logger.error(f"无法获取 {lottery_type} 数据")
            return None
        
        # 3. 保存到缓存
        self.cache_manager.save_cache(lottery_type, api_data, cache_key)
        
        logger.info(f"数据已缓存: {lottery_type}, {len(api_data)} 条")
        return api_data
    
    def fetch_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """获取最新一期数据"""
        cache_key = "latest"
        
        # 尝试缓存
        if self.cache_manager.is_cache_valid(lottery_type, cache_key):
            cached = self.cache_manager.load_cache(lottery_type, cache_key)
            if cached:
                return cached
        
        # API获取
        latest = self.api_client.fetch_latest(lottery_type)
        
        if latest:
            self.cache_manager.save_cache(lottery_type, latest, cache_key)
        
        return latest
    
    def get_previous_draw_info(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """获取上一期开奖信息"""
        latest = self.fetch_latest(lottery_type)
        
        if not latest:
            return None
        
        lottery_config = self.config.get('lottery', {}).get(lottery_type, {})
        lottery_name = lottery_config.get('name', lottery_type.upper())
        
        # 格式化号码
        if lottery_type == 'ssq':
            numbers = f"{' '.join(map(str, latest.get('red_balls', [])))} | {latest.get('blue_ball', '')}"
        else:
            fronts = ' '.join(map(str, latest.get('front_balls', [])))
            backs = ' '.join(map(str, latest.get('back_balls', [])))
            numbers = f"{fronts} | {backs}"
        
        return {
            'lottery_name': lottery_name,
            'lottery_type': lottery_type,
            'period': latest.get('period', ''),
            'date': latest.get('date', ''),
            'open_time': latest.get('open_time', ''),
            'numbers': numbers,
            'draw_time': lottery_config.get('draw_time', '')
        }
    
    def get_analysis_data(
        self,
        lottery_type: str,
        periods: int = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取用于分析的数据（排除最新一期）
        
        Args:
            lottery_type: 彩票类型
            periods: 分析期数
        
        Returns:
            历史数据列表（不包含最新一期）
        """
        periods = periods or self.periods
        
        all_data = self.fetch_data(lottery_type, periods + 5)  # 多获取几期
        
        if not all_data or len(all_data) < 2:
            return all_data
        
        # 排除最新一期，返回历史数据用于分析
        return all_data[1:periods + 1]
