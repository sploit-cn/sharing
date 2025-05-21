from typing import Optional
from pydantic.main import BaseModel


class ImageBase(BaseModel):
  """图片基础信息"""

  project_id: Optional[int] = None


class ImageCreate(ImageBase):
  """创建图片请求模型"""

  pass


class ImageResponse(ImageBase):
  """图片响应模型"""

  id: int
  file_name: str
  user_id: int
  original_name: str
  mime_type: str

  class Config:
    from_attributes = True
