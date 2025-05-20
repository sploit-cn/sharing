from typing import Optional
from pydantic import BaseModel, Field


class RatingBase(BaseModel):
  score: float = Field(ge=0, le=10)
  is_used: bool = False


class RatingCreate(RatingBase):
  pass


class RatingUpdate(RatingBase):
  score: Optional[float] = Field(None, ge=0, le=10)
  is_used: Optional[bool] = None


class RatingResponse(RatingBase):
  id: int
  project_id: int
  user_id: int

  class Config:
    from_attributes = True
