#!/usr/bin/env python3
"""
彩票数据分析与推荐系统主程序
Lottery Data Analysis and Recommendation System

支持双色球和大乐透的智能分析和推荐
通过企业微信机器人推送结果
"""

import argparse
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import load_config, reset_config
from src.data.fetcher import LotteryDataFetcher
from src.analysis.traditional.ssq_analyzer import SSQAnalyzer
from src.analysis.traditional.dlt_analyzer import DLTAnalyzer
from src.recommendation.generator import RecommendationGenerator
from src.notification.wechat_bot import WeChatBot
from src.notification.message_builder import MessageBuilder
from src.ai.analyzer import AIAnalyzer

# 配置日志
def setup_logging(log_file: str = None):
    """配置日志"""
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_file or f"./logs/lottery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def run_analysis(lottery_type: str, config: dict, test_mode: bool = False) -> bool:
    """运行分析流程"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"开始{lottery_type.upper()}分析...")

        # 1. 初始化数据获取器（内部使用DataSpider管理数据）
        fetcher = LotteryDataFetcher(config)
        
        # 3. 获取上一期开奖信息
        logger.info("获取上一期开奖信息...")
        previous_draw = fetcher.get_previous_draw_info(lottery_type)
        
        if not previous_draw:
            logger.error("无法获取上一期开奖信息")
            return False
        
        logger.info(f"上一期：{previous_draw.get('period', 'N/A')}，号码：{previous_draw.get('numbers', 'N/A')}")
        
        # 4. 获取历史数据用于分析（排除最新一期）
        logger.info("获取历史数据...")
        analysis_data = fetcher.get_analysis_data(lottery_type, periods=30)
        
        if not analysis_data:
            logger.error("无法获取历史数据")
            return False
        
        logger.info(f"成功获取 {len(analysis_data)} 期历史数据")
        
        # 5. 传统统计分析
        logger.info("执行传统统计分析...")
        if lottery_type == 'ssq':
            analyzer = SSQAnalyzer(analysis_data)
            blue_analysis = analyzer.analyze_blue()
        else:
            analyzer = DLTAnalyzer(analysis_data)
            blue_analysis = analyzer.analyze_back()
        
        traditional_result = analyzer.analyze()
        traditional_dict = traditional_result.to_dict()
        
        logger.info(f"热号TOP5：{traditional_dict.get('hot_numbers', [])[:5]}")
        logger.info(f"冷号TOP5：{traditional_dict.get('cold_numbers', [])[:5]}")
        logger.info(f"奇偶比：{traditional_dict.get('odd_even_ratio', 'N/A')}")
        
        # 6. AI深度分析
        ai_result = None
        ai_recommendations = None
        
        if config.get('analysis', {}).get('use_ai', True):
            logger.info("执行AI深度分析...")
            
            ai_analyzer = AIAnalyzer(config)
            ai_result = ai_analyzer.analyze(lottery_type, analysis_data)
            
            if ai_result:
                logger.info("AI分析完成")
                # 尝试生成AI推荐
                ai_recommendations = ai_analyzer.generate_recommendations(
                    lottery_type,
                    {'summary': traditional_dict.get('hot_numbers', []), 'details': ai_result.get('details', '')},
                    count=5
                )
            else:
                logger.warning("AI分析失败，将使用传统推荐")
        else:
            logger.info("AI分析已禁用")
        
        # 7. 生成推荐号码
        logger.info("生成推荐号码...")
        
        rec_generator = RecommendationGenerator(
            lottery_type, traditional_result, blue_analysis
        )
        
        recommendations = rec_generator.generate_recommendations(
            count=config.get('recommendation', {}).get('count', 5),
            strategy='mixed'
        )
        
        # 如果有AI推荐，使用AI推荐
        if ai_recommendations and isinstance(ai_recommendations, list) and len(ai_recommendations) >= 5:
            logger.info("使用AI生成的推荐号码")
            recommendations = _convert_ai_recommendations(ai_recommendations, lottery_type)
        
        top_recommendations = rec_generator.get_top_recommendations(
            recommendations,
            top_n=config.get('recommendation', {}).get('top_count', 3)
        )
        
        logger.info(f"生成 {len(recommendations)} 组推荐号码")
        
        # 8. 构建消息
        logger.info("构建消息...")
        msg_builder = MessageBuilder(lottery_type)
        message = msg_builder.build_message(
            previous_draw=previous_draw,
            traditional_analysis=traditional_dict,
            ai_analysis=ai_result,
            recommendations=recommendations,
            top_recommendations=top_recommendations
        )
        
        # 9. 发送消息
        if not test_mode:
            logger.info("发送企业微信通知...")
            webhook_url = config.get('notification', {}).get('wechat', {}).get('webhook_url', '')
            
            if not webhook_url or webhook_url.startswith('YOUR_'):
                logger.error("企业微信Webhook URL未配置")
                return False
            
            bot = WeChatBot(webhook_url)
            
            if bot.send_markdown(message):
                logger.info("消息发送成功！")
                return True
            else:
                logger.error("消息发送失败")
                return False
        else:
            # 测试模式，打印消息
            logger.info("测试模式，不发送实际消息")
            print("\n" + "="*60)
            print("消息预览：")
            print("="*60)
            print(message)
            print("="*60 + "\n")
            return True
        
    except Exception as e:
        logger.error(f"分析流程出错: {e}", exc_info=True)
        return False


def _convert_ai_recommendations(ai_recs: list, lottery_type: str) -> list:
    """转换AI推荐为标准格式"""
    from src.recommendation.generator import Recommendation
    
    recommendations = []
    
    for i, rec in enumerate(ai_recs, 1):
        try:
            if isinstance(rec, dict):
                numbers = rec.get('numbers', {})
                if lottery_type == 'ssq':
                    reds = numbers.get('reds', [])
                    blues = [numbers.get('blue', 0)]
                else:
                    reds = numbers.get('fronts', [])
                    blues = numbers.get('backs', [])
                
                reason = rec.get('reason', 'AI智能推荐')
                stars = rec.get('stars', '⭐')
                
                recommendations.append(Recommendation(
                    index=rec.get('index', i),
                    reds=reds,
                    blues=blues,
                    stars=stars,
                    reason=reason,
                    score=rec.get('score', 50.0)
                ))
        except Exception as e:
            logger.warning(f"转换AI推荐失败: {e}")
    
    return recommendations


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='彩票数据分析与推荐系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --lottery ssq          # 分析双色球
  python main.py --lottery dlt --test   # 测试模式分析大乐透
  python main.py --lottery ssq --periods 50  # 分析最近50期
        """
    )
    
    parser.add_argument(
        '--lottery', '-l',
        choices=['ssq', 'dlt'],
        required=True,
        help='彩票类型：ssq(双色球) 或 dlt(大乐透)'
    )
    
    parser.add_argument(
        '--periods', '-p',
        type=int,
        default=30,
        help='分析期数，默认30期'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='测试模式，不发送实际通知'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='./config/config.yaml',
        help='配置文件路径'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("彩票数据分析与推荐系统启动")
    logger.info(f"彩票类型: {args.lottery}")
    logger.info(f"分析期数: {args.periods}")
    logger.info(f"测试模式: {args.test}")
    logger.info("="*60)
    
    # 重置配置并加载
    reset_config()
    
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        sys.exit(1)
    
    # 临时修改分析期数
    if args.periods != 30:
        config['data']['periods'] = args.periods
    
    # 运行分析
    success = run_analysis(args.lottery, config, test_mode=args.test)
    
    if success:
        logger.info("分析完成！")
        sys.exit(0)
    else:
        logger.error("分析失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
