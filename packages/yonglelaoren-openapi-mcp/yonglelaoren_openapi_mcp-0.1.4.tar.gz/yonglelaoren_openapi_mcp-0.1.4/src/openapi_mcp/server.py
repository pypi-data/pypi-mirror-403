"""MCP 服务器入口。"""

from mcp.server.fastmcp import FastMCP

from .config import config
from .tools import register_get_endpoint_details_tool, register_list_endpoints_tool


def create_server() -> FastMCP:
    """创建 MCP 服务器实例。

    Returns:
        FastMCP 服务器实例
    """
    mcp = FastMCP(config.server_name)

    # 注册工具
    register_list_endpoints_tool(mcp)
    register_get_endpoint_details_tool(mcp)

    return mcp


def get_server() -> FastMCP:
    """获取 MCP 服务器实例（单例模式）。

    Returns:
        FastMCP 服务器实例
    """
    if not hasattr(get_server, "_instance"):
        get_server._instance = create_server()
    return get_server._instance