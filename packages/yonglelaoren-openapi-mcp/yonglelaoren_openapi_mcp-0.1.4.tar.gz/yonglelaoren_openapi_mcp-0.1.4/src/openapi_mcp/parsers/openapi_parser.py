"""基于 Prance 的 OpenAPI 规范解析器。"""

from typing import Any, Dict, List, Optional

import prance

from ..models.endpoint import EndpointDetail, EndpointSummary
from ..models.openapi import (
    MediaType,
    Parameter,
    RequestBody,
    Response,
)
from .base import BaseParser


class OpenAPIParser(BaseParser):
    """OpenAPI 规范解析器。"""

    def __init__(self, spec_source: str):
        """初始化解析器。

        Args:
            spec_source: 规范来源（文件路径或 URL）
        """
        self.spec_source = spec_source
        self._spec: Optional[Dict[str, Any]] = None
        self._parser: Optional[ResolvingParser] = None

    def load_spec(self, source: str) -> Dict[str, Any]:
        """加载 OpenAPI 规范。

        Args:
            source: 规范来源（文件路径或 URL）

        Returns:
            解析后的规范字典

        Raises:
            Exception: 加载失败时抛出异常
        """
        try:
            self._parser = prance.ResolvingParser(source, backend="openapi-spec-validator")
            self._parser.parse()
            self._spec = self._parser.specification
            return self._spec
        except Exception as e:
            raise Exception(f"加载 OpenAPI 规范失败: {e}") from e

    def _get_spec(self) -> Dict[str, Any]:
        """获取已加载的规范。

        Returns:
            规范字典

        Raises:
            Exception: 规范未加载时抛出异常
        """
        if self._spec is None:
            self.load_spec(self.spec_source)
        return self._spec

    def list_endpoints(self) -> List[EndpointSummary]:
        """列出所有接口。

        Returns:
            接口摘要列表
        """
        spec = self._get_spec()
        endpoints: List[EndpointSummary] = []

        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    if isinstance(operation, dict):
                        endpoint = EndpointSummary(
                            path=path,
                            method=method.upper(),
                            summary=operation.get("summary"),
                            description=operation.get("description"),
                            operation_id=operation.get("operationId"),
                            tags=operation.get("tags"),
                        )
                        endpoints.append(endpoint)

        return endpoints

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
        spec = self._get_spec()
        paths = spec.get("paths", {})

        if path not in paths:
            raise ValueError(f"接口路径不存在: {path}")

        path_item = paths[path]
        if not isinstance(path_item, dict):
            raise ValueError(f"接口路径格式错误: {path}")

        method_lower = method.lower()
        if method_lower not in path_item:
            raise ValueError(f"接口方法不存在: {method} {path}")

        operation = path_item[method_lower]
        if not isinstance(operation, dict):
            raise ValueError(f"接口操作格式错误: {method} {path}")

        # 解析参数
        parameters = self._parse_parameters(operation.get("parameters", []))

        # 解析请求体
        request_body = self._parse_request_body(operation.get("requestBody"))

        # 解析响应
        responses = self._parse_responses(operation.get("responses", {}))

        return EndpointDetail(
            path=path,
            method=method.upper(),
            summary=operation.get("summary"),
            description=operation.get("description"),
            operation_id=operation.get("operationId"),
            tags=operation.get("tags"),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            security=operation.get("security"),
            deprecated=operation.get("deprecated", False),
        )

    def _parse_parameters(self, parameters: List[Dict[str, Any]]) -> List[Parameter]:
        """解析参数。

        Args:
            parameters: 参数字典列表

        Returns:
            参数对象列表
        """
        result: List[Parameter] = []
        for param in parameters:
            if not isinstance(param, dict):
                continue
            result.append(
                Parameter(
                    name=param.get("name", ""),
                    in_=param.get("in", "query"),
                    description=param.get("description"),
                    required=param.get("required", False),
                    schema_=param.get("schema"),
                    type=param.get("type"),
                    enum=param.get("enum"),
                )
            )
        return result

    def _parse_request_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[RequestBody]:
        """解析请求体。

        Args:
            request_body: 请求体字典

        Returns:
            请求体对象
        """
        if not request_body or not isinstance(request_body, dict):
            return None

        content = request_body.get("content", {})
        parsed_content: Dict[str, MediaType] = {}
        for media_type, media_type_obj in content.items():
            if isinstance(media_type_obj, dict):
                parsed_content[media_type] = MediaType(
                    schema_=media_type_obj.get("schema"),
                    example=media_type_obj.get("example"),
                    examples=media_type_obj.get("examples"),
                )

        return RequestBody(
            description=request_body.get("description"),
            content=parsed_content,
            required=request_body.get("required", False),
        )

    def _parse_responses(self, responses: Dict[str, Any]) -> Dict[str, Response]:
        """解析响应。

        Args:
            responses: 响应字典

        Returns:
            响应对象字典
        """
        result: Dict[str, Response] = {}
        for status_code, response_obj in responses.items():
            if not isinstance(response_obj, dict):
                continue

            content = response_obj.get("content")
            parsed_content: Optional[Dict[str, MediaType]] = None
            if content and isinstance(content, dict):
                parsed_content = {}
                for media_type, media_type_obj in content.items():
                    if isinstance(media_type_obj, dict):
                        parsed_content[media_type] = MediaType(
                            schema_=media_type_obj.get("schema"),
                            example=media_type_obj.get("example"),
                            examples=media_type_obj.get("examples"),
                        )

            result[status_code] = Response(
                description=response_obj.get("description", ""),
                content=parsed_content,
                headers=response_obj.get("headers"),
            )

        return result