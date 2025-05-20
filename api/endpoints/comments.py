from fastapi import APIRouter, Security

from core.exceptions.client_errors import PermissionDeniedError
from models.models import Role
from schemas.comments import CommentResponse, CommentUpdate
from schemas.common import DataResponse, MessageResponse
from services.comment_service import CommentService
from utils.security import UserPayloadData, verify_current_user

router = APIRouter()


@router.get("/{comment_id}/replies", response_model=DataResponse[list[CommentResponse]])
async def get_comment_replies(comment_id: int):
  replies = await CommentService.get_comment_replies(comment_id)
  return DataResponse(data=replies)


@router.get("/{comment_id}", response_model=DataResponse[CommentResponse])
async def get_comment(comment_id: int):
  comment = await CommentService.get_comment(comment_id)
  return DataResponse(data=comment)


@router.put("/{comment_id}", response_model=DataResponse[CommentResponse])
async def update_comment(comment_id: int, comment_update: CommentUpdate, payload: UserPayloadData = Security(verify_current_user)):
  comment = await CommentService.get_comment(comment_id)
  if comment.user.id != payload.id and payload.role != Role.ADMIN:
    raise PermissionDeniedError(message="您无权更新此评论")
  comment.content = comment_update.content
  await comment.save()
  return DataResponse(data=comment)


@router.delete("/{comment_id}", response_model=MessageResponse)
async def delete_comment(comment_id: int, payload: UserPayloadData = Security(verify_current_user)):
  comment = await CommentService.get_comment(comment_id)
  if comment.user.id != payload.id and payload.role != Role.ADMIN:
    raise PermissionDeniedError(message="您无权删除此评论")
  await comment.delete()
  return MessageResponse(message="评论删除成功")
