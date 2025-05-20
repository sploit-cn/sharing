from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from config import Settings
from core.exceptions import ResourceConflictError
from core.exceptions.base import CustomBaseException
from core.exceptions.client_errors import PermissionDeniedError
from models.models import OAuthAccount, Platform, Role, User
from schemas.common import DataResponse
from schemas.users import UserCreate, UserResponse
from services.auth_service import AuthService
from utils.github_api import GitHubAPI
from utils.gitee_api import GiteeAPI
from utils.security import (
    OAuthPayloadData,
    create_oauth_access_token,
    create_user_access_token,
    get_password_hash,
    verify_current_oauth,
)
from utils.time import now

router = APIRouter()


# JWT令牌模型
class LoginResponse(BaseModel):
  access_token: str
  token_type: str
  user: UserResponse


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Security(),
) -> LoginResponse:
  """用户登录"""
  user = await AuthService.authenticate_user(form_data.username, form_data.password)
  # 此处错误处理兼容 Swagger UI，使用 HTTP Error code
  if not user:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"},
    )
  if not user.in_use:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="用户已注销或被封禁",
    )

  # 更新最后登录时间
  user.last_login = now()
  await user.save()
  # 创建访问令牌
  access_token = create_user_access_token(user=user)
  # 构建用户数据
  user_data = UserResponse.model_validate(user)

  return LoginResponse(access_token=access_token, token_type="bearer", user=user_data)


@router.post("/register", response_model=DataResponse[LoginResponse])
async def register(user_data: UserCreate) -> DataResponse[LoginResponse]:
  """注册用户"""
  # 检查用户名是否已存在
  if await User.filter(username=user_data.username).exists():
    raise ResourceConflictError(resource="用户名")

  # 检查邮箱是否已存在
  if await User.filter(email=user_data.email).exists():
    raise ResourceConflictError(resource="邮箱")

  # 创建用户
  now_time = now()
  user = await User.create(
      username=user_data.username,
      email=user_data.email,
      password_hash=get_password_hash(user_data.password),
      last_login=now_time,
      updated_at=now_time,
      role=Role.USER,
  )
  access_token = create_user_access_token(user=user)

  return DataResponse(
      data=LoginResponse(
          access_token=access_token,
          token_type="bearer",
          user=UserResponse.model_validate(user),
      )
  )


# https://github.com/login/oauth/authorize?client_id=Ov23liCF21cB290Tihuy&scope=user%3Aemail
@router.get("/github")
async def get_github_url():
  encoded_params = urlencode(
      {
          "client_id": Settings.GITHUB_CLIENT_ID,
          "redirect_uri": Settings.GITHUB_REDIRECT_URI,
          "scope": "user:email",
      }
  )
  github_url = f"https://github.com/login/oauth/authorize?{encoded_params}"
  return DataResponse(data=github_url)


@router.get("/github/callback")
async def github_callback(code: str):
  try:
    access_token = await AuthService.github_auth(code)
    github_user = await GitHubAPI.get_current_user(access_token)
    github_id = github_user["id"]
    github_name = github_user["login"]
    github_avatar = github_user["avatar_url"]
    user = await User.get_or_none(github_id=github_id)
    # 若已注册且绑定账号
    if user:
      if not user.in_use:
        raise PermissionDeniedError("用户已注销或被封禁")
      user.github_name = github_name
      if user.avatar is None:
        user.avatar = github_avatar
      user.last_login = now()
      await user.save()
      user_jwt_token = create_user_access_token(user)
      token_encoded = urlencode({"token": user_jwt_token})
      await OAuthAccount.update_or_create(
          defaults={"access_token": access_token},
          platform=Platform.GITHUB,
          platform_id=github_id,
          user_id=user.id,
      )
      return RedirectResponse(url=f"/oauth-success?{token_encoded}")
    # 若用户未绑定过 OAuth，检查用户是否已用邮箱注册过账号
    github_emails = await GitHubAPI.get_current_user_emails(access_token)
    primary_email_address = None
    for email in github_emails:
      if email["primary"] and email["verified"]:
        primary_email_address = email["email"]
        break
    user = await User.get_or_none(email=primary_email_address)
    # 若用户邮箱已注册账号，直接绑定并登录
    if user:
      if not user.in_use:
        raise PermissionDeniedError("邮箱关联用户已注销或被封禁")
      now_time = now()
      user.github_id = github_id
      user.github_name = github_name
      if user.avatar is None:
        user.avatar = github_avatar
      user.last_login = now_time
      user.updated_at = now_time
      await user.save()
      user_jwt_token = create_user_access_token(user)
      token_encoded = urlencode({"token": user_jwt_token})
      await OAuthAccount.update_or_create(
          defaults={"access_token": access_token},
          platform=Platform.GITHUB,
          platform_id=github_id,
          user_id=user.id,
      )
      return RedirectResponse(url=f"/oauth-success?{token_encoded}")
    # 若未注册，跳转注册
    oauth_jwt_token = create_oauth_access_token(
        Platform.GITHUB, github_id, github_name)
    token_encoded = urlencode(
        {"token": oauth_jwt_token, "email": primary_email_address}
    )
    await OAuthAccount.update_or_create(
        defaults={"access_token": access_token},
        platform=Platform.GITHUB,
        platform_id=github_id,
    )
    return RedirectResponse(url=f"/oauth-register?{token_encoded}")
  except Exception as e:
    message_encoded = urlencode({"message": str(e)})
    return RedirectResponse(url=f"/oauth-failure?{message_encoded}")


# https://gitee.com/oauth/authorize?client_id=e53d4be774ef8d561f479640f06d05befd932ea2053621f8700843d534e4ffd1&redirect_uri=http://127.0.0.1:8000/auth/gitee/callback&response_type=code&scope=user_info%20emails
@router.get("/gitee")
async def get_gitee_url():
  encoded_params = urlencode(
      {
          "client_id": Settings.GITEE_CLIENT_ID,
          "redirect_uri": Settings.GITEE_REDIRECT_URI,
          "response_type": "code",
          "scope": "user_info emails",
      }
  )
  gitee_url = f"https://gitee.com/oauth/authorize?{encoded_params}"
  return DataResponse(data=gitee_url)


@router.get("/gitee/callback")
async def gitee_callback(code: str):
  try:
    access_token, refresh_token = await AuthService.gitee_auth(code)
    # 获取用户信息
    gitee_user_data = await GiteeAPI.get_current_user(access_token)
    gitee_id = gitee_user_data["id"]
    gitee_name = gitee_user_data["login"]
    gitee_avatar = gitee_user_data["avatar_url"]
    user = await User.get_or_none(gitee_id=gitee_id)
    # 若已注册且绑定账号
    if user:
      if not user.in_use:
        raise PermissionDeniedError("邮箱关联用户已注销或被封禁")
      user.gitee_name = gitee_name
      if user.avatar is None:
        user.avatar = gitee_avatar
      user.last_login = now()
      await user.save()
      user_jwt_token = create_user_access_token(user)
      token_encoded = urlencode({"token": user_jwt_token})
      await OAuthAccount.update_or_create(
          defaults={"access_token": access_token,
                    "refresh_token": refresh_token},
          platform=Platform.GITEE,
          platform_id=gitee_id,
          user_id=user.id,
      )
      return RedirectResponse(url=f"/oauth-success?{token_encoded}")
    # 若用户未绑定过 OAuth，检查用户是否已用邮箱注册过账号
    email_address = None
    if gitee_user_data["email"] != "未公开邮箱":
      # 获取用户邮箱
      gitee_emails = await GiteeAPI.get_current_user_emails(access_token)
      for email in gitee_emails:
        if email["state"] == "confirmed" and ("primary" in email["scope"]):
          email_address = email["email"]
          break
      user = await User.get_or_none(email=email_address)
      # 若用户邮箱已注册账号，直接绑定并登录
      if user:
        if not user.in_use:
          raise PermissionDeniedError("邮箱关联用户已注销或被封禁")
        now_time = now()
        user.gitee_id = gitee_id
        user.gitee_name = gitee_name
        if user.avatar is None:
          user.avatar = gitee_avatar
        user.last_login = now_time
        user.updated_at = now_time
        await user.save()
        user_jwt_token = create_user_access_token(user)
        token_encoded = urlencode({"token": user_jwt_token})
        await OAuthAccount.update_or_create(
            defaults={"access_token": access_token,
                      "refresh_token": refresh_token},
            platform=Platform.GITEE,
            platform_id=gitee_id,
            user_id=user.id,
        )
        return RedirectResponse(url=f"/oauth-success?{token_encoded}")
    # 若未注册，跳转注册
    oauth_jwt_token = create_oauth_access_token(
        Platform.GITEE, gitee_id, gitee_name)
    token_encoded = urlencode(
        {"token": oauth_jwt_token, "email": email_address})
    await OAuthAccount.update_or_create(
        defaults={"access_token": access_token,
                  "refresh_token": refresh_token},
        platform=Platform.GITEE,
        platform_id=gitee_id,
    )
    return RedirectResponse(url=f"/oauth-register?{token_encoded}")
  except Exception as e:
    message_encoded = urlencode({"message": str(e)})
    return RedirectResponse(url=f"/oauth-failure?{message_encoded}")


@router.post("/oauth-register", response_model=DataResponse[UserResponse])
async def oauth_register(
    user_data: UserCreate, payload: OAuthPayloadData = Security(verify_current_oauth)
):
  """注册用户"""
  # 检查用户名是否已存在
  if await User.filter(username=user_data.username).exists():
    raise ResourceConflictError(resource="用户名")
  # 检查邮箱是否已存在
  if await User.filter(email=user_data.email).exists():
    raise ResourceConflictError(resource="邮箱")

  # 创建用户
  now_time = now()
  user = None
  if payload.platform is Platform.GITHUB:
    access_token = await AuthService.get_access_token_by_payload(payload)
    github_user = await GitHubAPI.get_current_user(access_token)
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        last_login=now_time,
        updated_at=now_time,
        role=Role.USER,
        github_id=github_user["id"],
        github_name=github_user["login"],
        avatar=github_user["avatar_url"],
    )
    await OAuthAccount.filter(github_id=payload.id).update(user_id=user.id)
  elif payload.platform is Platform.GITEE:
    access_token = await AuthService.get_access_token_by_payload(payload)
    gitee_user = await GiteeAPI.get_current_user(access_token)
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        last_login=now_time,
        updated_at=now_time,
        role=Role.USER,
        gitee_id=gitee_user["id"],
        gitee_name=gitee_user["login"],
        avatar=gitee_user["avatar_url"],
    )
    await OAuthAccount.filter(gitee_id=payload.id).update(user_id=user.id)

  return DataResponse(data=user)
