"""Google Gemini API客户端"""

import json
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai 未安装，Gemini客户端不可用")


@dataclass
class GeminiError(Exception):
    """Gemini API 错误异常"""
    message: str
    error_type: str = "gemini_error"
    retryable: bool = True


class GeminiClient:
    """Gemini API客户端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        request_delay: float = 2.0,
        max_retries: int = 5,
        retry_delay: float = 5.0,
        model_fallback: str = "gemini-2.0-flash-exp"
    ):
        if not GEMINI_AVAILABLE:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")
        
        self.api_key = api_key
        self.model = model
        self.model_fallback = model_fallback
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 配置Gemini
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
    
    def generate_content(self, prompt: str) -> str:
        """
        生成内容

        Args:
            prompt: 提示词

        Returns:
            AI生成的文本内容

        Raises:
            GeminiError: 当API调用失败时抛出，允许调用方切换到备用提供商
        """
        time.sleep(self.request_delay)
        
        last_error = None
        models_to_try = [self.model]
        
        if hasattr(self, 'model_fallback') and self.model_fallback:
            models_to_try.append(self.model_fallback)
        
        for model in models_to_try:
            for attempt in range(self.max_retries):
                try:
                    if model != self.model:
                        client = genai.GenerativeModel(model)
                    else:
                        client = self.client
                    
                    response = client.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_output_tokens
                        )
                    )

                    if response.text:
                        return response.text
                    else:
                        raise GeminiError(
                            message="Gemini返回空内容",
                            error_type="empty_response",
                            retryable=False
                        )

                except GeminiError:
                    raise
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    if '429' in error_str or 'resource_exhausted' in error_str:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Gemini API速率限制 (429)，等待 {wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise GeminiError(
                            message=f"Gemini API调用失败: {e}",
                            error_type="api_error",
                            retryable=False
                        )
        
        raise GeminiError(
            message=f"Gemini API多次重试后失败: {last_error}",
            error_type="retry_exhausted",
            retryable=False
        )

    def check_availability(self) -> bool:
        """
        检查API是否可用

        Returns:
            API是否可用
        """
        try:
            # 尝试调用模型列表 API 来验证
            for model in genai.list_models():
                if model.name == f"models/{self.model}":
                    return True
            # 如果模型不存在，抛出异常
            raise ValueError(f"Model {self.model} not available")
        except Exception as e:
            logger.warning(f"Gemini API不可用: {e}")
            return False
    
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        生成JSON格式内容
        
        Args:
            prompt: 提示词
        
        Returns:
            解析后的字典
        
        Raises:
            GeminiError: 当API调用失败时抛出
        """
        json_prompt = f"{prompt}\n\n请以JSON格式返回，确保JSON格式正确。"
        
        content = self.generate_content(json_prompt)
        
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
            
            raise GeminiError(
                message="无法解析Gemini返回的JSON内容",
                error_type="json_parse_error",
                retryable=False
            )
