import random
import string
from typing import Any, Dict, List, TypeVar

T = TypeVar('T')


def generate_random_string(length: int = 16, include_special: bool = False) -> str:
    """生成随机字符串

    Args:
        length: 字符串长度
        include_special: 是否包含特殊字符

    Returns:
        str: 随机字符串

    """
    characters = string.ascii_letters + string.digits
    if include_special:
        characters += string.punctuation

    return ''.join(random.choice(characters) for _ in range(length))


def generate_otp(length: int = 6) -> str:
    """生成一次性密码（OTP）

    Args:
        length: OTP长度

    Returns:
        str: 数字OTP

    """
    return ''.join(random.choice(string.digits) for _ in range(length))


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """移除字典中的None值

    Args:
        data: 输入字典

    Returns:
        Dict[str, Any]: 移除None值后的字典

    """
    return {k: v for k, v in data.items() if v is not None}


def deep_merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典

    Args:
        a: 第一个字典
        b: 第二个字典

    Returns:
        Dict[str, Any]: 合并后的字典

    """
    result = a.copy()

    for key, value in b.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def paginate_list(items: List[T], page: int, page_size: int) -> Dict[str, Any]:
    """分页处理列表数据

    Args:
        items: 列表数据
        page: 当前页码
        page_size: 每页大小

    Returns:
        Dict[str, Any]: 包含分页数据的字典

    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """截断字符串

    Args:
        s: 输入字符串
        max_length: 最大长度
        suffix: 截断后的后缀

    Returns:
        str: 截断后的字符串

    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix
