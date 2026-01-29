"""通用工具函数"""
import random
import string
from typing import Optional


def generate_random_string(length: int = 4, charset: Optional[str] = None) -> str:
    """生成指定长度的随机字符串。
    
    Args:
        length: 字符串长度。
        charset: 字符集，默认为大写字母 + 数字。
    """
    if charset is None:
        charset = string.ascii_uppercase + string.digits
    return "".join(random.choice(charset) for _ in range(length))
