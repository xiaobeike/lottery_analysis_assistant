"""常量定义模块"""

from enum import Enum


class LotteryType(Enum):
    """彩票类型枚举"""
    SSQ = "ssq"  # 双色球
    DLT = "dlt"  # 大乐透


class AIProvider(Enum):
    """AI提供商枚举"""
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"


# 星期映射（1=周一, 7=周日）
WEEKDAY_MAP = {
    1: "周一",
    2: "周二", 
    3: "周三",
    4: "周四",
    5: "周五",
    6: "周六",
    7: "周日"
}

# 彩票名称
LOTTERY_NAMES = {
    "ssq": "双色球",
    "dlt": "大乐透"
}
