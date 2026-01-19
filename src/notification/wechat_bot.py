"""企业微信机器人模块"""

import json
from typing import Any, Dict, Optional
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)


class WeChatBot:
    """企业微信群机器人"""
    
    def __init__(
        self,
        webhook_url: str,
        rate_limit: int = 20
    ):
        self.webhook_url = webhook_url
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def send_markdown(self, content: str) -> bool:
        """发送Markdown消息"""
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        return self._send(payload)
    
    def send_text(
        self,
        content: str,
        mentioned_list: list = None,
        mentioned_mobile_list: list = None
    ) -> bool:
        """发送文本消息"""
        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        if mentioned_list:
            payload["text"]["mentioned_list"] = mentioned_list
        if mentioned_mobile_list:
            payload["text"]["mentioned_mobile_list"] = mentioned_mobile_list
        
        return self._send(payload)
    
    def _send(self, payload: Dict[str, Any]) -> bool:
        """发送消息"""
        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False
    
    def close(self):
        """关闭会话"""
        self.session.close()
