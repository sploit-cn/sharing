from models.models import Comment, User
from schemas.comments import CommentCreate
from tortoise.query_utils import Prefetch
from core.exceptions import ResourceNotFoundError


class CommentService:
  @staticmethod
  async def create_comment(user_id: int, comment_create: CommentCreate):
    comment = await Comment.create(user_id=user_id, **comment_create.model_dump(exclude_unset=True))
    await comment.fetch_related("user")
    return comment

  @staticmethod
  async def get_comment(comment_id: int):
    comment = await Comment.get_or_none(id=comment_id).prefetch_related(
        Prefetch("user", queryset=User.all().only(
            "id", "username", "avatar", "bio", "in_use"))
    )
    if comment is None:
      raise ResourceNotFoundError(resource="评论")
    return comment

  @staticmethod
  async def get_comment_replies(comment_id: int):
    replies = await Comment.filter(parent_id=comment_id).prefetch_related(
        Prefetch("user", queryset=User.all().only(
            "id", "username", "avatar", "bio", "in_use"))
    )
    return replies

  @staticmethod
  async def delete_comment(comment_id: int):
    count = await Comment.filter(id=comment_id).delete()
    if count == 0:
      raise ResourceNotFoundError(resource="评论")
