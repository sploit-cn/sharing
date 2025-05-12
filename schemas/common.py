from typing import Generic, Literal, TypeVar, List

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")
Order = Literal["asc", "desc"]


class ResponseBase(BaseModel):
  """基础响应模型"""

  code: int = 200
  message: str = "成功"


class MessageResponse(ResponseBase):
  """消息响应模型"""

  pass


class ErrorResponse(BaseModel):
  """错误响应模型"""

  code: int = 500
  message: str = "服务器错误"
  pass


class ValidationErrorResponse(ErrorResponse):
  """验证错误响应模型"""

  fields: dict[str, str | list[str]] = {}
  pass


class DataResponse(ResponseBase, Generic[T]):
  """数据响应模型"""

  data: T


class PaginationParams(BaseModel):
  """分页参数模型"""

  page: int = Query(1, ge=1)
  page_size: int = Query(20, ge=1, le=100)


class PaginatedData(BaseModel, Generic[T]):
  """分页数据模型"""

  items: List[T]
  total: int
  page: int
  page_size: int
  pages: int


class PaginatedResponse(ResponseBase, Generic[T]):
  """分页响应模型"""

  data: PaginatedData[T]


class OAuthCallbackUrl(BaseModel):
  """OAuth回调URL模型"""

  url: str


class SyncStatus(BaseModel):
  """同步状态模型"""

  status: str
  message: str


class HttpExceptionDetail(BaseModel):
  """HTTP异常详情模型"""

  detail: str
