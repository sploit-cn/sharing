from datetime import datetime

from pydantic import BaseModel

from schemas.projects import ProjectBaseResponse
from schemas.users import UserRelatedResponse


class FavoriteResponse(BaseModel):
  id: int
  project_id: int
  user_id: int
  created_at: datetime

  class Config:
    from_attributes = True


class FavoriteUserResponse(BaseModel):
  id: int
  project_id: int
  user: UserRelatedResponse
  created_at: datetime

  class Config:
    from_attributes = True


class FavoriteProjectResponse(BaseModel):
  id: int
  project: ProjectBaseResponse
  user_id: int
  created_at: datetime

  class Config:
    from_attributes = True
