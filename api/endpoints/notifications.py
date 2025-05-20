from fastapi import APIRouter, Security

from schemas.common import DataResponse, MessageResponse
from schemas.notifications import NotificationResponse
from services.notification_service import NotificationService
from utils.security import UserPayloadData, verify_current_user


router = APIRouter()


@router.get("/", response_model=DataResponse[list[NotificationResponse]])
async def get_notifications(payload: UserPayloadData = Security(verify_current_user)):
  notifications = await NotificationService.get_notifications(payload.id)
  return DataResponse(data=notifications)


@router.put("/", response_model=MessageResponse)
async def read_notification(notification_id: int, payload: UserPayloadData = Security(verify_current_user)):
  await NotificationService.read_notification(notification_id, payload.id)
  return MessageResponse(message="已读")


@router.put("/all", response_model=MessageResponse)
async def read_all_notifications(payload: UserPayloadData = Security(verify_current_user)):
  await NotificationService.read_all_notifications(payload.id)
  return MessageResponse(message="已读")


@router.delete("/", response_model=MessageResponse)
async def delete_notification(notification_id: int, payload: UserPayloadData = Security(verify_current_user)):
  await NotificationService.delete_notification(notification_id, payload.id)
  return MessageResponse(message="删除成功")
