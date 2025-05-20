from fastapi import APIRouter, Security

from core.exceptions.client_errors import PermissionDeniedError
from models.models import Role
from schemas.comments import CommentCreate, CommentResponse
from schemas.common import DataResponse, MessageResponse
from services.comment_service import CommentService
from services.notification_service import NotificationService
from services.project_service import ProjectService
from utils.security import UserPayloadData, verify_current_user

router = APIRouter()


@router.post("/", response_model=DataResponse[CommentResponse])
async def create_comment(comment_create: CommentCreate, payload: UserPayloadData = Security(verify_current_user)):
  comment = await CommentService.create_comment(payload.id, comment_create)
  project = await ProjectService.get_project_shallow(comment.project_id)
  if comment_create.parent_id is not None:
    parent_comment = await CommentService.get_comment(comment_create.parent_id)
    await NotificationService.notify_user(f"您在项目 {project.name} 的评论有新的回复", user_id=parent_comment.user_id, related_project=comment.project_id, related_comment=comment.id)
  else:
    await NotificationService.notify_admins(f"您分享的项目 {project.name} 有新的评论", related_project=comment.project_id, related_comment=comment.id)
  return DataResponse(data=comment)


@router.get("/{comment_id}", response_model=DataResponse[CommentResponse])
async def get_comment(comment_id: int):
  comment = await CommentService.get_comment(comment_id)
  return DataResponse(data=comment)


@router.get("/{comment_id}/replies", response_model=DataResponse[list[CommentResponse]])
async def get_comment_replies(comment_id: int):
  replies = await CommentService.get_comment_replies(comment_id)
  return DataResponse(data=replies)


@router.delete("/{comment_id}", response_model=MessageResponse)
async def delete_comment(comment_id: int, payload: UserPayloadData = Security(verify_current_user)):
  comment = await CommentService.get_comment(comment_id)
  if comment.user.id != payload.id and payload.role != Role.ADMIN:
    raise PermissionDeniedError(message="您无权删除此评论")
  await CommentService.delete_comment(comment_id)
  return MessageResponse(message="评论删除成功")
