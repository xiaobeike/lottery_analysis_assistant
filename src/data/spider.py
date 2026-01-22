"""500.com 数据爬虫模块"""

import re
import time
import random
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class DataSpider:
    """500.com 数据爬虫"""

    # 使用 datachart.500.com 的 API（更稳定）
    API_URLS = {
        'ssq': 'https://datachart.500.com/ssq/history/newinc/history.php',
        'dlt': 'https://datachart.500.com/dlt/history/newinc/history.php'
    }

    # 基础URL（用于获取最新期号）
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

    def _parse_ssq_table(self, html: str) -> List[Dict[str, Any]]:
        """解析双色球表格数据（datachart.500.com格式）"""
        data_list = []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'id': 'tablelist'})

            if not table:
                logger.warning("未找到双色球表格")
                return data_list

            rows = table.find_all('tr')

            # 跳过表头行（前2行）
            for row in rows[2:]:
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue

                try:
                    # 解析数据
                    period = cells[0].get_text(strip=True)

                    # 跳过汇总行
                    if not period.isdigit():
                        continue

                    # 红球 (第2-7列)
                    reds = []
                    for i in range(1, 7):
                        ball_text = cells[i].get_text(strip=True)
                        if ball_text.isdigit():
                            reds.append(int(ball_text))

                    if len(reds) != 6:
                        continue

                    # 蓝球 (第8列)
                    blue_text = cells[7].get_text(strip=True)
                    blue = int(blue_text) if blue_text.isdigit() else 0

                    # 销售额 (倒数第3列)
                    sale_text = cells[-3].get_text(strip=True).replace(',', '')
                    sale_amount = int(sale_text) if sale_text.isdigit() else 0

                    # 开奖日期 (最后一列)
                    date_text = cells[-1].get_text(strip=True)
                    # 格式: 2026-01-20
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                    date = date_match.group(1) if date_match else ''

                    data_list.append({
                        'lottery_type': 'ssq',
                        'period': period,
                        'date': date,
                        'red_balls': sorted(reds),
                        'blue_ball': blue,
                        'sale_amount': sale_amount,
                        'pool_amount': 0
                    })

                except (ValueError, IndexError) as e:
                    logger.warning(f"解析双色球行数据失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析双色球表格失败: {e}")

        return data_list

    def _parse_dlt_table(self, html: str) -> List[Dict[str, Any]]:
        """解析大乐透表格数据（datachart.500.com格式）"""
        data_list = []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'id': 'tablelist'})

            if not table:
                logger.warning("未找到大乐透表格")
                return data_list

            rows = table.find_all('tr')

            # 跳过表头行（前2行）
            for row in rows[2:]:
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue

                try:
                    # 解析数据
                    period = cells[0].get_text(strip=True)

                    # 跳过汇总行
                    if not period.isdigit():
                        continue

                    # 前区 (第2-6列)
                    fronts = []
                    for i in range(1, 6):
                        ball_text = cells[i].get_text(strip=True)
                        if ball_text.isdigit():
                            fronts.append(int(ball_text))

                    if len(fronts) != 5:
                        continue

                    # 后区 (第7-8列)
                    backs = []
                    for i in range(6, 8):
                        ball_text = cells[i].get_text(strip=True)
                        if ball_text.isdigit():
                            backs.append(int(ball_text))

                    if len(backs) != 2:
                        continue

                    # 销售额 (倒数第3列)
                    sale_text = cells[-3].get_text(strip=True).replace(',', '')
                    sale_amount = int(sale_text) if sale_text.isdigit() else 0

                    # 开奖日期 (最后一列)
                    date_text = cells[-1].get_text(strip=True)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                    date = date_match.group(1) if date_match else ''

                    data_list.append({
                        'lottery_type': 'dlt',
                        'period': period,
                        'date': date,
                        'front_balls': sorted(fronts),
                        'back_balls': sorted(backs),
                        'sale_amount': sale_amount,
                        'pool_amount': 0
                    })

                except (ValueError, IndexError) as e:
                    logger.warning(f"解析大乐通行数据失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析大乐透表格失败: {e}")

        return data_list
    
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
        """使用 API 获取历史数据（一次请求获取全部数据）"""
        api_url = self.API_URLS.get(lottery_type)
        if not api_url:
            logger.error(f"不支持的彩票类型: {lottery_type}")
            return []

        # 先获取最新期号
        latest_period = self.get_latest_period(lottery_type)
        if not latest_period:
            logger.error(f"获取{lottery_type}最新期号失败")
            return []

        # 计算起始期号
        start_period = int(latest_period) - periods + 1

        # 构建 API URL
        url = f"{api_url}?start={start_period}&end={latest_period}"
        logger.info(f"请求{lottery_type}历史数据: {url}")

        # 发送请求
        html = self._fetch_with_retry(url)
        if not html:
            logger.error(f"获取{lottery_type}历史数据失败")
            return []

        # 解析数据
        if lottery_type == 'ssq':
            history = self._parse_ssq_table(html)
        else:
            history = self._parse_dlt_table(html)

        # 按期号倒序（最新在前）
        history.sort(key=lambda x: int(x.get('period', 0)), reverse=True)

        logger.info(f"成功解析{lottery_type}{len(history)}期数据")
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
        existing_data = self.load_history(lottery_type)

        latest_period = self.get_latest_period(lottery_type)
        if not latest_period:
            logger.error(f"无法获取{lottery_type}最新期号")
            return existing_data

        # 检查是否已有最新数据
        if existing_data and existing_data[0].get('period') == latest_period:
            logger.info(f"{lottery_type}数据已是最新，无需更新")
            return existing_data

        logger.info(f"获取{lottery_type}最新一期数据...")

        # 获取最新一期的数据
        api_url = self.API_URLS.get(lottery_type)
        if not api_url:
            return existing_data

        # 只请求最新1期
        url = f"{api_url}?start={latest_period}&end={latest_period}"
        html = self._fetch_with_retry(url)

        if not html:
            logger.error(f"获取{lottery_type}最新数据失败")
            return existing_data

        # 解析最新数据
        if lottery_type == 'ssq':
            new_data_list = self._parse_ssq_table(html)
        else:
            new_data_list = self._parse_dlt_table(html)

        if not new_data_list:
            logger.error(f"解析{lottery_type}最新数据失败")
            return existing_data

        new_data = new_data_list[0]

        # 添加新数据到最前面，删除最后一条，保持30条
        updated_data = [new_data] + existing_data[:29]

        self.save_history(lottery_type, updated_data)
        logger.info(f"更新{lottery_type}数据完成，共{len(updated_data)}条，最新期号: {new_data['period']}")
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
