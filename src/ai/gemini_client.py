"""Google Gemini API客户端"""

import json
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai 未安装，Gemini客户端不可用")


class GeminiClient:
    """Gemini API客户端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_output_tokens: int = 2048
    ):
        if not GEMINI_AVAILABLE:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        # 配置Gemini
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
    
    def generate_content(self, prompt: str) -> Optional[str]:
        """
        生成内容
        
        Args:
            prompt: 提示词
        
        Returns:
            AI生成的文本内容
        """
        try:
            response = self.client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens
                )
            )
            
            if response.text:
                return response.text
            else:
                logger.warning("Gemini返回空内容")
                return None
                
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            return None
    
    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        生成JSON格式内容
        
        Args:
            prompt: 提示词
        
        Returns:
            解析后的字典
        """
        # 在提示词中要求JSON格式
        json_prompt = f"{prompt}\n\n请以JSON格式返回，确保JSON格式正确。"
        
        content = self.generate_content(json_prompt)
        
        if not content:
            return None
        
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取JSON块
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 尝试提取花括号内容
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            logger.error("无法解析Gemini返回的JSON内容")
            return None
