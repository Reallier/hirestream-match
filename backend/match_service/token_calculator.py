# -*- coding: utf-8 -*-
"""
Token 费用计算模块

提供 token 费用计算和使用量汇总功能。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pricing_config import get_tier_prices, get_model_display_name


@dataclass
class TokenUsage:
    """单次 API 调用的 token 使用记录"""
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    
    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
    
    @property
    def display_name(self) -> str:
        return get_model_display_name(self.model)


class TokenCalculator:
    """Token 费用计算器"""
    
    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        根据模型和 token 数计算费用
        
        Args:
            model: 模型名称
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            
        Returns:
            费用（元）
        """
        input_price, output_price = get_tier_prices(model, prompt_tokens)
        
        # 价格单位是 元/千Token，需要除以 1000
        input_cost = (prompt_tokens / 1000) * input_price
        output_cost = (completion_tokens / 1000) * output_price
        
        return input_cost + output_cost
    
    @staticmethod
    def create_usage(model: str, prompt_tokens: int, completion_tokens: int) -> TokenUsage:
        """
        创建一个包含费用计算的 TokenUsage 记录
        
        Args:
            model: 模型名称
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            
        Returns:
            TokenUsage 实例
        """
        cost = TokenCalculator.calculate_cost(model, prompt_tokens, completion_tokens)
        return TokenUsage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost
        )
    
    @staticmethod
    def aggregate_usages(usages: List[TokenUsage]) -> Dict[str, Any]:
        """
        汇总多个 token 使用记录
        
        Args:
            usages: TokenUsage 列表
            
        Returns:
            汇总报告字典
        """
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        
        by_model: Dict[str, Dict[str, Any]] = {}
        
        for usage in usages:
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
            total_cost += usage.cost
            
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "display_name": usage.display_name,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost": 0.0,
                    "calls": 0
                }
            
            by_model[usage.model]["prompt_tokens"] += usage.prompt_tokens
            by_model[usage.model]["completion_tokens"] += usage.completion_tokens
            by_model[usage.model]["cost"] += usage.cost
            by_model[usage.model]["calls"] += 1
        
        return {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_cost": total_cost,
            "by_model": by_model
        }
    
    @staticmethod
    def format_cost(cost: float) -> str:
        """格式化费用显示"""
        if cost < 0.01:
            return f"¥{cost:.6f}"
        elif cost < 1:
            return f"¥{cost:.4f}"
        else:
            return f"¥{cost:.2f}"
