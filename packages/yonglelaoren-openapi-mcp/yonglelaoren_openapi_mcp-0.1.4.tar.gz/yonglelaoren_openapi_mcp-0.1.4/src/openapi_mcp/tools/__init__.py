"""工具模块。"""

from .get_endpoint_details import register_get_endpoint_details_tool
from .list_endpoints import register_list_endpoints_tool

__all__ = ["register_list_endpoints_tool", "register_get_endpoint_details_tool"]