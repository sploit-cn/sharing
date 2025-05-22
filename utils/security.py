from datetime import timedelta, datetime, UTC
from typing import Optional

from fastapi import Cookie, Security, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette import status

from config import Settings
from core.exceptions.client_errors import AuthenticationError, PermissionDeniedError
from models.models import Platform, Role, User

# 密码上下文，用于哈希和验证密码
pwd_context = CryptContext(schemes=["bcrypt"])


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
  return pwd_context.hash(password)


def get_credentials_exception():
  return HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="无效的身份验证凭据",
      headers={"WWW-Authenticate": "Bearer"},
  )


# JWT令牌数据模型
class UserPayloadData(BaseModel):
  name: str
  id: int
  role: Role


class OAuthPayloadData(BaseModel):
  platform: Platform
  id: int
  name: str


# OAuth2密码流
oauth2_password_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login_form", auto_error=False)
bearer_scheme = HTTPBearer()


def create_user_access_token(user: User, expires_delta: timedelta | None = None) -> str:
  """创建用户访问令牌"""
  data = UserPayloadData(name=user.username, id=user.id, role=user.role)
  return create_access_token(data.model_dump(), expires_delta)


def create_oauth_access_token(
    platform: Platform, id: int, name: str, expires_delta: timedelta | None = None
) -> str:
  """创建OAuth访问令牌"""
  data = OAuthPayloadData(platform=platform, id=id, name=name)
  return create_access_token(data.model_dump(), expires_delta)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
  """创建JWT令牌"""
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(UTC) + expires_delta
  else:
    expire = datetime.now(
        UTC) + timedelta(seconds=Settings.ACCESS_TOKEN_EXPIRE_SECONDS)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(
      to_encode, Settings.JWT_SECRET_KEY, algorithm=Settings.JWT_ALGORITHM
  )
  return encoded_jwt


async def verify_current_user(
    header_token: Optional[str] = Security(oauth2_password_scheme),
    user_token: Optional[str] = Cookie(None),
) -> UserPayloadData:
  """获取当前用户"""
  try:
    token = header_token or user_token
    if not token:
      raise AuthenticationError(auth="JWT Token")
    payload = jwt.decode(
        token, Settings.JWT_SECRET_KEY, algorithms=[Settings.JWT_ALGORITHM]
    )
    return UserPayloadData.model_validate(payload)
  except Exception:
    raise AuthenticationError(auth="JWT Token")


async def verify_current_admin_user(
    payload: UserPayloadData = Security(verify_current_user),
) -> UserPayloadData:
  """获取当前管理员用户"""
  if payload.role != Role.ADMIN:
    raise PermissionDeniedError()
  return payload


async def verify_current_oauth(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> OAuthPayloadData:
  """获取当前OAuth用户"""
  try:
    payload = jwt.decode(
        credentials.credentials, Settings.JWT_SECRET_KEY, algorithms=[
            Settings.JWT_ALGORITHM]
    )
    return OAuthPayloadData.model_validate(payload)
  except Exception:
    raise AuthenticationError(auth="OAuth JWT Token")
