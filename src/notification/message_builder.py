"""消息构建器模块"""

from typing import Any, Dict, List
from datetime import datetime
import logging

from src.recommendation.generator import Recommendation

logger = logging.getLogger(__name__)


class MessageBuilder:
    """消息构建器"""
    
    def __init__(self, lottery_type: str):
        self.lottery_type = lottery_type
        self.lottery_name = "双色球" if lottery_type == "ssq" else "大乐透"
    
    def build_message(
        self,
        previous_draw: Dict[str, Any],
        traditional_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        recommendations: List[Recommendation],
        top_recommendations: List[Recommendation]
    ) -> str:
        """构建完整消息"""
        
        message = f"# 🤖 AI智能分析 - {self.lottery_name}第{previous_draw.get('period', '????')}期\n\n"
        
        # 上一期开奖信息
        message += self._build_previous_draw_section(previous_draw)
        
        # 传统统计分析
        message += self._build_traditional_section(traditional_analysis)
        
        # AI深度分析
        if ai_analysis:
            message += self._build_ai_section(ai_analysis)
        
        # 推荐号码
        message += self._build_recommendations_section(
            recommendations, top_recommendations
        )
        
        # 分析说明
        message += self._build_analysis_note(previous_draw)
        
        # 免责声明
        message += self._build_disclaimer()
        
        return message
    
    def _build_previous_draw_section(self, previous_draw: Dict[str, Any]) -> str:
        """构建上一期开奖信息"""
        message = "## 📅 上一期开奖信息\n\n"
        message += f"- **期号**：{previous_draw.get('period', '暂无')}\n"
        message += f"- **开奖号码**：{previous_draw.get('numbers', '暂无')}\n"
        
        open_time = previous_draw.get('open_time', '')
        if open_time:
            try:
                dt = datetime.fromisoformat(open_time.replace('Z', '+08:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                message += f"- **开奖时间**：{formatted_time}\n"
            except:
                message += f"- **开奖时间**：{open_time}\n"
        
        message += f"- **开奖时间**：{previous_draw.get('draw_time', '21:15')}\n\n"
        
        return message
    
    def _build_traditional_section(self, analysis: Dict[str, Any]) -> str:
        """构建传统统计分析"""
        message = "## 📊 传统统计分析\n\n"
        
        # 热号
        hot = analysis.get('hot_numbers', [])[:10]
        message += f"- **热号TOP10**：{', '.join(map(str, hot)) if hot else '暂无数据'}\n"
        
        # 冷号
        cold = analysis.get('cold_numbers', [])[:10]
        message += f"- **冷号TOP10**：{', '.join(map(str, cold)) if cold else '暂无数据'}\n"
        
        # 奇偶比
        odd_even = analysis.get('odd_even_ratio', '0:0')
        message += f"- **平均奇偶比**：{odd_even}\n"
        
        # 大小比
        big_small = analysis.get('big_small_ratio', '0:0')
        message += f"- **平均大小比**：{big_small}\n"
        
        # 和值
        sum_value = analysis.get('sum_value', 0)
        sum_range = analysis.get('sum_range', '')
        message += f"- **平均和值**：{sum_value}（{sum_range}）\n"
        
        # 连号
        consecutive = analysis.get('consecutive_count', 0)
        message += f"- **近期连号数**：{consecutive}\n\n"
        
        return message
    
    def _build_ai_section(self, ai_result: Dict[str, Any]) -> str:
        """构建AI分析部分"""
        message = "## 🧠 AI深度分析\n\n"
        
        raw_result = ai_result.get('raw_result', '')
        
        # 提取AI分析的关键内容
        if raw_result:
            # 取前1000字符作为AI分析摘要
            summary = raw_result[:1000]
            if len(raw_result) > 1000:
                summary += "...\n\n> AI分析内容较长，以上为摘要"
            else:
                summary += "\n"
            
            message += f"> {summary}\n\n"
        else:
            message += "- AI分析已完成\n\n"
        
        return message
    
    def _build_recommendations_section(
        self,
        recommendations: List[Recommendation],
        top_recommendations: List[Recommendation]
    ) -> str:
        """构建推荐号码部分"""
        message = "## 💡 AI智能推荐\n\n"
        
        top_indices = set(rec.index for rec in top_recommendations)
        
        # 先显示推荐的3组（按评分排序）
        top_sorted = sorted(top_recommendations, key=lambda x: x.score, reverse=True)
        message += "**🎯 最推荐（按评分排序）：**\n\n"
        for i, rec in enumerate(top_sorted, 1):
            numbers_str = self._format_numbers(rec)
            message += f"### ⭐⭐⭐ 第{rec.index}组：{numbers_str}\n"
            message += f"📝 **推荐理由**：{rec.reason}\n"
            message += f"📊 **推荐评分**：{rec.score:.1f}/100\n\n"
        
        # 再显示参考的2组
        other_recommendations = [r for r in recommendations if r.index not in top_indices]
        if other_recommendations:
            message += "**📌 参考推荐：**\n\n"
            for rec in other_recommendations:
                numbers_str = self._format_numbers(rec)
                message += f"### ⭐ 第{rec.index}组：{numbers_str}\n"
                message += f"📝 **推荐理由**：{rec.reason}\n"
                message += f"📊 **推荐评分**：{rec.score:.1f}/100\n\n"
        
        # 添加汇总表格（重新排序：推荐在前，参考在后）
        sorted_for_table = top_sorted + other_recommendations
        message += self._build_summary_table(sorted_for_table, top_recommendations)
        
        return message
    
    def _format_numbers(self, rec: Recommendation) -> str:
        """格式化号码字符串"""
        if self.lottery_type == 'ssq':
            return f"{' '.join(map(str, rec.reds))} | {rec.blues[0]}"
        else:
            return f"{' '.join(map(str, rec.reds))} | {' '.join(map(str, rec.blues))}"
    
    def _build_summary_table(
        self,
        recommendations: List[Recommendation],
        top_recommendations: List[Recommendation]
    ) -> str:
        """构建简洁的汇总表格（便于复制和截图）"""
        message = "## 📋 推荐号码汇总\n\n"
        
        # 使用简单格式，兼容性好
        message += "```\n"
        message += "推荐   号码                           评分\n"
        message += "----------------------------------------\n"
        
        top_indices = [rec.index for rec in top_recommendations]
        
        for rec in recommendations:
            # 格式化号码
            if self.lottery_type == 'ssq':
                numbers = f"{' '.join(map(str, rec.reds))} | {rec.blues[0]}"
            else:
                numbers = f"{' '.join(map(str, rec.reds))} | {' '.join(map(str, rec.blues))}"
            
            # 推荐标记
            if rec.index in top_indices:
                marker = "[推荐]"
            elif rec.index <= 3:
                marker = "[不错]"
            else:
                marker = "[普通]"
            
            # 格式化行
            message += f"{marker}第{rec.index:>2}组  {numbers:<22} {rec.score:>5.1f}\n"
        
        message += "```\n\n"
        
        # 特别提示 - 简化版
        top_sorted = sorted(top_indices)
        message += f"🎯 **最推荐：第 {top_sorted[0]}, {top_sorted[1]}, {top_sorted[2]} 组**\n\n"
        
        return message
    
    def _build_analysis_note(self, previous_draw: Dict[str, Any]) -> str:
        """构建分析说明"""
        message = "## 📈 分析说明\n\n"
        
        draw_time = previous_draw.get('draw_time', '21:00')
        message += f"- 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}（开奖前{draw_time}）\n"
        message += "- 分析基于最近30期历史数据\n"
        message += "- 结合传统统计和AI智能分析\n"
        message += "- 前3组为最推荐组合\n\n"
        
        return message
    
    def _build_disclaimer(self) -> str:
        """构建免责声明"""
        return """## ⚠️ 重要提示

- 🤖 本分析由AI智能生成，仅供参考
- 🎲 彩票具有随机性，请理性购彩
- 💰 请理性投注，量力而行
- 📅 实际开奖时间：今晚21:15

---
*分析仅供参考，不构成任何购彩建议*
"""
