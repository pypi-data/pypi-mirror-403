"""列出所有接口的工具。"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..parsers.openapi_parser import OpenAPIParser


def register_list_endpoints_tool(mcp: FastMCP) -> None:
    """注册列出所有接口的工具。

    Args:
        mcp: FastMCP 服务器实例
    """

    @mcp.tool()
    def list_endpoints(spec_source: str) -> list[dict[str, Any]]:
        """列出 OpenAPI 规范中的所有接口。

        Args:
            spec_source: OpenAPI 规范来源（文件路径或 URL）

        Returns:
            接口列表，每个接口包含路径、方法、摘要和描述

        Raises:
            Exception: 加载或解析规范失败时抛出异常
        """
        try:
            parser = OpenAPIParser(spec_source)
            endpoints = parser.list_endpoints()
            return [endpoint.model_dump() for endpoint in endpoints]
        except Exception as e:
            raise Exception(f"列出接口失败: {e}") from e