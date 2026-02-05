# -*- coding: utf-8 -*-
"""
模型定价配置模块

支持多模型、阶梯定价配置。
价格单位：元/千Token
"""

from typing import Dict, List, Any

# 模型定价配置
# 结构:
#   - display_name: 模型显示名称
#   - tiers: 阶梯列表，按 max_tokens 升序排列
#     - max_tokens: 该阶梯的 token 上限（输入 token 总数）
#     - input_price: 输入价格 (元/千Token)
#     - output_price: 输出价格 (元/千Token)

MODEL_PRICING: Dict[str, Dict[str, Any]] = {
    # Qwen3-Max - 用于 JD 与简历匹配分析
    # 阶梯定价：根据输入 token 数量分档
    "qwen3-max": {
        "display_name": "Qwen3-Max (分析)",
        "tiers": [
            {"max_tokens": 32000, "input_price": 0.0032, "output_price": 0.0128},
            {"max_tokens": 128000, "input_price": 0.0064, "output_price": 0.0256},
            {"max_tokens": 256000, "input_price": 0.0096, "output_price": 0.0384},
        ]
    },
    
    # Qwen-VL-OCR - 用于简历/图片 OCR 识别
    # 固定价格
    "qwen-vl-ocr": {
        "display_name": "Qwen-VL-OCR (识别)",
        "tiers": [
            {"max_tokens": float('inf'), "input_price": 0.0003, "output_price": 0.0005},
        ]
    },
    "qwen-vl-ocr-2025-11-20": {
        "display_name": "Qwen-VL-OCR (识别)",
        "tiers": [
            {"max_tokens": float('inf'), "input_price": 0.0003, "output_price": 0.0005},
        ]
    },
}



def get_model_pricing(model: str) -> Dict[str, Any] | None:
    """
    获取指定模型的定价配置
    
    Args:
        model: 模型名称
        
    Returns:
        模型定价配置，如果模型不存在则返回 None
    """
    return MODEL_PRICING.get(model)


def get_tier_prices(model: str, input_tokens: int) -> tuple[float, float]:
    """
    根据模型名称和输入 token 数量获取对应阶梯的价格
    
    Args:
        model: 模型名称
        input_tokens: 输入 token 数量
        
    Returns:
        (input_price, output_price) 元/千Token
    """
    pricing = get_model_pricing(model)
    if not pricing:
        # 默认价格（未知模型）
        return (0.001, 0.002)
    
    tiers = pricing.get("tiers", [])
    for tier in tiers:
        if input_tokens <= tier["max_tokens"]:
            return (tier["input_price"], tier["output_price"])
    
    # 如果超出所有阶梯，使用最后一个阶梯的价格
    if tiers:
        last_tier = tiers[-1]
        return (last_tier["input_price"], last_tier["output_price"])
    
    return (0.001, 0.002)


def get_model_display_name(model: str) -> str:
    """获取模型的显示名称"""
    pricing = get_model_pricing(model)
    if pricing:
        return pricing.get("display_name", model)
    return model


def list_supported_models() -> List[str]:
    """列出所有支持定价的模型"""
    return list(MODEL_PRICING.keys())
