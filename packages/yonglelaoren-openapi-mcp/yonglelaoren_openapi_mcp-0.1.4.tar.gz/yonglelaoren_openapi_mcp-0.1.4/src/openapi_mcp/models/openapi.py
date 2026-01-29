"""OpenAPI 规范数据模型。"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OpenAPIInfo(BaseModel):
    """OpenAPI 规范信息。"""

    title: str
    version: str
    description: Optional[str] = None


class OpenAPISpec(BaseModel):
    """OpenAPI 规范。"""

    openapi: str
    info: OpenAPIInfo
    paths: Dict[str, Any] = Field(default_factory=dict)
    components: Optional[Dict[str, Any]] = None
    servers: Optional[List[Dict[str, Any]]] = None


class ParameterLocation(str):
    """参数位置枚举。"""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


class Parameter(BaseModel):
    """OpenAPI 参数。"""

    name: str
    in_: str = Field(default="query", alias="in")
    description: Optional[str] = None
    required: bool = False
    schema_: Optional[Dict[str, Any]] = Field(default=None, alias="schema")
    type: Optional[str] = None
    enum: Optional[List[Any]] = None


class MediaType(BaseModel):
    """媒体类型。"""

    schema_: Optional[Dict[str, Any]] = Field(default=None, alias="schema")
    example: Optional[Any] = None
    examples: Optional[Dict[str, Any]] = None


class RequestBody(BaseModel):
    """请求体。"""

    description: Optional[str] = None
    content: Dict[str, MediaType] = Field(default_factory=dict)
    required: bool = False


class Response(BaseModel):
    """响应。"""

    description: str
    content: Optional[Dict[str, MediaType]] = None
    headers: Optional[Dict[str, Any]] = None