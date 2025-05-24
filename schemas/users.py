from typing import Literal, Optional
from datetime import datetime
from fastapi import Query
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from models.models import Role
from schemas.common import Order, PaginationParams


class UserBase(BaseModel):
  username: str = Field(
      min_length=3,
      max_length=20,
      pattern=r"^[a-zA-Z0-9_\-]+$",  # 匹配字母、数字和下划线、横线
      description="用户名，长度3-20，只能包含字母、数字、下划线、横线",
  )

  email: EmailStr


class UserLogin(BaseModel):
  username: str
  password: str


class UserCreate(UserBase):
  password: str = Field(min_length=6)


class UserUpdate(BaseModel):
  email: Optional[EmailStr] = None
  avatar: Optional[HttpUrl] = None
  bio: Optional[str] = None


class UserUpdatePassword(BaseModel):
  old_password: str = Field(min_length=6)
  new_password: str = Field(min_length=6)


class AdminUpdatePassword(BaseModel):
  new_password: str = Field(min_length=6)


class UserUpdateByAdmin(UserUpdate):
  role: Optional[Role] = None
  in_use: Optional[bool] = None


class UserResponse(BaseModel):
  id: int
  username: str
  email: str
  avatar: Optional[str] = None
  bio: str
  role: Role
  created_at: datetime
  updated_at: datetime
  last_login: datetime
  github_id: Optional[int] = None
  gitee_id: Optional[int] = None
  github_name: Optional[str] = None
  gitee_name: Optional[str] = None
  in_use: bool

  class Config:
    from_attributes = True


class UserRelatedResponse(BaseModel):
  id: int
  username: str
  avatar: Optional[str] = None
  bio: str
  in_use: bool

  class Config:
    from_attributes = True


UserFields = Literal[
    "id",
    "avatar",
    "bio",
    "role",
    "created_at",
    "updated_at",
    "last_login",
    "github_id",
    "gitee_id",
    "github_name",
    "gitee_name",
    "in_use",
]


class UserPaginationParams(PaginationParams):
  order_by: UserFields = Query("id")
  order: Order = Query("asc")


class OAuthLogin(BaseModel):
  """OAuth登录请求"""

  platform: str
  code: str
  redirect_uri: str


# class PasswordReset(BaseModel):
#   """密码重置请求"""

#   email: EmailStr


# class PasswordResetConfirm(BaseModel):
#   """密码重置确认"""

#   token: str
#   new_password: str = Field(min_length=6, description="密码，长度至少为6位")
