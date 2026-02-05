#!/usr/bin/env python
"""
License 生成工具

用于生成 TalentAI 私有化部署的 License 密钥。

使用方式：
    # 首先生成 RSA 密钥对（仅需一次）
    python generate_license.py --generate-keys
    
    # 生成 License
    python generate_license.py --machine-id <MACHINE_ID> --customer "公司名称" --edition professional --days 365

注意：
    - 私钥 (private_key.pem) 必须严格保密，仅在 INTJsys 服务器使用
    - 公钥 (public_key.pem) 需要部署到客户服务器的环境变量 LICENSE_PUBLIC_KEY
"""
import argparse
import json
import jwt
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_rsa_keys(output_dir: Path = Path(".")):
    """生成 RSA 密钥对"""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    
    print("正在生成 2048 位 RSA 密钥对...")
    
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # 导出私钥
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # 导出公钥
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # 保存文件
    private_key_path = output_dir / "license_private_key.pem"
    public_key_path = output_dir / "license_public_key.pem"
    
    private_key_path.write_bytes(private_pem)
    public_key_path.write_bytes(public_pem)
    
    print(f"✓ 私钥已保存: {private_key_path}")
    print(f"✓ 公钥已保存: {public_key_path}")
    print()
    print("⚠️  重要提醒:")
    print("  1. 私钥必须严格保密，切勿泄露或提交到代码仓库")
    print("  2. 公钥需要配置到客户服务器的 LICENSE_PUBLIC_KEY 环境变量")
    
    return private_pem.decode(), public_pem.decode()


def generate_license(
    private_key: str,
    machine_id: str,
    customer: str,
    edition: str = "professional",
    max_users: int = 200,
    max_concurrency: int = 20,
    features: list = None,
    days: int = 365,
    lic_id: str = None,
):
    """
    生成 License 密钥
    
    Args:
        private_key: RSA 私钥 (PEM 格式)
        machine_id: 客户服务器机器指纹
        customer: 客户名称
        edition: 版本 (standard/professional/enterprise/flagship)
        max_users: 用户数上限
        max_concurrency: 并发数上限
        features: 功能列表
        days: 有效天数
        lic_id: License ID (可选，自动生成)
    
    Returns:
        str: JWT 格式的 License 密钥
    """
    if features is None:
        # 根据版本设置默认功能
        edition_features = {
            "standard": ["instant_match", "talent_pool"],
            "professional": ["instant_match", "talent_pool", "jd_search", "api_access"],
            "enterprise": ["instant_match", "talent_pool", "jd_search", "api_access", "custom_model", "sso"],
            "flagship": ["instant_match", "talent_pool", "jd_search", "api_access", "custom_model", "sso", "source_code"],
        }
        features = edition_features.get(edition, ["instant_match"])
    
    if lic_id is None:
        lic_id = f"LIC-{datetime.now().strftime('%Y%m%d')}-{machine_id[:8].upper()}"
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=days)
    
    payload = {
        "lic_id": lic_id,
        "customer": customer,
        "machine_id": machine_id,
        "edition": edition,
        "max_users": max_users,
        "max_concurrency": max_concurrency,
        "features": features,
        "issued_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token, payload


def main():
    parser = argparse.ArgumentParser(description="TalentAI License 生成工具")
    
    parser.add_argument(
        "--generate-keys",
        action="store_true",
        help="生成 RSA 密钥对"
    )
    parser.add_argument(
        "--private-key",
        type=str,
        default="license_private_key.pem",
        help="私钥文件路径"
    )
    parser.add_argument(
        "--machine-id",
        type=str,
        help="客户服务器机器指纹"
    )
    parser.add_argument(
        "--customer",
        type=str,
        help="客户名称"
    )
    parser.add_argument(
        "--edition",
        type=str,
        default="professional",
        choices=["standard", "professional", "enterprise", "flagship"],
        help="版本类型"
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=200,
        help="用户数上限"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=20,
        help="并发数上限"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="有效天数"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径 (不指定则输出到控制台)"
    )
    
    args = parser.parse_args()
    
    # 生成密钥对模式
    if args.generate_keys:
        generate_rsa_keys()
        return
    
    # 生成 License 模式
    if not args.machine_id or not args.customer:
        parser.error("生成 License 需要 --machine-id 和 --customer 参数")
    
    # 读取私钥
    private_key_path = Path(args.private_key)
    if not private_key_path.exists():
        print(f"❌ 私钥文件不存在: {private_key_path}")
        print("   请先运行: python generate_license.py --generate-keys")
        sys.exit(1)
    
    private_key = private_key_path.read_text()
    
    # 生成 License
    license_key, payload = generate_license(
        private_key=private_key,
        machine_id=args.machine_id,
        customer=args.customer,
        edition=args.edition,
        max_users=args.max_users,
        max_concurrency=args.max_concurrency,
        days=args.days,
    )
    
    print("="*60)
    print("License 生成成功")
    print("="*60)
    print()
    print(f"License ID: {payload['lic_id']}")
    print(f"客户: {payload['customer']}")
    print(f"版本: {payload['edition']}")
    print(f"用户上限: {payload['max_users']}")
    print(f"并发上限: {payload['max_concurrency']}")
    print(f"功能: {', '.join(payload['features'])}")
    print(f"生效时间: {payload['issued_at']}")
    print(f"过期时间: {payload['expires_at']}")
    print()
    print("License Key:")
    print("-"*60)
    print(license_key)
    print("-"*60)
    
    if args.output:
        output_path = Path(args.output)
        output_data = {
            "license_key": license_key,
            "metadata": payload,
        }
        output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
        print(f"\n✓ 已保存到: {output_path}")


if __name__ == "__main__":
    main()
