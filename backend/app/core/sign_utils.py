import logging
import hashlib
import hmac
import json
import time
from typing import Dict, Any
logger = logging.getLogger(__name__)


def generate_nonce(length: int = 16) -> str:
    """生成随机字符串"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_signature(params: Dict[str, Any], secret: str) -> str:
    """
    生成 HMAC-SHA256 签名
    
    :param params: 参数字典
    :param secret: 签名密钥
    :return: 十六进制签名字符串
    """
    if not params:
        params = {}
    
    sorted_keys = sorted(params.keys())
    sign_string = '&'.join(f"{k}={json.dumps(params[k], separators=(',', ':')) if isinstance(params[k], (dict, list)) else params[k]}" for k in sorted_keys)
    logger.debug(f"签名前字符串: {sign_string}")
    signature = hmac.new(secret.encode(), sign_string.encode(), hashlib.sha256).hexdigest()
    return signature


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
