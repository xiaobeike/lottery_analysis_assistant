"""数据获取模块"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .spider import DataSpider

logger = logging.getLogger(__name__)


class LotteryDataFetcher:
    """彩票数据获取器（使用500.com数据源）"""

    def __init__(
        self,
        config: Dict[str, Any],
        data_dir: str = None
    ):
        self.config = config
        self.data_dir = data_dir or config.get('data', {}).get('history_dir', './data/history')

        # 初始化爬虫
        self.spider = DataSpider(
            data_dir=self.data_dir,
            request_delay=2.0,
            max_retries=3
        )

        self.periods = config.get('data', {}).get('periods', 30)

    def fetch_data(
        self,
        lottery_type: str,
        periods: int = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取彩票数据

        Args:
            lottery_type: 彩票类型 (ssq/dlt)
            periods: 获取期数

        Returns:
            彩票数据列表
        """
        periods = periods or self.periods

        # 先尝试更新到最新数据
        logger.info(f"更新{lottery_type}到最新数据...")
        self.spider.update_to_latest(lottery_type)

        # 尝试加载本地历史数据
        existing_data = self.spider.load_history(lottery_type)

        # 如果本地数据不足30期，重新获取
        if not existing_data or len(existing_data) < periods:
            logger.info(f"本地数据不足{periods}期，重新获取...")
            existing_data = self.spider.fetch_history(lottery_type, periods)
            if existing_data:
                self.spider.save_history(lottery_type, existing_data)

        if existing_data and len(existing_data) >= periods:
            logger.info(f"使用本地缓存数据: {lottery_type}, {len(existing_data)} 条")
            return existing_data[:periods]

        # 初始化数据（首次运行或数据不足）
        logger.info(f"初始化{lottery_type}数据...")
        data = self.spider.initialize_data(lottery_type, periods)

        if not data:
            logger.error(f"无法获取 {lottery_type} 数据")
            return None

        return data[:periods]

    def fetch_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """获取最新一期数据"""
        # 获取最新期号
        latest_period = self.spider.get_latest_period(lottery_type)
        if not latest_period:
            logger.error(f"无法获取{lottery_type}最新期号")
            return None

        # 获取最新一期数据
        return self.spider.fetch_single(lottery_type, latest_period)

    def update_data(self, lottery_type: str) -> bool:
        """更新数据到最新一期"""
        try:
            updated_data = self.spider.update_to_latest(lottery_type)
            return len(updated_data) > 0
        except Exception as e:
            logger.error(f"更新{lottery_type}数据失败: {e}")
            return False

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
