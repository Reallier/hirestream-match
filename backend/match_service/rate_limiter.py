# -*- coding: utf-8 -*-
"""
DashScope API 多 Key 轮询限流器

核心发现: DashScope 单 Key 同时只能处理 1 个请求（纯串行）
解决方案: 多 Key 轮询，N 个 Key = N 并发

限流规则参考: https://help.aliyun.com/document_detail/2712195.html
"""
import os
import time
import threading
from typing import List, Optional
from itertools import cycle

class MultiKeyRotator:
    """
    多 Key 轮询器 - 真正实现 N 并发
    
    DashScope 单 Key 同时只能处理 1 个请求，通过轮询多个 Key 实现真正并发。
    
    使用方式:
        rotator = MultiKeyRotator(["sk-xxx", "sk-yyy"])
        api_key = rotator.get_next_key()  # 获取下一个可用的 Key
    """
    
    def __init__(self, api_keys: Optional[List[str]] = None):
        """
        初始化多 Key 轮询器
        
        Args:
            api_keys: API Key 列表。如果为空，从环境变量 DASHSCOPE_API_KEYS 读取（逗号分隔）
        """
        if api_keys:
            self.keys = [k.strip() for k in api_keys if k.strip()]
        else:
            # 从环境变量读取，支持逗号分隔的多个 Key
            keys_str = os.getenv("DASHSCOPE_API_KEYS", "")
            if keys_str:
                self.keys = [k.strip() for k in keys_str.split(",") if k.strip()]
            else:
                # 兼容单 Key 环境变量
                single_key = os.getenv("DASHSCOPE_API_KEY", "")
                self.keys = [single_key] if single_key else []
        
        if not self.keys:
            raise ValueError("未找到任何 DashScope API Key")
        
        self._key_cycle = cycle(self.keys)
        self._lock = threading.Lock()
        self._key_usage = {k: {"last_used": 0.0, "count": 0} for k in self.keys}
    
    def get_next_key(self) -> str:
        """
        获取下一个可用的 API Key（轮询）
        
        Returns:
            API Key 字符串
        """
        with self._lock:
            key = next(self._key_cycle)
            self._key_usage[key]["last_used"] = time.time()
            self._key_usage[key]["count"] += 1
            return key
    
    def get_key_count(self) -> int:
        """返回可用 Key 数量"""
        return len(self.keys)
    
    def get_usage_stats(self) -> dict:
        """获取 Key 使用统计"""
        return self._key_usage.copy()


# 平滑限流器（保留，用于控制全局发送速率）
class SmoothRateLimiter:
    """平滑限流器 - 控制请求发送速率，避免瞬时爆发"""
    
    def __init__(self, rps: float = 10.0):
        self.rps = rps
        self.interval = 1.0 / rps
        self._last_request_time: float = 0.0
        self._lock = threading.Lock()
    
    def acquire(self) -> float:
        """获取发送许可，返回等待时间"""
        with self._lock:
            now = time.time()
            wait_time = self._last_request_time + self.interval - now
            
            if wait_time > 0:
                time.sleep(wait_time)
                waited = wait_time
            else:
                waited = 0.0
            
            self._last_request_time = time.time()
            return waited


# 全局实例
_rotator: Optional[MultiKeyRotator] = None
_limiter = SmoothRateLimiter(rps=10.0)


def init_keys(api_keys: Optional[List[str]] = None):
    """初始化多 Key 轮询器"""
    global _rotator
    _rotator = MultiKeyRotator(api_keys)
    return _rotator


def get_rotator() -> MultiKeyRotator:
    """获取全局轮询器实例"""
    global _rotator
    if _rotator is None:
        _rotator = MultiKeyRotator()
    return _rotator


def get_next_key() -> str:
    """获取下一个 API Key（轮询）"""
    return get_rotator().get_next_key()


def acquire() -> float:
    """获取发送许可（平滑限流）"""
    return _limiter.acquire()
