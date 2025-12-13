# -*- coding: utf-8 -*-
"""
共享模块包

包含 HireStream-Match 和 TalentAI 共用的模块：
- qwen_pdf_ocr: PDF/图片 OCR 识别
- token_calculator: Token 费用计算
- pricing_config: 模型定价配置
- llm_client: 统一 LLM 调用客户端
"""

from .pricing_config import (
    MODEL_PRICING,
    get_model_pricing,
    get_tier_prices,
    get_model_display_name,
    list_supported_models
)

from .token_calculator import (
    TokenUsage,
    TokenCalculator
)

# QwenPDFOCR 需要特殊处理 import，因为它依赖 log 模块
# 使用时请直接 from shared.qwen_pdf_ocr import QwenPDFOCR

__all__ = [
    'MODEL_PRICING',
    'get_model_pricing', 
    'get_tier_prices',
    'get_model_display_name',
    'list_supported_models',
    'TokenUsage',
    'TokenCalculator',
]
