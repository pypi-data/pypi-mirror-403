"""接口相关数据模型。"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .openapi import Parameter, RequestBody, Response


class EndpointSummary(BaseModel):
    """接口摘要。"""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    tags: Optional[List[str]] = None


class EndpointDetail(BaseModel):
    """接口详细信息。"""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    tags: Optional[List[str]] = None
    parameters: List[Parameter] = Field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: Dict[str, Response] = Field(default_factory=dict)
    security: Optional[List[Dict[str, Any]]] = None
    deprecated: bool = False