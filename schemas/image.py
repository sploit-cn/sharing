from uuid import UUID
from typing import Optional
from pydantic import Field
from pydantic.main import BaseModel


class ImageBase(BaseModel):
  """图片基础信息"""

  original_name: str = Field(max_length=255)
  project_id: Optional[int] = None
  alt: Optional[str] = None


class ImageCreate(ImageBase):
  """创建图片请求模型"""

  pass


class ImageUpdate(BaseModel):
  """更新图片请求模型"""

  alt: Optional[str] = None


class ImageResponse(ImageBase):
  """图片响应模型"""

  id: int
  uuid: UUID

  class Config:
    from_attributes = True
