"""OpenAPI MCP Server - 基于 Model Context Protocol 的 OpenAPI 规范解析服务器。"""

from .server import get_server

__version__ = "0.1.4"


def main() -> None:
    """主函数，启动 MCP 服务器。"""
    mcp = get_server()
    mcp.run(transport="stdio")


__all__ = ["main"]