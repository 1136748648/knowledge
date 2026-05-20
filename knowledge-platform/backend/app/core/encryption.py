import os
import base64
import logging
from functools import lru_cache

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


@lru_cache()
def _get_fernet() -> Fernet:
    """获取 Fernet 加密实例"""
    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        # 自动生成并持久化（开发环境）
        key = Fernet.generate_key().decode()
        os.environ["ENCRYPTION_KEY"] = key
        logger.warning("ENCRYPTION_KEY not set, generated a temporary key. Set ENCRYPTION_KEY in .env for production.")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    """加密字符串，返回 base64 编码的密文"""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """解密 base64 编码的密文"""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def mask_sensitive(value: str, show_chars: int = 4) -> str:
    """脱敏显示：保留前 show_chars 个字符，其余用 *** 替代"""
    if not value or len(value) <= show_chars:
        return "***"
    return value[:show_chars] + "***"
