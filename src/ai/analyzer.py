"""AI分析器模块"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .gemini_client import GeminiClient
from .deepseek_client import DeepSeekClient
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = config.get('ai', {}).get('providers', {})
        self.primary_provider = config.get('ai', {}).get('primary_provider', 'gemini')
        self._clients = {}
    
    def _get_client(self, provider: str):
        """获取AI客户端"""
        if provider in self._clients:
            return self._clients[provider]
        
        provider_config = self.providers.get(provider, {})
        
        if not provider_config.get('enabled', False):
            logger.warning(f"AI提供商 {provider} 未启用")
            return None
        
        api_key = provider_config.get('api_key', '')
        if not api_key or api_key.startswith('YOUR_'):
            logger.warning(f"{provider} API密钥未配置")
            return None
        
        try:
            if provider == 'gemini':
                client = GeminiClient(
                    api_key=api_key,
                    model=provider_config.get('model', 'gemini-1.5-flash'),
                    temperature=provider_config.get('temperature', 0.7)
                )
            elif provider == 'deepseek':
                client = DeepSeekClient(
                    api_key=api_key,
                    model=provider_config.get('model', 'deepseek-chat'),
                    temperature=provider_config.get('temperature', 0.7)
                )
            else:
                logger.error(f"不支持的AI提供商: {provider}")
                return None
            
            self._clients[provider] = client
            return client
            
        except Exception as e:
            logger.error(f"初始化{provider}客户端失败: {e}")
            return None
    
    def analyze(
        self,
        lottery_type: str,
        historical_data: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI分析彩票数据
        
        Args:
            lottery_type: 彩票类型
            historical_data: 历史数据
        
        Returns:
            分析结果
        """
        # 尝试主提供商
        client = self._get_client(self.primary_provider)
        
        if client:
            try:
                prompt = PromptTemplates.build_analysis_prompt(
                    lottery_type, historical_data
                )
                
                result = client.generate_content(prompt)
                
                if result:
                    return self._parse_analysis_result(result, lottery_type)
                    
            except Exception as e:
                logger.error(f"AI分析失败（{self.primary_provider}）: {e}")
        
        # 尝试备用提供商
        backup_provider = 'deepseek' if self.primary_provider == 'gemini' else 'gemini'
        
        if backup_provider != self.primary_provider:
            logger.info(f"尝试备用提供商: {backup_provider}")
            client = self._get_client(backup_provider)
            
            if client:
                try:
                    prompt = PromptTemplates.build_analysis_prompt(
                        lottery_type, historical_data
                    )
                    
                    result = client.generate_content(prompt)
                    
                    if result:
                        return self._parse_analysis_result(result, lottery_type)
                        
                except Exception as e:
                    logger.error(f"AI分析失败（{backup_provider}）: {e}")
        
        logger.error("所有AI提供商都不可用")
        return None
    
    def generate_recommendations(
        self,
        lottery_type: str,
        analysis_results: Dict[str, Any],
        count: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI生成推荐号码
        
        Args:
            lottery_type: 彩票类型
            analysis_results: 分析结果
            count: 推荐数量
        
        Returns:
            推荐结果
        """
        # 尝试主提供商
        client = self._get_client(self.primary_provider)
        
        if client:
            try:
                prompt = PromptTemplates.build_recommendation_prompt(
                    lottery_type, analysis_results, count
                )
                
                result = client.generate_json(prompt)
                
                if result:
                    return result
                    
            except Exception as e:
                logger.error(f"AI推荐生成失败（{self.primary_provider}）: {e}")
        
        # 尝试备用提供商
        backup_provider = 'deepseek' if self.primary_provider == 'gemini' else 'gemini'
        
        if backup_provider != self.primary_provider:
            client = self._get_client(backup_provider)
            
            if client:
                try:
                    prompt = PromptTemplates.build_recommendation_prompt(
                        lottery_type, analysis_results, count
                    )
                    
                    result = client.generate_json(prompt)
                    
                    if result:
                        return result
                        
                except Exception as e:
                    logger.error(f"AI推荐生成失败（{backup_provider}）: {e}")
        
        return None
    
    def _parse_analysis_result(
        self,
        result: str,
        lottery_type: str
    ) -> Dict[str, Any]:
        """解析AI分析结果"""
        return {
            'lottery_type': lottery_type,
            'analysis_time': datetime.now().isoformat(),
            'raw_result': result,
            'summary': self._extract_summary(result),
            'details': result
        }
    
    def _extract_summary(self, result: str) -> str:
        """提取分析摘要"""
        # 提取前500字符作为摘要
        if len(result) <= 500:
            return result
        
        # 尝试在段落边界截断
        newline_pos = result[:500].rfind('\n')
        if newline_pos > 200:
            return result[:newline_pos] + '...'
        
        return result[:500] + '...'
