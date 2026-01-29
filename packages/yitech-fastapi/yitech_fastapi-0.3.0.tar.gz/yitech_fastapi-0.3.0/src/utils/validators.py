import re
from typing import List


def validate_email(email: str) -> bool:
    """验证邮箱格式是否正确

    Args:
        email: 邮箱地址

    Returns:
        bool: 邮箱格式正确返回True，否则返回False

    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_password_strength(password: str) -> List[str]:
    """验证密码强度

    Args:
        password: 密码

    Returns:
        List[str]: 密码强度问题列表，为空表示密码强度符合要求

    """
    issues = []

    if len(password) < 8:
        issues.append("密码长度至少为8个字符")

    if not re.search(r'[a-z]', password):
        issues.append("密码至少包含一个小写字母")

    if not re.search(r'[A-Z]', password):
        issues.append("密码至少包含一个大写字母")

    if not re.search(r'[0-9]', password):
        issues.append("密码至少包含一个数字")

    if not re.search(r'[^a-zA-Z0-9]', password):
        issues.append("密码至少包含一个特殊字符")

    return issues


def validate_username(username: str) -> List[str]:
    """验证用户名格式

    Args:
        username: 用户名

    Returns:
        List[str]: 用户名问题列表，为空表示用户名格式符合要求

    """
    issues = []

    if len(username) < 3:
        issues.append("用户名长度至少为3个字符")

    if len(username) > 20:
        issues.append("用户名长度不能超过20个字符")

    # 只允许字母、数字、下划线和连字符
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        issues.append("用户名只能包含字母、数字、下划线和连字符")

    return issues


def validate_phone(phone: str) -> bool:
    """验证手机号格式是否正确（支持中国大陆手机号）

    Args:
        phone: 手机号

    Returns:
        bool: 手机号格式正确返回True，否则返回False

    """
    phone_pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(phone_pattern, phone))


def validate_url(url: str) -> bool:
    """验证URL格式是否正确

    Args:
        url: URL地址

    Returns:
        bool: URL格式正确返回True，否则返回False

    """
    url_pattern = r'^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$'
    return bool(re.match(url_pattern, url))
