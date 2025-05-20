from typing import Annotated
from fastapi import APIRouter, Query, Security

from core.exceptions.client_errors import AuthenticationError, ResourceNotFoundError
from schemas.common import DataResponse, MessageResponse, PaginatedResponse
from schemas.users import (
    AdminUpdatePassword,
    UserResponse,
    UserPaginationParams,
    UserUpdate,
    UserUpdateByAdmin,
    UserUpdatePassword,
)
from services.user_service import UserService
from utils.security import (
    verify_current_admin_user,
    verify_current_user,
    verify_password,
)


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def get_users(
    params: Annotated[UserPaginationParams, Query()],
    payload=Security(verify_current_admin_user),
):
  data = await UserService.get_users(params)
  return PaginatedResponse(data=data)


@router.get("/me", response_model=DataResponse[UserResponse])
async def get_current_user(
    payload=Security(verify_current_user),
):
  user = await UserService.get_user_by_id(payload.id)
  return DataResponse(data=user)


@router.get("/{user_id}", response_model=DataResponse[UserResponse])
async def get_user(
    user_id: int,
):
  user = await UserService.get_user_by_id(user_id)
  return DataResponse(data=user)


@router.put("/me", response_model=DataResponse[UserResponse])
async def update_current_user(
    update_fields: UserUpdate,
    payload=Security(verify_current_user),
):
  user = await UserService.update_user(payload.id, update_fields)
  return DataResponse(data=user)


@router.put("/me/password", response_model=MessageResponse)
async def update_current_user_password(
    update_fields: UserUpdatePassword,
    payload=Security(verify_current_user),
):
  user = await UserService.get_user_by_id(payload.id)
  if verify_password(update_fields.old_password, user.password_hash):
    await UserService.update_user_password(payload.id, update_fields.new_password)
    return MessageResponse(message="用户密码更新成功")
  raise AuthenticationError(message="旧密码错误")


@router.put("/{user_id}/password", response_model=MessageResponse)
async def update_user_password(
    user_id: int,
    update_fields: AdminUpdatePassword,
    payload=Security(verify_current_admin_user),
):
  await UserService.update_user_password(user_id, update_fields.new_password)
  return MessageResponse(message="用户密码更新成功")


@router.put("/{user_id}", response_model=DataResponse[UserResponse])
async def update_user(
    user_id: int,
    update_fields: UserUpdateByAdmin,
    payload=Security(verify_current_admin_user),
):
  user = await UserService.update_user(user_id, update_fields)
  return DataResponse(data=user)
