"""配置管理。"""

import os
from typing import Optional


class Config:
    """应用配置。"""

    def __init__(self) -> None:
        """初始化配置。"""
        self._server_name: str = os.getenv("MCP_SERVER_NAME", "openapi-mcp")
        self._server_version: str = os.getenv("MCP_SERVER_VERSION", "0.1.0")
        self._log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def server_name(self) -> str:
        """获取服务器名称。"""
        return self._server_name

    @property
    def server_version(self) -> str:
        """获取服务器版本。"""
        return self._server_version

    @property
    def log_level(self) -> str:
        """获取日志级别。"""
        return self._log_level


# 全局配置实例
config = Config()