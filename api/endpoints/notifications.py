from fastapi import APIRouter, Security

from schemas.common import DataResponse, MessageResponse
from schemas.notifications import (
  NotificationBroadcastCreate,
  NotificationResponse,
  NotificationUserCreate,
)
from services.notification_service import NotificationService
from utils.security import (
  UserPayloadData,
  verify_current_admin_user,
  verify_current_user,
)


router = APIRouter()


@router.get("", response_model=DataResponse[list[NotificationResponse]])
async def get_notifications(payload: UserPayloadData = Security(verify_current_user)):
  notifications = await NotificationService.get_notifications(payload.id)
  return DataResponse(data=notifications)


@router.post("/broadcast", response_model=MessageResponse)
async def create_broadcast_notification(
  notification: NotificationBroadcastCreate,
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  await NotificationService.create_broadcast_notification(notification)
  return MessageResponse(message="通知已创建")


@router.post("/user", response_model=MessageResponse)
async def create_user_notification(
  notification: NotificationUserCreate,
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  await NotificationService.notify_user(notification.content, notification.user_id)
  return MessageResponse(message="通知已创建")


@router.put("/{notification_id}", response_model=MessageResponse)
async def read_notification(
  notification_id: int, payload: UserPayloadData = Security(verify_current_user)
):
  await NotificationService.read_notification(notification_id, payload.id)
  return MessageResponse(message="已读")


@router.put("/all", response_model=MessageResponse)
async def read_all_notifications(
  payload: UserPayloadData = Security(verify_current_user),
):
  await NotificationService.read_all_notifications(payload.id)
  return MessageResponse(message="已读")


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(
  notification_id: int, payload: UserPayloadData = Security(verify_current_user)
):
  await NotificationService.delete_notification(notification_id, payload.id)
  return MessageResponse(message="删除成功")
