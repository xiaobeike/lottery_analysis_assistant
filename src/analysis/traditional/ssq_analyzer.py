"""双色球分析器"""

from typing import Any, Dict, List
from collections import Counter

from .base_analyzer import BaseAnalyzer, AnalysisResult

import logging

logger = logging.getLogger(__name__)


class SSQAnalyzer(BaseAnalyzer):
    """双色球分析器"""
    
    BALLS_NAME = "红球"
    SMALL_THRESHOLD = 16  # 红球1-16为小，17-33为大
    MAX_BALL = 33
    RED_COUNT = 6
    
    def analyze(self) -> AnalysisResult:
        """执行双色球分析"""
        if not self.data:
            return self._empty_result()
        
        try:
            # 统计红球出现次数
            red_counter = self._count_numbers(self.reds)
            
            # 热号冷号
            hot_numbers, cold_numbers = self._get_hot_cold_numbers(red_counter)
            
            # 奇偶比例
            odd_even_ratio = self._calculate_odd_even_ratio()
            
            # 大小比例
            big_small_ratio = self._calculate_big_small_ratio()
            
            # 连号统计
            consecutive_count = self._count_consecutive()
            
            # 和值统计
            sum_value, sum_range = self._calculate_sum_stats()
            
            # 遗漏统计
            missing_stats = self._calculate_missing_stats()
            
            # 平均奇数数量
            avg_odd_count = self._get_avg_odd_count()
            
            # 平均大号数量
            avg_big_count = self._get_avg_big_count()
            
            return AnalysisResult(
                hot_numbers=hot_numbers,
                cold_numbers=cold_numbers,
                odd_even_ratio=odd_even_ratio,
                big_small_ratio=big_small_ratio,
                consecutive_count=consecutive_count,
                sum_value=sum_value,
                sum_range=sum_range,
                avg_odd_count=avg_odd_count,
                avg_big_count=avg_big_count,
                missing_stats=missing_stats
            )
            
        except Exception as e:
            logger.error(f"双色球分析失败: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> AnalysisResult:
        """返回空结果"""
        return AnalysisResult(
            hot_numbers=[],
            cold_numbers=[],
            odd_even_ratio="0:0",
            big_small_ratio="0:0",
            consecutive_count=0,
            sum_value=0,
            sum_range="未知",
            avg_odd_count=0.0,
            avg_big_count=0.0,
            missing_stats={}
        )
    
    def analyze_blue(self) -> Dict[str, Any]:
        """分析蓝球"""
        if not self.blues:
            return {}
        
        blue_counter = Counter()
        for blue in self.blues:
            if isinstance(blue, list):
                blue_counter.update(blue)
            else:
                blue_counter[blue] += 1
        
        # 热号冷号
        total = sum(blue_counter.values())
        hot = sorted(blue_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        cold = sorted(blue_counter.items(), key=lambda x: x[1])[:5]
        
        # 奇偶分布
        odd_count = sum(1 for b in blue_counter if b % 2 == 1)
        even_count = len(blue_counter) - odd_count
        
        # 大小分布
        small_count = sum(1 for b in blue_counter if b <= 8)
        big_count = len(blue_counter) - small_count
        
        return {
            'hot_blue': [b for b, _ in hot],
            'cold_blue': [b for b, _ in cold],
            'odd_even': f"{odd_count}:{even_count}",
            'big_small': f"{small_count}:{big_count}"
        }
