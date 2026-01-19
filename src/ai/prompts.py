"""AI提示词模板"""

from typing import Dict, Any, List


class PromptTemplates:
    """提示词模板"""
    
    # 彩票名称映射
    LOTTERY_NAMES = {
        'ssq': '双色球',
        'dlt': '大乐透'
    }
    
    @staticmethod
    def build_analysis_prompt(
        lottery_type: str,
        historical_data: List[Dict[str, Any]]
    ) -> str:
        """构建分析提示词"""
        lottery_name = PromptTemplates.LOTTERY_NAMES.get(lottery_type, lottery_type)
        
        data_summary = PromptTemplates._summarize_data(historical_data, lottery_type)
        
        return f"""
你是一个专业的彩票数据分析专家。请分析以下{lottery_name}历史数据，并提供深度分析报告。

## 历史数据摘要（最近30期）
{data_summary}

## 需要分析的内容

请从以下维度进行深度分析：

1. **热号分析**：统计出现频率最高的号码（TOP10），分析其出现规律
2. **冷号分析**：统计出现频率最低的号码（TOP10），分析其遗漏趋势
3. **奇偶比例分析**：奇数和偶数的分布比例，分析趋势变化
4. **大小比例分析**：大号和小号的分布比例（双色球小号1-16，大号17-33；大乐透前区小号1-17，大号18-35）
5. **区间分布分析**：号码在不同区间的分布情况
6. **连号模式分析**：连续号码出现的频率和模式
7. **和值分析**：号码总和的变化趋势和范围
8. **后区分析**（大乐透适用）：后区两个号码的组合规律
9. **蓝球分析**（双色球适用）：蓝球的奇偶、大小分布
10. **趋势预测**：基于历史数据，预测下一期的可能趋势

## 输出要求

1. 请用中文回复
2. 分析要专业、深入
3. 提供具体的号码推荐和理由
4. 格式清晰，便于阅读

请开始分析：
"""

    @staticmethod
    def build_recommendation_prompt(
        lottery_type: str,
        analysis_results: Dict[str, Any],
        count: int = 5
    ) -> str:
        """构建推荐提示词"""
        lottery_name = PromptTemplates.LOTTERY_NAMES.get(lottery_type, lottery_type)
        
        return f"""
基于以下{lottery_name}分析结果，请生成{count}组推荐号码：

## 分析结果摘要
{analysis_results.get('summary', '无摘要数据')}

## 分析详情
{analysis_results.get('details', '无详情数据')}

## 生成要求

1. 生成{count}组不同的号码组合
2. 每组号码需要包含：
   - 完整的号码（红球/前区 + 蓝球/后区）
   - 详细推荐理由（为什么选择这组号码）
   - 推荐等级（⭐⭐⭐最推荐，⭐⭐次推荐，⭐参考推荐）
3. 推荐要基于统计分析结果
4. 考虑热号、冷号、奇偶比、大小比等因素
5. 确保号码组合的多样性

## 输出格式

请以JSON格式返回：

```json
{{
  "recommendations": [
    {{
      "index": 1,
      "numbers": {{
        "reds": [号码列表] 或 "fronts": [号码列表],
        "blue": 蓝球号码 或 "backs": [后区列表]
      }},
      "reason": "推荐理由",
      "stars": "⭐⭐⭐"
    }}
  ],
  "top_recommendations": [1, 2, 3],
  "analysis_summary": "简要分析说明"
}}
```

请生成推荐：
"""

    @staticmethod
    def _summarize_data(
        data: List[Dict[str, Any]],
        lottery_type: str
    ) -> str:
        """总结数据为简洁格式"""
        if not data:
            return "无数据"
        
        summary_lines = []
        
        # 显示最近10期的号码
        summary_lines.append("最近10期开奖号码：")
        for draw in data[:10]:
            period = draw.get('period', '')
            if lottery_type == 'ssq':
                reds = draw.get('red_balls', [])
                blue = draw.get('blue_ball', 0)
                numbers = f"红球: {' '.join(map(str, reds))} | 蓝球: {blue}"
            else:
                fronts = draw.get('front_balls', [])
                backs = draw.get('back_balls', [])
                numbers = f"前区: {' '.join(map(str, fronts))} | 后区: {' '.join(map(str, backs))}"
            
            summary_lines.append(f"  {period}: {numbers}")
        
        return '\n'.join(summary_lines)
