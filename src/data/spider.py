"""500.com 数据爬虫模块"""

import re
import time
import random
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataSpider:
    """500.com 数据爬虫"""
    
    # 基础URL
    BASE_URLS = {
        'ssq': 'https://kaijiang.500.com/shtml/ssq/',
        'dlt': 'https://kaijiang.500.com/shtml/dlt/'
    }
    
    def __init__(
        self,
        data_dir: str = './data/history',
        request_delay: float = 2.0,  # 请求间隔（秒）
        max_retries: int = 3
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.request_delay = request_delay
        self.max_retries = max_retries
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _random_delay(self):
        """添加随机延迟，避免被封"""
        time.sleep(self.request_delay + random.uniform(0.5, 1.5))
    
    def _fetch_with_retry(self, url: str) -> Optional[str]:
        """带重试的请求"""
        for attempt in range(self.max_retries):
            try:
                self._random_delay()
                
                response = self.session.get(url, timeout=30)
                
                # 检查状态码
                if response.status_code == 409:
                    logger.warning(f"请求过于频繁，状态码409，尝试{attempt + 1}/{self.max_retries}")
                    time.sleep(5 * (attempt + 1))  # 递增等待时间
                    continue
                
                response.raise_for_status()
                
                # 检测编码
                if response.encoding == 'ISO-8859-1':
                    response.encoding = 'gbk'
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败，尝试{attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(3 * (attempt + 1))
        
        return None
    
    def _parse_ssq_page(self, html: str, period: str) -> Optional[Dict[str, Any]]:
        """解析双色球页面"""
        try:
            # 期号
            period_match = re.search(r'期\s+(\d+)', html)
            period = period_match.group(1) if period_match else period

            # 开奖日期 - 使用简单模式
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html)
            if date_match:
                year, month, day = date_match.groups()
                date = f"{year}-{int(month):02d}-{int(day):02d}"
            else:
                date = ''

            # 提取所有球号码（使用class="ball"模式）
            ball_pattern = r'class="[^"]*ball[^"]*"[^>]*>(\d{2})'
            all_balls = re.findall(ball_pattern, html)

            if len(all_balls) >= 7:
                # 双色球: 前6个是红球，最后1个是蓝球
                reds = sorted([int(b) for b in all_balls[:6]])
                blue = int(all_balls[6])
            elif len(all_balls) >= 6:
                # 只找到红球
                reds = sorted([int(b) for b in all_balls[:6]])
                blue = 0
            else:
                logger.warning(f"双色球{period}球数量不足: {len(all_balls)}")
                return None

            # 销售额 - 尝试多种模式
            sale_amount = '0'
            sale_patterns = [
                r'本期销量.*?>([0-9,]+)元',
                r'销售额.*?>([0-9,]+)元',
                r'本期销量[：:]*([0-9,]+)',
                r'销售额[：:]*([0-9,]+)',
            ]
            for pattern in sale_patterns:
                sale_match = re.search(pattern, html)
                if sale_match:
                    sale_amount = sale_match.group(1).replace(',', '')
                    break

            # 奖池 - 尝试多种模式
            pool_amount = '0'
            pool_patterns = [
                r'奖池滚存.*?>([0-9,]+)元',
                r'奖池.*?>([0-9,]+)元',
                r'奖池资金[：:]*([0-9,]+)',
                r'滚存[：:]*([0-9,]+)',
            ]
            for pattern in pool_patterns:
                pool_match = re.search(pattern, html)
                if pool_match:
                    pool_amount = pool_match.group(1).replace(',', '')
                    break

            return {
                'lottery_type': 'ssq',
                'period': period,
                'date': date,
                'red_balls': reds,
                'blue_ball': blue,
                'sale_amount': int(sale_amount) if sale_amount.isdigit() else 0,
                'pool_amount': int(pool_amount) if pool_amount.isdigit() else 0
            }

        except Exception as e:
            logger.error(f"解析双色球{period}失败: {e}")
            return None
    
    def _parse_dlt_page(self, html: str, period: str) -> Optional[Dict[str, Any]]:
        """解析大乐透页面"""
        try:
            # 期号
            period_match = re.search(r'期\s+(\d+)', html)
            period = period_match.group(1) if period_match else period

            # 开奖日期 - 使用简单模式
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html)
            if date_match:
                year, month, day = date_match.groups()
                date = f"{year}-{int(month):02d}-{int(day):02d}"
            else:
                date = ''

            # 提取所有球号码（使用class="ball"模式）
            ball_pattern = r'class="[^"]*ball[^"]*"[^>]*>(\d{2})'
            all_balls = re.findall(ball_pattern, html)

            if len(all_balls) >= 7:
                # 大乐透: 前5个是前区，后2个是后区
                fronts = sorted([int(b) for b in all_balls[:5]])
                backs = sorted([int(b) for b in all_balls[5:7]])
            elif len(all_balls) >= 5:
                # 只找到前区
                fronts = sorted([int(b) for b in all_balls[:5]])
                backs = []
            else:
                logger.warning(f"大乐透{period}球数量不足: {len(all_balls)}")
                return None

            # 销售额 - 尝试多种模式
            sale_amount = '0'
            sale_patterns = [
                (r'本期全国销售金额.*?>([0-9.]+)亿', lambda m: str(int(float(m.group(1)) * 100000000))),
                (r'本期销量.*?>([0-9,]+)元', lambda m: m.group(1).replace(',', '')),
                (r'销售额.*?>([0-9,]+)元', lambda m: m.group(1).replace(',', '')),
                (r'本期销量[：:]*([0-9,]+)', lambda m: m.group(1).replace(',', '')),
                (r'销售额[：:]*([0-9,]+)', lambda m: m.group(1).replace(',', '')),
            ]
            for pattern, converter in sale_patterns:
                sale_match = re.search(pattern, html)
                if sale_match:
                    try:
                        sale_amount = converter(sale_match)
                        break
                    except (ValueError, AttributeError):
                        continue

            # 奖池 - 尝试多种模式
            pool_amount = '0'
            pool_patterns = [
                (r'奖池滚存.*?>([0-9.]+)亿', lambda m: str(int(float(m.group(1)) * 100000000))),
                (r'奖池.*?>([0-9,]+)元', lambda m: m.group(1).replace(',', '')),
                (r'奖池资金[：:]*([0-9,]+)', lambda m: m.group(1).replace(',', '')),
                (r'滚存[：:]*([0-9,]+)', lambda m: m.group(1).replace(',', '')),
            ]
            for pattern, converter in pool_patterns:
                pool_match = re.search(pattern, html)
                if pool_match:
                    try:
                        pool_amount = converter(pool_match)
                        break
                    except (ValueError, AttributeError):
                        continue

            return {
                'lottery_type': 'dlt',
                'period': period,
                'date': date,
                'front_balls': fronts,
                'back_balls': backs,
                'sale_amount': int(sale_amount) if sale_amount.isdigit() else 0,
                'pool_amount': int(pool_amount) if pool_amount.isdigit() else 0
            }

        except Exception as e:
            logger.error(f"解析大乐透{period}失败: {e}")
            return None
    
    def fetch_single(self, lottery_type: str, period: str) -> Optional[Dict[str, Any]]:
        """获取单期数据"""
        base_url = self.BASE_URLS.get(lottery_type)
        if not base_url:
            logger.error(f"不支持的彩票类型: {lottery_type}")
            return None
        
        url = f"{base_url}{period}.shtml"
        html = self._fetch_with_retry(url)
        
        if not html:
            logger.error(f"获取{lottery_type}{period}失败")
            return None
        
        if lottery_type == 'ssq':
            return self._parse_ssq_page(html, period)
        else:
            return self._parse_dlt_page(html, period)
    
    def fetch_history(self, lottery_type: str, periods: int = 30) -> List[Dict[str, Any]]:
        """获取历史数据"""
        history = []
        base_url = self.BASE_URLS.get(lottery_type)

        if not base_url:
            logger.error(f"不支持的彩票类型: {lottery_type}")
            return history

        # 获取最新期号
        latest_period = self.get_latest_period(lottery_type)
        if not latest_period:
            logger.error(f"获取{lottery_type}最新期号失败")
            return history

        logger.info(f"获取{lottery_type}最新期号: {latest_period}")
        
        # 向前获取指定期数
        for i in range(periods):
            try:
                period_num = int(latest_period) - i
                period_str = str(period_num)
                
                url = f"{base_url}{period_str}.shtml"
                html = self._fetch_with_retry(url)
                
                if html:
                    if lottery_type == 'ssq':
                        data = self._parse_ssq_page(html, period_str)
                    else:
                        data = self._parse_dlt_page(html, period_str)
                    
                    if data:
                        history.append(data)
                        logger.info(f"获取{lottery_type}{period_str}成功: {data.get('red_balls', data.get('front_balls', []))}")
            
            except Exception as e:
                logger.warning(f"获取{lottery_type}{period_str}失败: {e}")
                continue
        
        return history
    
    def save_history(self, lottery_type: str, data: List[Dict[str, Any]]):
        """保存历史数据"""
        file_path = self.data_dir / f"{lottery_type}.json"
        
        save_data = {
            'updated_at': datetime.now().isoformat(),
            'count': len(data),
            'data': data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"保存{lottery_type}数据{len(data)}条到{file_path}")
    
    def load_history(self, lottery_type: str) -> List[Dict[str, Any]]:
        """加载历史数据"""
        file_path = self.data_dir / f"{lottery_type}.json"
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('data', [])
        except Exception as e:
            logger.error(f"加载{lottery_type}历史数据失败: {e}")
            return []
    
    def update_to_latest(self, lottery_type: str) -> List[Dict[str, Any]]:
        """更新到最新一期（添加新数据，删除最老数据，保持30条）"""
        # 加载现有数据
        existing_data = self.load_history(lottery_type)
        
        # 获取最新期号
        latest_period = self.get_latest_period(lottery_type)
        if not latest_period:
            logger.error(f"无法获取{lottery_type}最新期号")
            return existing_data
        
        # 检查是否已有最新数据
        if existing_data and existing_data[0].get('period') == latest_period:
            logger.info(f"{lottery_type}数据已是最新，无需更新")
            return existing_data
        
        # 获取最新一期数据
        new_data = self.fetch_single(lottery_type, latest_period)
        if not new_data:
            logger.error(f"获取{lottery_type}{latest_period}失败")
            return existing_data
        
        # 添加新数据，删除最老数据
        updated_data = [new_data]
        for item in existing_data[:29]:  # 保留前29条
            updated_data.append(item)
        
        # 保存
        self.save_history(lottery_type, updated_data)
        
        logger.info(f"更新{lottery_type}数据完成，共{len(updated_data)}条")
        return updated_data
    
    def get_latest_period(self, lottery_type: str) -> Optional[str]:
        """获取最新期号"""
        base_url = self.BASE_URLS.get(lottery_type)
        if not base_url:
            return None

        html = self._fetch_with_retry(base_url)
        if not html:
            return None

        # 查找最新期号 - 使用更具体的模式
        type_patterns = {
            'ssq': r'/ssq/(\d{5,8})\.shtml',
            'dlt': r'/dlt/(\d{5,8})\.shtml',
        }

        pattern = type_patterns.get(lottery_type)
        if not pattern:
            return None

        matches = re.findall(pattern, html)
        if matches:
            # 返回最大的期号
            return str(max(matches, key=lambda x: int(x) if x.isdigit() else 0))

        return None
    
    def initialize_data(self, lottery_type: str, periods: int = 30) -> List[Dict[str, Any]]:
        """初始化数据（首次运行）"""
        # 尝试加载现有数据
        existing_data = self.load_history(lottery_type)
        if existing_data:
            logger.info(f"加载{lottery_type}现有数据{len(existing_data)}条")
            return existing_data
        
        # 获取历史数据
        logger.info(f"首次获取{lottery_type}最近{periods}期数据...")
        history = self.fetch_history(lottery_type, periods)
        
        if history:
            self.save_history(lottery_type, history)
            logger.info(f"初始化{lottery_type}数据完成，共{len(history)}条")
        else:
            logger.error(f"初始化{lottery_type}数据失败")
        
        return history
