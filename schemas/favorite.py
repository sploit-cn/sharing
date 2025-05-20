from pydantic import BaseModel

from schemas.projects import ProjectRelatedResponse
from schemas.users import UserRelatedResponse


class FavoriteResponse(BaseModel):
  id: int
  project_id: int
  user_id: int

  class Config:
    from_attributes = True


class FavoriteUserResponse(BaseModel):
  id: int
  project_id: int
  user: UserRelatedResponse

  class Config:
    from_attributes = True


class FavoriteProjectResponse(BaseModel):
  id: int
  project: ProjectRelatedResponse
  user_id: int

  class Config:
    from_attributes = True
