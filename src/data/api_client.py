"""API客户端模块"""

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LotteryAPIClient:
    """彩票API客户端"""
    
    def __init__(self, base_url: str = "http://api.huiniao.top/interface/home/lotteryHistory"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_data(
        self,
        lottery_type: str,
        periods: int = 30,
        page: int = 1
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取彩票数据
        
        Args:
            lottery_type: 彩票类型 (ssq/dlt)
            periods: 获取期数
            page: 页码
        
        Returns:
            彩票数据列表
        """
        # API类型映射
        type_map = {
            'ssq': 'ssq',   # 双色球
            'dlt': 'dlt'    # 大乐透
        }
        
        api_type = type_map.get(lottery_type, lottery_type)
        
        params = {
            'type': api_type,
            'page': page,
            'limit': periods
        }
        
        try:
            logger.info(f"请求API: {self.base_url}, 参数: {params}")
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 1:
                result = data.get('data', {})
                # 修复：正确的路径是 data.data.list
                data_obj = result.get('data', {})
                records = data_obj.get('list', [])
                
                logger.info(f"成功获取 {len(records)} 条记录")
                return self._parse_records(records, lottery_type)
            else:
                logger.error(f"API返回错误: {data.get('info', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            return None
    
    def _parse_records(
        self,
        records: List[Dict],
        lottery_type: str
    ) -> List[Dict[str, Any]]:
        """解析API返回的记录"""
        parsed = []
        
        for record in records:
            try:
                if lottery_type == 'ssq':
                    # 双色球：6个红球 + 1个蓝球
                    parsed_record = {
                        'lottery_type': 'ssq',
                        'period': record.get('code', ''),
                        'date': record.get('day', ''),
                        'open_time': record.get('open_time', ''),
                        'red_balls': self._parse_reds(record),
                        'blue_ball': self._parse_blues(record),
                        'next_open_time': record.get('next_open_time', ''),
                        'next_code': record.get('next_code', '')
                    }
                else:
                    # 大乐透：5个前区 + 2个后区
                    parsed_record = {
                        'lottery_type': 'dlt',
                        'period': record.get('code', ''),
                        'date': record.get('day', ''),
                        'open_time': record.get('open_time', ''),
                        'front_balls': self._parse_fronts(record),
                        'back_balls': self._parse_backs(record),
                        'next_open_time': record.get('next_open_time', ''),
                        'next_code': record.get('next_code', '')
                    }
                
                parsed.append(parsed_record)
                
            except Exception as e:
                logger.warning(f"解析记录失败: {e}, 记录: {record}")
                continue
        
        return parsed
    
    def _parse_reds(self, record: Dict) -> List[int]:
        """解析双色球红球（字段：one-six）"""
        reds = []
        field_names = ['one', 'two', 'three', 'four', 'five', 'six']
        for field in field_names:
            value = record.get(field, 0)
            if value:
                try:
                    reds.append(int(value))
                except (ValueError, TypeError):
                    continue
        return sorted(reds)
    
    def _parse_blues(self, record: Dict) -> int:
        """解析双色球蓝球（字段名为seven）"""
        blue = record.get('seven', 0)
        if blue:
            try:
                return int(blue)
            except (ValueError, TypeError):
                return 0
        return 0
    
    def _parse_fronts(self, record: Dict) -> List[int]:
        """解析大乐透前区（one-five）"""
        fronts = []
        field_names = ['one', 'two', 'three', 'four', 'five']
        for field in field_names:
            value = record.get(field, 0)
            if value:
                try:
                    fronts.append(int(value))
                except (ValueError, TypeError):
                    continue
        return sorted(fronts)
    
    def _parse_backs(self, record: Dict) -> List[int]:
        """解析大乐透后区（six, seven）"""
        backs = []
        # six 和 seven 是后区两个号码
        for key in ['six', 'seven']:
            back = record.get(key, 0)
            if back:
                try:
                    backs.append(int(back))
                except (ValueError, TypeError):
                    continue
        return sorted(backs)
    
    def fetch_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """获取最新一期数据"""
        records = self.fetch_data(lottery_type, periods=1)
        return records[0] if records else None
    
    def close(self):
        """关闭会话"""
        self.session.close()
