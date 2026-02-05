# -*- coding: utf-8 -*-
"""
邮件发送工具模块

使用 Resend API 发送验证码邮件
环境变量:
- RESEND_API_KEY: Resend API Key
"""

import os
import random
import string
import resend
from loguru import logger


# 配置
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "简序智能 INTJsys <noreply@auth.intjsys.com>")


def generate_code(length: int = 6) -> str:
    """生成 6 位随机验证码"""
    return ''.join(random.choices(string.digits, k=length))


def send_email_code(email: str, code: str) -> dict:
    """
    发送验证码邮件
    
    Args:
        email: 目标邮箱
        code: 验证码
        
    Returns:
        dict: { success: bool, message: str }
    """
    # 开发环境模拟发送
    if os.getenv("ENVIRONMENT") != "production" or not RESEND_API_KEY:
        logger.info(f"[Email Mock] 向 {email} 发送验证码: {code}")
        return {"success": True, "message": "验证码已发送（开发模式）"}
    
    try:
        resend.api_key = RESEND_API_KEY
        
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <h1 style="font-size: 24px; font-weight: 800; color: #111; margin: 0;">TalentAI</h1>
                <p style="font-size: 14px; color: #666; margin: 8px 0 0;">智能招聘匹配系统</p>
            </div>
            <div style="background: #f9f9f9; border: 1px solid #eee; padding: 32px; text-align: center;">
                <p style="font-size: 16px; color: #333; margin: 0 0 20px;">您的登录验证码是：</p>
                <div style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #111; font-family: monospace;">
                    {code}
                </div>
                <p style="font-size: 14px; color: #999; margin: 20px 0 0;">验证码 5 分钟内有效，请勿泄露给他人</p>
            </div>
            <p style="font-size: 12px; color: #999; text-align: center; margin-top: 24px;">
                如果这不是您的操作，请忽略此邮件
            </p>
        </div>
        """
        
        result = resend.Emails.send({
            "from": RESEND_FROM,
            "to": email,
            "subject": "【TalentAI】登录验证码",
            "html": html_content
        })
        
        logger.info(f"[Email] 发送成功: {email}, ID: {result.get('id')}")
        return {"success": True, "message": "验证码已发送"}
        
    except Exception as e:
        logger.error(f"[Email] 发送异常: {e}")
        return {"success": False, "message": str(e) or "邮件发送失败"}
