from typing import Optional
from pydantic import BaseModel, Field


class TagBase(BaseModel):
  """标签基础信息"""

  name: str = Field(max_length=100)
  category: str = Field("默认分类", max_length=100)
  description: str = Field("", max_length=255)


class TagCreate(TagBase):
  """创建标签请求模型"""

  pass


class TagUpdate(BaseModel):
  """更新标签请求模型"""

  name: Optional[str] = Field(None, max_length=100)
  category: Optional[str] = Field(None, max_length=100)
  description: Optional[str] = Field(None, max_length=255)


class TagResponse(TagBase):
  """标签响应模型"""

  id: int

  class Config:
    from_attributes = True
