"""大乐透分析器"""

from typing import Any, Dict, List
from collections import Counter

from .base_analyzer import BaseAnalyzer, AnalysisResult

import logging

logger = logging.getLogger(__name__)


class DLTAnalyzer(BaseAnalyzer):
    """大乐透分析器"""
    
    BALLS_NAME = "前区"
    SMALL_THRESHOLD = 17  # 前区1-17为小，18-35为大
    MAX_BALL = 35
    RED_COUNT = 5
    
    def analyze(self) -> AnalysisResult:
        """执行大乐透分析"""
        if not self.data:
            return self._empty_result()
        
        try:
            # 统计前区出现次数
            front_counter = self._count_numbers(self.reds)
            
            # 热号冷号
            hot_numbers, cold_numbers = self._get_hot_cold_numbers(front_counter)
            
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
            logger.error(f"大乐透分析失败: {e}")
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
    
    def analyze_back(self) -> Dict[str, Any]:
        """分析后区"""
        if not self.blues:
            return {}
        
        back_counter = Counter()
        for back in self.blues:
            if isinstance(back, list):
                back_counter.update(back)
            else:
                back_counter[back] += 1
        
        # 统计组合
        combos = []
        for i in range(len(self.blues)):
            if isinstance(self.blues[i], list) and len(self.blues[i]) >= 2:
                combo = tuple(sorted(self.blues[i]))
                combos.append(combo)
        
        combo_counter = Counter(combos)
        hot_combos = combo_counter.most_common(5)
        
        # 热号冷号
        total = sum(back_counter.values())
        hot = sorted(back_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        cold = sorted(back_counter.items(), key=lambda x: x[1])[:5]
        
        return {
            'hot_back': [b for b, _ in hot],
            'cold_back': [b for b, _ in cold],
            'hot_combos': [f"{c[0]}-{c[1]}" for c, _ in hot_combos],
            'total_back_count': len(back_counter)
        }
