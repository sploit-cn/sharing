from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from schemas.users import UserRelatedResponse


class CommentRelatedResponse(BaseModel):
  id: int
  content: str
  user_id: int
  project_id: int

  class Config:
    from_attributes = True


class CommentCreate(BaseModel):
  project_id: int
  content: str
  parent_id: Optional[int] = None


class CommentResponse(BaseModel):
  id: int
  content: str
  user: UserRelatedResponse
  project_id: int
  parent_id: Optional[int] = None
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True
