# 计费定价模块

本模块负责 Token 费用计算和定价策略管理。

## 模型定价

### 当前支持的模型

| 模型 | 显示名称 | 定价类型 | 用途 |
|------|----------|----------|------|
| `qwen3-max` | Qwen3-Max (分析) | 阶梯定价 | JD-简历匹配分析 |
| `qwen-vl-ocr-2025-11-20` | Qwen-VL-OCR (识别) | 固定定价 | PDF/图片 OCR |

### Qwen3-Max 阶梯定价

根据**输入 Token 数量**分档计费：

| 阶梯 | 输入 Token 范围 | 输入价格 | 输出价格 |
|------|----------------|----------|----------|
| Tier 1 | ≤ 32,000 | ¥0.0032/千 | ¥0.0128/千 |
| Tier 2 | 32,001 ~ 128,000 | ¥0.0064/千 | ¥0.0256/千 |
| Tier 3 | 128,001 ~ 256,000 | ¥0.0096/千 | ¥0.0384/千 |

### Qwen-VL-OCR 固定定价

| 输入价格 | 输出价格 |
|----------|----------|
| ¥0.0003/千 | ¥0.0005/千 |

---

## 费用计算示例

### 示例 1：普通简历匹配（Tier 1）

```
输入 Token: 2,500 (JD + 简历 + 系统提示词)
输出 Token: 300 (匹配报告)

费用 = (2,500/1000) × 0.0032 + (300/1000) × 0.0128
     = 0.008 + 0.00384
     = ¥0.01184
```

### 示例 2：长简历匹配（Tier 2）

```
输入 Token: 50,000
输出 Token: 500

费用 = (50,000/1000) × 0.0064 + (500/1000) × 0.0256
     = 0.32 + 0.0128
     = ¥0.3328
```

### 示例 3：OCR + 分析

```
OCR:
  输入 Token: 5,000 (图片编码)
  输出 Token: 2,000 (识别结果)
  OCR 费用 = 5×0.0003 + 2×0.0005 = ¥0.0025

分析:
  输入 Token: 3,000
  输出 Token: 350
  分析费用 = 3×0.0032 + 0.35×0.0128 = ¥0.01408

总费用 = ¥0.01658
```

---

## 代码使用

### 获取价格

```python
from pricing_config import get_tier_prices, get_model_display_name

# 获取对应阶梯的价格
input_price, output_price = get_tier_prices("qwen3-max", input_tokens=2500)
# (0.0032, 0.0128)

# 获取显示名称
name = get_model_display_name("qwen3-max")
# "Qwen3-Max (分析)"
```

### 计算费用

```python
from token_calculator import TokenCalculator

# 计算费用
cost = TokenCalculator.calculate_cost(
    model="qwen3-max",
    prompt_tokens=2500,
    completion_tokens=300
)
# 0.01184

# 格式化费用
formatted = TokenCalculator.format_cost(cost)
# "¥0.0118"
```

---

## 配置定价

定价配置在 `pricing_config.py` 中：

```python
MODEL_PRICING = {
    "qwen3-max": {
        "display_name": "Qwen3-Max (分析)",
        "tiers": [
            {"max_tokens": 32000, "input_price": 0.0032, "output_price": 0.0128},
            {"max_tokens": 128000, "input_price": 0.0064, "output_price": 0.0256},
            {"max_tokens": 256000, "input_price": 0.0096, "output_price": 0.0384},
        ]
    },
    "qwen-vl-ocr-2025-11-20": {
        "display_name": "Qwen-VL-OCR (识别)",
        "tiers": [
            {"max_tokens": float('inf'), "input_price": 0.0003, "output_price": 0.0005},
        ]
    },
}
```

### 添加新模型

```python
MODEL_PRICING["new-model"] = {
    "display_name": "New Model",
    "tiers": [
        {"max_tokens": 10000, "input_price": 0.001, "output_price": 0.002},
        {"max_tokens": float('inf'), "input_price": 0.002, "output_price": 0.004},
    ]
}
```

---

## 成本估算

### 单次使用成本

| 场景 | 预估费用 |
|------|----------|
| 纯文本简历匹配 | ¥0.01 ~ ¥0.02 |
| PDF 简历（1页）+ 匹配 | ¥0.01 ~ ¥0.03 |
| PDF 简历（多页）+ 匹配 | ¥0.02 ~ ¥0.05 |
| 长 JD + 详细简历 | ¥0.05 ~ ¥0.10 |

### 月度成本估算

| 使用量 | 月成本 |
|--------|--------|
| 100 次/月 | ¥1 ~ ¥3 |
| 1000 次/月 | ¥10 ~ ¥30 |
| 10000 次/月 | ¥100 ~ ¥300 |

---

## 相关文件

- [`pricing_config.py`](../../pricing_config.py) - 定价配置
- [`token_calculator.py`](../../token_calculator.py) - 费用计算器
- [用户模块](user.md) - 扣费逻辑
- [数据库设计](../architecture/database.md) - 费用记录表
