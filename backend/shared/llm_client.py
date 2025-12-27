"""
共享 LLM 客户端
通过 DashScope API 调用通义千问模型
"""
import os
import dashscope
import json
import re


class LLMClient:
    """LLM 客户端封装"""
    
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or os.getenv("QWEN_MODEL", "qwen-max")
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        dashscope.api_key = self.api_key
    
    def call_json(self, user_prompt: str, system_prompt: str = None) -> dict:
        """
        调用 LLM 并返回 JSON 格式的结果
        
        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词（可选）
        
        Returns:
            包含 LLM 响应和 token 使用情况的字典
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response = dashscope.Generation.call(
                model=self.model,
                messages=messages,
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                
                # 尝试解析 JSON
                result = self._extract_json(content)
                
                # 添加 token 使用信息
                usage = response.usage
                result["token_usage"] = {
                    "model": self.model,
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "cost": TokenCalculator.calculate_cost(
                        self.model,
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0)
                    )
                }
                
                return result
            else:
                return {
                    "error": f"API 调用失败: {response.code} - {response.message}",
                    "match_score": 50,
                    "advantages": [],
                    "risks": ["API 调用失败"],
                    "advice": "请稍后重试"
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "match_score": 50,
                "advantages": [],
                "risks": [str(e)],
                "advice": "系统错误，请稍后重试"
            }
    
    def _extract_json(self, text: str) -> dict:
        """从文本中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 尝试提取大括号内容
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # 返回默认值
        return {
            "match_score": 50,
            "advantages": ["无法解析响应"],
            "risks": ["响应格式错误"],
            "advice": "请检查输入内容"
        }


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
