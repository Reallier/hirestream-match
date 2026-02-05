"""
阿里云 DashScope 余额查询工具

查询方式：
1. 通过阿里云 Billing API 查询账户余额
2. 需要配置 AccessKey ID 和 AccessKey Secret

使用方法：
    设置环境变量:
    - ALIYUN_ACCESS_KEY_ID
    - ALIYUN_ACCESS_KEY_SECRET
    
    python check_dashscope_balance.py
"""

import os
import json
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
from datetime import datetime, timezone
import uuid


def percent_encode(value: str) -> str:
    """RFC 3986 URL 编码"""
    return urllib.parse.quote(value, safe='~')


def create_signature(
    method: str,
    params: dict,
    access_key_secret: str
) -> str:
    """创建请求签名"""
    # 按参数名排序
    sorted_params = sorted(params.items())
    
    # 构建规范化查询字符串
    canonicalized_query_string = '&'.join([
        f"{percent_encode(k)}={percent_encode(str(v))}"
        for k, v in sorted_params
    ])
    
    # 构建待签名字符串
    string_to_sign = f"{method}&{percent_encode('/')}&{percent_encode(canonicalized_query_string)}"
    
    # 计算签名
    key = (access_key_secret + '&').encode('utf-8')
    message = string_to_sign.encode('utf-8')
    signature = base64.b64encode(
        hmac.new(key, message, hashlib.sha1).digest()
    ).decode('utf-8')
    
    return signature


def query_account_balance(
    access_key_id: str,
    access_key_secret: str
) -> dict:
    """
    查询阿里云账户余额
    
    API 文档: https://help.aliyun.com/document_detail/87872.html
    """
    # 基础参数
    params = {
        'Format': 'JSON',
        'Version': '2017-12-14',
        'AccessKeyId': access_key_id,
        'SignatureMethod': 'HMAC-SHA1',
        'Timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'SignatureVersion': '1.0',
        'SignatureNonce': str(uuid.uuid4()),
        'Action': 'QueryAccountBalance',
    }
    
    # 计算签名
    signature = create_signature('GET', params, access_key_secret)
    params['Signature'] = signature
    
    # 发送请求
    query_string = urllib.parse.urlencode(params)
    url = f"https://business.aliyuncs.com/?{query_string}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {'error': f"HTTP {e.code}", 'message': error_body}
    except Exception as e:
        return {'error': str(e)}


def format_balance_result(result: dict) -> str:
    """格式化余额查询结果"""
    if 'error' in result:
        return f"❌ 查询失败: {result.get('message', result['error'])}"
    
    data = result.get('Data', {})
    
    output = []
    output.append("=" * 50)
    output.append("阿里云账户余额信息")
    output.append("=" * 50)
    
    # 可用余额
    available = data.get('AvailableAmount', 'N/A')
    output.append(f"💰 可用余额: ¥{available}")
    
    # 现金余额
    cash = data.get('AvailableCashAmount', 'N/A')
    output.append(f"💵 现金余额: ¥{cash}")
    
    # 代金券余额
    coupon = data.get('CreditAmount', 'N/A')
    output.append(f"🎫 代金券余额: ¥{coupon}")
    
    # 信用额度
    credit = data.get('MybankCreditAmount', 'N/A')
    if credit != 'N/A' and credit != '0.00':
        output.append(f"🏦 信用额度: ¥{credit}")
    
    output.append("=" * 50)
    
    # 公测建议
    try:
        available_amount = float(available)
        if available_amount < 100:
            output.append("⚠️ 警告: 余额不足，建议立即充值!")
        elif available_amount < 500:
            output.append("⚡ 提醒: 余额较低，建议尽快充值")
        else:
            output.append("✅ 余额充足，可支持公测运营")
    except:
        pass
    
    return '\n'.join(output)


def main():
    # 从环境变量读取 AccessKey
    access_key_id = os.environ.get('ALIYUN_ACCESS_KEY_ID', '')
    access_key_secret = os.environ.get('ALIYUN_ACCESS_KEY_SECRET', '')
    
    if not access_key_id or not access_key_secret:
        print("=" * 50)
        print("阿里云 DashScope 余额查询")
        print("=" * 50)
        print()
        print("❌ 未配置 AccessKey，请设置环境变量:")
        print("   ALIYUN_ACCESS_KEY_ID=your_access_key_id")
        print("   ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret")
        print()
        print("📌 替代方案 - 手动查询:")
        print("   1. 登录 DashScope 控制台:")
        print("      https://dashscope.console.aliyun.com/")
        print()
        print("   2. 登录阿里云费用中心:")
        print("      https://usercenter2.aliyun.com/finance/fund-management/overview")
        print()
        print("💡 公测期间建议余额 > ¥500")
        return
    
    print("正在查询阿里云账户余额...")
    result = query_account_balance(access_key_id, access_key_secret)
    print(format_balance_result(result))


if __name__ == '__main__':
    main()
