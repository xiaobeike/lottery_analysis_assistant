"""基础分析器"""

from typing import Any, Dict, List, Optional
from collections import Counter
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    hot_numbers: List[int]
    cold_numbers: List[int]
    odd_even_ratio: str
    big_small_ratio: str
    consecutive_count: int
    sum_value: int
    sum_range: str
    avg_odd_count: float
    avg_big_count: float
    missing_stats: Dict[int, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'hot_numbers': self.hot_numbers,
            'cold_numbers': self.cold_numbers,
            'odd_even_ratio': self.odd_even_ratio,
            'big_small_ratio': self.big_small_ratio,
            'consecutive_count': self.consecutive_count,
            'sum_value': self.sum_value,
            'sum_range': self.sum_range,
            'avg_odd_count': self.avg_odd_count,
            'avg_big_count': self.avg_big_count,
            'missing_stats': self.missing_stats
        }


class BaseAnalyzer:
    """分析器基类"""
    
    # 子类需要覆盖这些属性
    BALLS_NAME = "号码"
    SMALL_THRESHOLD = 0  # 小号阈值
    MAX_BALL = 0  # 最大号码
    RED_COUNT = 0  # 红球/前区数量
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.reds = []  # 红球/前区列表
        self.blues = []  # 蓝球/后区列表
        self._parse_data()
    
    def _parse_data(self):
        """解析数据"""
        for draw in self.data:
            self.reds.append(draw.get('red_balls', draw.get('front_balls', [])))
            self.blues.append(draw.get('blue_ball', draw.get('back_balls', [])))
    
    def analyze(self) -> AnalysisResult:
        """执行分析"""
        raise NotImplementedError
    
    def _count_numbers(self, balls_list: List[List[int]]) -> Counter:
        """统计号码出现次数"""
        all_numbers = []
        for balls in balls_list:
            all_numbers.extend(balls)
        return Counter(all_numbers)
    
    def _get_hot_cold_numbers(
        self,
        counter: Counter,
        top_n: int = 10
    ) -> tuple:
        """获取热号和冷号"""
        if not counter:
            return [], []
        
        total = sum(counter.values())
        # 计算频率
        freq = {num: count / total for num, count in counter.items()}
        
        # 热号：频率最高的号码
        hot = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        hot_numbers = [num for num, _ in hot]
        
        # 冷号：频率最低的号码（排除未出现的）
        cold = sorted(freq.items(), key=lambda x: x[1])[:top_n]
        cold_numbers = [num for num, _ in cold]
        
        return hot_numbers, cold_numbers
    
    def _calculate_odd_even_ratio(self) -> str:
        """计算奇偶比例"""
        if not self.reds:
            return "0:0"
        
        odd_counts = []
        even_counts = []
        
        for balls in self.reds:
            odd = sum(1 for b in balls if b % 2 == 1)
            even = len(balls) - odd
            odd_counts.append(odd)
            even_counts.append(even)
        
        avg_odd = sum(odd_counts) / len(odd_counts)
        avg_even = sum(even_counts) / len(even_counts)
        
        return f"{avg_odd:.1f}:{avg_even:.1f}"
    
    def _calculate_big_small_ratio(self) -> str:
        """计算大小比例"""
        if not self.reds:
            return "0:0"
        
        big_counts = []
        small_counts = []
        
        for balls in self.reds:
            big = sum(1 for b in balls if b > self.SMALL_THRESHOLD)
            small = len(balls) - big
            big_counts.append(big)
            small_counts.append(small)
        
        avg_big = sum(big_counts) / len(big_counts)
        avg_small = sum(small_counts) / len(small_counts)
        
        return f"{avg_big:.1f}:{avg_small:.1f}"
    
    def _count_consecutive(self) -> int:
        """统计连号出现次数"""
        if not self.reds:
            return 0
        
        consecutive_count = 0
        
        for balls in self.reds:
            sorted_balls = sorted(balls)
            for i in range(len(sorted_balls) - 1):
                if sorted_balls[i + 1] - sorted_balls[i] == 1:
                    consecutive_count += 1
        
        return consecutive_count
    
    def _calculate_sum_stats(self) -> tuple:
        """计算和值统计"""
        if not self.reds:
            return 0, ""
        
        sums = [sum(balls) for balls in self.reds]
        avg_sum = sum(sums) / len(sums)
        
        # 和值范围分类
        if avg_sum < 80:
            range_str = "偏小"
        elif avg_sum < 120:
            range_str = "适中"
        else:
            range_str = "偏大"
        
        return int(avg_sum), range_str
    
    def _calculate_missing_stats(self) -> Dict[int, int]:
        """计算遗漏统计"""
        missing = {}
        
        # 初始化所有号码为0
        for i in range(1, self.MAX_BALL + 1):
            missing[i] = 0
        
        # 反向遍历，计算每个号码的遗漏期数
        for i, balls in enumerate(self.reds):
            for num in range(1, self.MAX_BALL + 1):
                if num not in balls:
                    missing[num] += 1
                else:
                    missing[num] = 0
        
        return missing
    
    def _get_avg_odd_count(self) -> float:
        """获取平均奇数数量"""
        if not self.reds:
            return 0.0
        
        odd_counts = [
            sum(1 for b in balls if b % 2 == 1)
            for balls in self.reds
        ]
        
        return sum(odd_counts) / len(odd_counts)
    
    def _get_avg_big_count(self) -> float:
        """获取平均大号数量"""
        if not self.reds:
            return 0.0
        
        big_counts = [
            sum(1 for b in balls if b > self.SMALL_THRESHOLD)
            for balls in self.reds
        ]
        
        return sum(big_counts) / len(big_counts)
