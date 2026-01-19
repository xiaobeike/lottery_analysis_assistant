"""推荐生成器模块"""

import random
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

from src.analysis.traditional.base_analyzer import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """推荐号码"""
    index: int
    reds: List[int]
    blues: List[int]
    stars: str
    reason: str
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'reds': self.reds,
            'blues': self.blues,
            'stars': self.stars,
            'reason': self.reason,
            'score': self.score
        }


class RecommendationGenerator:
    """推荐号码生成器"""
    
    def __init__(
        self,
        lottery_type: str,
        analysis_result: AnalysisResult,
        blue_analysis: Dict[str, Any] = None
    ):
        self.lottery_type = lottery_type
        self.analysis = analysis_result
        self.blue_analysis = blue_analysis or {}
        
        # 设置参数
        if lottery_type == 'ssq':
            self.red_range = (1, 33)
            self.blue_range = (1, 16)
            self.red_count = 6
            self.blue_count = 1
        else:
            self.red_range = (1, 35)
            self.blue_range = (1, 12)
            self.red_count = 5
            self.blue_count = 2
        
        self.hot_numbers = analysis_result.hot_numbers
        self.cold_numbers = analysis_result.cold_numbers
    
    def generate_recommendations(
        self,
        count: int = 5,
        strategy: str = "mixed"
    ) -> List[Recommendation]:
        """生成推荐号码"""
        recommendations = []
        
        strategies = {
            'hot_first': self._generate_hot_first,
            'balanced': self._generate_balanced,
            'mixed': self._generate_mixed_strategy,
            'random': self._generate_random_optimized
        }
        
        generator_func = strategies.get(strategy, strategies['mixed'])
        
        for i in range(count):
            try:
                rec = generator_func(i + 1)
                if rec:
                    recommendations.append(rec)
            except Exception as e:
                logger.error(f"生成第{i+1}组推荐失败: {e}")
        
        return recommendations
    
    def _generate_hot_first(self, index: int) -> Optional[Recommendation]:
        """热号优先策略"""
        # 从热号中选择红球
        if len(self.hot_numbers) < self.red_count:
            available = list(range(self.red_range[0], self.red_range[1] + 1))
        else:
            available = self.hot_numbers[:20]
        
        reds = sorted(random.sample(available, self.red_count))
        
        # 蓝球/后区选择
        blues = self._select_blue()
        
        # 评分
        score = self._calculate_score(reds, blues, 'hot_first')
        
        return Recommendation(
            index=index,
            reds=reds,
            blues=blues,
            stars="⭐⭐⭐" if index <= 3 else "⭐",
            reason=self._generate_reason(reds, blues, 'hot_first'),
            score=score
        )
    
    def _generate_balanced(self, index: int) -> Optional[Recommendation]:
        """平衡策略"""
        # 热号和冷号混合
        hot_count = max(1, self.red_count // 2)
        cold_count = self.red_count - hot_count
        
        if len(self.hot_numbers) < hot_count:
            hot_count = len(self.hot_numbers)
            cold_count = self.red_count - hot_count
        
        # 选择热号
        available_hot = [n for n in self.hot_numbers if n not in []]
        hot_selected = random.sample(available_hot, min(hot_count, len(available_hot)))
        
        # 选择冷号（避开过热号码）
        cold_selected = []
        if cold_count > 0 and len(self.cold_numbers) >= cold_count:
            available_cold = [n for n in self.cold_numbers if n not in hot_selected]
            if available_cold:
                cold_selected = random.sample(available_cold, min(cold_count, len(available_cold)))
        
        # 补足数量
        reds = hot_selected + cold_selected
        while len(reds) < self.red_count:
            remaining = list(range(self.red_range[0], self.red_range[1] + 1))
            remaining = [n for n in remaining if n not in reds]
            if remaining:
                reds.append(random.choice(remaining))
            else:
                break
        
        reds = sorted(reds[:self.red_count])
        
        # 蓝球/后区
        blues = self._select_blue()
        
        score = self._calculate_score(reds, blues, 'balanced')
        
        return Recommendation(
            index=index,
            reds=reds,
            blues=blues,
            stars="⭐⭐⭐" if index <= 3 else "⭐",
            reason=self._generate_reason(reds, blues, 'balanced'),
            score=score
        )
    
    def _generate_mixed_strategy(self, index: int) -> Optional[Recommendation]:
        """混合策略"""
        strategies = ['hot_first', 'balanced']
        chosen = random.choice(strategies)
        
        return self._generate_hot_first(index) if chosen == 'hot_first' else self._generate_balanced(index)
    
    def _generate_random_optimized(self, index: int) -> Optional[Recommendation]:
        """随机优化策略"""
        # 随机生成，但验证统计规律
        max_attempts = 100
        
        for _ in range(max_attempts):
            reds = sorted(random.sample(
                list(range(self.red_range[0], self.red_range[1] + 1)),
                self.red_count
            ))
            
            # 验证奇偶比
            odd_count = sum(1 for r in reds if r % 2 == 1)
            if self.red_count in [5, 6] and odd_count not in [2, 3, 4]:
                continue
            
            # 验证大小比
            big_count = sum(1 for r in reds if r > self.red_range[0] + (self.red_range[1] - self.red_range[0]) // 2)
            if self.red_count in [5, 6] and big_count not in [2, 3, 4]:
                continue
            
            # 验证和值
            red_sum = sum(reds)
            if self.red_range[1] == 33:  # 双色球
                if red_sum < 70 or red_sum > 140:
                    continue
            else:  # 大乐透
                if red_sum < 50 or red_sum > 110:
                    continue
            
            # 验证通过
            break
        
        blues = self._select_blue()
        
        score = self._calculate_score(reds, blues, 'random')
        
        return Recommendation(
            index=index,
            reds=reds,
            blues=blues,
            stars="⭐⭐⭐" if index <= 3 else "⭐",
            reason=self._generate_reason(reds, blues, 'random_optimized'),
            score=score
        )
    
    def _select_blue(self) -> List[int]:
        """选择蓝球/后区"""
        if self.lottery_type == 'ssq':
            # 单个蓝球
            if self.blue_analysis.get('hot_blue'):
                candidates = self.blue_analysis['hot_blue'][:5]
                return [random.choice(candidates)]
            else:
                return [random.randint(1, 16)]
        else:
            # 两个后区
            if self.blue_analysis.get('hot_back'):
                candidates = self.blue_analysis['hot_back'][:8]
            else:
                candidates = list(range(1, 13))
            
            if len(candidates) >= 2:
                back = sorted(random.sample(candidates, 2))
            else:
                back = sorted(random.sample(list(range(1, 13)), 2))
            
            return back
    
    def _calculate_score(
        self,
        reds: List[int],
        blues: List[int],
        strategy: str
    ) -> float:
        """计算推荐分数"""
        score = 0.0
        
        # 热号数量
        hot_count = sum(1 for r in reds if r in self.hot_numbers[:15])
        score += hot_count * 10
        
        # 奇偶平衡
        odd_count = sum(1 for r in reds if r % 2 == 1)
        if self.red_count in [5, 6]:
            if 2 <= odd_count <= 4:
                score += 15
        
        # 大小平衡
        big_count = sum(1 for r in reds if r > self.red_range[0] + (self.red_range[1] - self.red_range[0]) // 2)
        if self.red_count in [5, 6]:
            if 2 <= big_count <= 4:
                score += 15
        
        # 连号检测
        has_consecutive = any(
            reds[i+1] - reds[i] == 1
            for i in range(len(reds) - 1)
        )
        if has_consecutive:
            score += 10
        
        return min(score, 100)
    
    def _generate_reason(
        self,
        reds: List[int],
        blues: List[int],
        strategy: str
    ) -> str:
        """生成推荐理由"""
        reasons = []
        
        hot_count = sum(1 for r in reds if r in self.hot_numbers[:10])
        if hot_count >= 3:
            reasons.append("热号组合")
        
        odd_count = sum(1 for r in reds if r % 2 == 1)
        if odd_count == self.red_count // 2:
            reasons.append("奇偶均衡")
        
        big_count = sum(1 for r in reds if r > self.red_range[0] + (self.red_range[1] - self.red_range[0]) // 2)
        if big_count == self.red_count // 2:
            reasons.append("大小均衡")
        
        has_consecutive = any(
            reds[i+1] - reds[i] == 1
            for i in range(len(reds) - 1)
        )
        if has_consecutive:
            reasons.append("含连号")
        
        if strategy == 'hot_first':
            reasons.append("热号优先")
        elif strategy == 'balanced':
            reasons.append("平衡组合")
        elif strategy == 'random_optimized':
            reasons.append("随机优化")
        
        return "，".join(reasons) if reasons else "综合推荐"
    
    def get_top_recommendations(
        self,
        recommendations: List[Recommendation],
        top_n: int = 3
    ) -> List[Recommendation]:
        """获取最推荐的号码组"""
        sorted_recs = sorted(recommendations, key=lambda x: x.score, reverse=True)
        return sorted_recs[:top_n]
