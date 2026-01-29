"""获取接口详细信息的工具。"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..parsers.openapi_parser import OpenAPIParser


def register_get_endpoint_details_tool(mcp: FastMCP) -> None:
    """注册获取接口详细信息的工具。

    Args:
        mcp: FastMCP 服务器实例
    """

    @mcp.tool()
    def get_endpoint_details(spec_source: str, path: str, method: str) -> dict[str, Any]:
        """获取 OpenAPI 规范中指定接口的详细信息。

        Args:
            spec_source: OpenAPI 规范来源（文件路径或 URL）
            path: 接口路径（例如：/users/{id}）
            method: HTTP 方法（GET, POST, PUT, DELETE 等）

        Returns:
            接口详细信息，包括参数、请求体、响应等

        Raises:
            ValueError: 接口不存在时抛出异常
            Exception: 加载或解析规范失败时抛出异常
        """
        try:
            parser = OpenAPIParser(spec_source)
            endpoint = parser.get_endpoint_details(path, method)
            return endpoint.model_dump()
        except ValueError as e:
            raise ValueError(f"获取接口详情失败: {e}") from e
        except Exception as e:
            raise Exception(f"获取接口详情失败: {e}") from e