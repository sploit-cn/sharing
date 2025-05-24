from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from schemas.users import UserRelatedResponse


class RatingBase(BaseModel):
  score: int = Field(ge=0, le=10)
  is_used: bool = False


class RatingCreate(RatingBase):
  pass


class RatingUpdate(BaseModel):
  score: Optional[int] = Field(None, ge=0, le=10)
  is_used: Optional[bool] = None


class RatingResponse(RatingBase):
  id: int
  project_id: int
  user_id: int

  class Config:
    from_attributes = True


class RatingModifiedResponse(BaseModel):
  average_rating: float
  rating_count: int


class RatingUserResponse(RatingBase):
  id: int
  user: UserRelatedResponse
  updated_at: datetime


class RatingDistributionResponse(BaseModel):
  ratings: list[RatingUserResponse]
  distribution: dict[int, int]

  class Config:
    from_attributes = True
