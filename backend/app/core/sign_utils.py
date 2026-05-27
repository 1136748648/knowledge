import logging
import hashlib
import hmac
import json
import time
import re
import urllib.parse
from typing import Dict, Any

logger = logging.getLogger(__name__)

LARGE_FIELD_THRESHOLD = 1000


def generate_nonce(length: int = 16) -> str:
    """生成随机字符串"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def normalize_string(value: str) -> str:
    """规范化字符串，统一换行符和空白字符"""
    if not isinstance(value, str):
        return value
    
    normalized = value.replace('\r\n', '\n')
    normalized = normalized.strip()
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    normalized = re.sub(r'[ \t]+', ' ', normalized)
    
    return normalized


def generate_signature(params: Dict[str, Any], secret: str) -> str:
    """
    生成 HMAC-SHA256 签名
    
    特性：
    1. 签名参数包含：timestamp、nonce、body_hash
    2. body_hash 是请求 body 的 SHA256 哈希值
    
    :param params: 参数字典，应包含 timestamp, nonce, body_hash
    :param secret: 签名密钥
    :return: 十六进制签名字符串
    """
    if not params:
        params = {}
    
    processed_params = {}
    
    for key, value in params.items():
        if isinstance(value, str):
            processed_params[key] = value.strip()
        elif isinstance(value, (dict, list)):
            processed_params[key] = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        else:
            processed_params[key] = str(value)
    
    sorted_keys = sorted(processed_params.keys())
    sign_string = '&'.join(
        f"{k}={urllib.parse.quote(processed_params[k], safe='')}"
        for k in sorted_keys
    )
    
    logger.debug(f"签名前字符串: {sign_string}")
    signature = hmac.new(secret.encode(), sign_string.encode(), hashlib.sha256).hexdigest()
    return signature


def compute_body_hash(body_bytes: bytes) -> str:
    """
    计算请求 body 的 SHA256 哈希值
    
    :param body_bytes: 请求 body 的 UTF-8 字节流
    :return: 十六进制哈希字符串
    """
    if not body_bytes:
        body_bytes = b''
    return hashlib.sha256(body_bytes).hexdigest()


def verify_signature(params: Dict[str, Any], signature: str, secret: str) -> bool:
    """
    验证签名是否正确
    
    :param params: 参数字典
    :param signature: 待验证的签名
    :param secret: 签名密钥
    :return: 是否验证通过
    """
    expected_signature = generate_signature(params, secret)
    return hmac.compare_digest(expected_signature, signature)


def is_timestamp_valid(timestamp: int, tolerance: int = 60) -> bool:
    """
    验证时间戳是否在允许范围内
    
    :param timestamp: 请求时间戳（Unix时间戳，秒）
    :param tolerance: 时间差容忍度（秒）
    :return: 是否有效
    """
    current_time = int(time.time())
    return abs(current_time - timestamp) <= tolerance
