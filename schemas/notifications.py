from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from schemas.comments import CommentRelatedResponse
from schemas.projects import ProjectRelatedResponse


class NotificationResponse(BaseModel):
  id: int
  user_id: int
  content: str
  is_read: bool
  created_at: datetime
  related_project: Optional[ProjectRelatedResponse] = None
  related_comment: Optional[CommentRelatedResponse] = None

  class Config:
    from_attributes = True
