"""
Token 费用计算器
"""


class TokenCalculator:
    """Token 费用计算器"""
    
    # 价格配置 (元/1000 tokens)
    PRICING = {
        "qwen-max": {"input": 0.02, "output": 0.06},
        "qwen-plus": {"input": 0.004, "output": 0.012},
        "qwen-turbo": {"input": 0.002, "output": 0.006},
        "qwen-vl-ocr": {"input": 0.003, "output": 0.003},
        "qwen-vl-ocr-2025-11-20": {"input": 0.003, "output": 0.003},
        "qwen3-max": {"input": 0.02, "output": 0.06},
    }
    
    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        计算 API 调用费用
        
        Args:
            model: 模型名称
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
        
        Returns:
            费用（元）
        """
        pricing = cls.PRICING.get(model, {"input": 0.02, "output": 0.06})
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
