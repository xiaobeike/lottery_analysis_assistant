"""DeepSeek API客户端"""

import json
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests 未安装，DeepSeek客户端不可用")


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        base_url: str = "https://api.deepseek.com/v1"
    ):
        if not REQUESTS_AVAILABLE:
            raise ImportError("请安装 requests: pip install requests")
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def generate_content(self, prompt: str) -> Optional[str]:
        """
        生成内容
        
        Args:
            prompt: 提示词
        
        Returns:
            AI生成的文本内容
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 4096
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            
            if content:
                return content
            else:
                logger.warning("DeepSeek返回空内容")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return None
        except Exception as e:
            logger.error(f"DeepSeek处理失败: {e}")
            return None
    
    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        生成JSON格式内容
        
        Args:
            prompt: 提示词
        
        Returns:
            解析后的字典
        """
        json_prompt = f"{prompt}\n\n请以JSON格式返回，确保JSON格式正确。"
        
        content = self.generate_content(json_prompt)
        
        if not content:
            return None
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            logger.error("无法解析DeepSeek返回的JSON内容")
            return None
    
    def close(self):
        """关闭会话"""
        self.session.close()
