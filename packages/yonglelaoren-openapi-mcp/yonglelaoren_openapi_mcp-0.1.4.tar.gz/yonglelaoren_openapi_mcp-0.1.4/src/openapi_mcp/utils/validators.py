"""输入验证器。"""

import re
from typing import Optional


def validate_http_method(method: str) -> bool:
    """验证 HTTP 方法是否有效。

    Args:
        method: HTTP 方法字符串

    Returns:
        如果方法有效返回 True，否则返回 False
    """
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
    return method.upper() in valid_methods


def validate_url(url: str) -> bool:
    """验证 URL 格式是否有效。

    Args:
        url: URL 字符串

    Returns:
        如果 URL 有效返回 True，否则返回 False
    """
    url_pattern = re.compile(
        r"^(https?|ftp)://"  # 协议
        r"([A-Za-z0-9-]+\.)+[A-Za-z]{2,}"  # 域名
        r"(:\d{1,5})?"  # 端口（可选）
        r"(/.*)?$"  # 路径（可选）
    )
    return bool(url_pattern.match(url))


def validate_path(path: str) -> bool:
    """验证接口路径格式是否有效。

    Args:
        path: 接口路径字符串

    Returns:
        如果路径有效返回 True，否则返回 False
    """
    if not path or not path.startswith("/"):
        return False
    return True


def validate_spec_source(source: str) -> bool:
    """验证 OpenAPI 规范来源是否有效。

    Args:
        source: 规范来源（文件路径或 URL）

    Returns:
        如果来源有效返回 True，否则返回 False
    """
    # 检查是否为 URL
    if validate_url(source):
        return True

    # 检查是否为文件路径（简单验证）
    if source.endswith((".json", ".yaml", ".yml")):
        return True

    return False