"""解析器基类和接口。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..models.endpoint import EndpointDetail, EndpointSummary


class BaseParser(ABC):
    """解析器基类。"""

    @abstractmethod
    def load_spec(self, source: str) -> Dict[str, Any]:
        """加载 OpenAPI 规范。

        Args:
            source: 规范来源（文件路径或 URL）

        Returns:
            解析后的规范字典

        Raises:
            Exception: 加载失败时抛出异常
        """
        pass

    @abstractmethod
    def list_endpoints(self) -> List[EndpointSummary]:
        """列出所有接口。

        Returns:
            接口摘要列表
        """
        pass

    @abstractmethod
    def get_endpoint_details(self, path: str, method: str) -> EndpointDetail:
        """获取接口详细信息。

        Args:
            path: 接口路径
            method: HTTP 方法（GET, POST, PUT, DELETE 等）

        Returns:
            接口详细信息

        Raises:
            ValueError: 接口不存在时抛出异常
        """
        pass