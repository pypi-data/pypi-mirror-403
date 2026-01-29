"""输出格式化工具。"""

from typing import Any, Dict, List

import yaml


def format_endpoint_summary(endpoint: Dict[str, Any]) -> str:
    """格式化接口摘要。

    Args:
        endpoint: 接口摘要字典

    Returns:
        格式化后的字符串
    """
    path = endpoint.get("path", "")
    method = endpoint.get("method", "")
    summary = endpoint.get("summary", "")
    description = endpoint.get("description", "")

    lines = [
        f"{method} {path}",
    ]

    if summary:
        lines.append(f"  摘要: {summary}")

    if description:
        lines.append(f"  描述: {description}")

    return "\n".join(lines)


def format_endpoint_detail(endpoint: Dict[str, Any]) -> str:
    """格式化接口详细信息。

    Args:
        endpoint: 接口详细信息字典

    Returns:
        格式化后的字符串
    """
    path = endpoint.get("path", "")
    method = endpoint.get("method", "")
    summary = endpoint.get("summary", "")
    description = endpoint.get("description", "")
    operation_id = endpoint.get("operation_id", "")
    tags = endpoint.get("tags", [])
    parameters = endpoint.get("parameters", [])
    request_body = endpoint.get("request_body")
    responses = endpoint.get("responses", {})
    deprecated = endpoint.get("deprecated", False)

    lines = [
        f"{method} {path}",
    ]

    if deprecated:
        lines.append("  ⚠️ 已废弃")

    if summary:
        lines.append(f"  摘要: {summary}")

    if description:
        lines.append(f"  描述: {description}")

    if operation_id:
        lines.append(f"  操作 ID: {operation_id}")

    if tags:
        lines.append(f"  标签: {', '.join(tags)}")

    if parameters:
        lines.append("  参数:")
        for param in parameters:
            param_name = param.get("name", "")
            param_in = param.get("in_", "")
            param_required = " (必需)" if param.get("required") else ""
            param_desc = param.get("description", "")
            lines.append(f"    - {param_name} [{param_in}]{param_required}")
            if param_desc:
                lines.append(f"      {param_desc}")

    if request_body:
        lines.append("  请求体:")
        req_desc = request_body.get("description", "")
        if req_desc:
            lines.append(f"    描述: {req_desc}")
        content = request_body.get("content", {})
        for media_type, media_type_obj in content.items():
            lines.append(f"    - {media_type}")
            if media_type_obj.get("example"):
                lines.append(f"      示例: {media_type_obj['example']}")

    if responses:
        lines.append("  响应:")
        for status_code, response in responses.items():
            resp_desc = response.get("description", "")
            lines.append(f"    - {status_code}: {resp_desc}")

    return "\n".join(lines)


def format_yaml(data: Any) -> str:
    """格式化为 YAML 字符串。

    Args:
        data: 要格式化的数据

    Returns:
        YAML 格式字符串
    """
    return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)