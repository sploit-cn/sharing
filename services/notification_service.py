from models.models import Comment, Notification, Project, Role, User
from tortoise.query_utils import Prefetch
from typing import Optional

from schemas.notifications import NotificationBroadcastCreate


class NotificationService:
  @staticmethod
  async def get_notifications(user_id: int):
    notifications = (
        await Notification.filter(user_id=user_id)
        .order_by("-created_at")
        .all()
        .prefetch_related(
            Prefetch(
                "related_project",
                queryset=Project.all().only("id", "name", "repo_id", "avatar", "is_approved"),
            ),
            Prefetch(
                "related_comment",
                queryset=Comment.all().only(
                    "id", "content", "user_id", "project_id", "created_at"
                ),
            ),
        )
    )
    return notifications

  @staticmethod
  async def read_notification(notification_id: int, user_id: int):
    await Notification.filter(id=notification_id, user_id=user_id).update(is_read=True)

  @staticmethod
  async def read_all_notifications(user_id: int):
    await Notification.filter(user_id=user_id).update(is_read=True)

  @staticmethod
  async def delete_notification(notification_id: int, user_id: int):
    await Notification.filter(id=notification_id, user_id=user_id).delete()

  @staticmethod
  async def notify_admins(
      message: str,
      related_project: Optional[int] = None,
      related_comment: Optional[int] = None,
  ):
    admins = await User.filter(role=Role.ADMIN).all()
    for admin in admins:
      await Notification.create(
          user=admin,
          content=message,
          related_project_id=related_project,
          related_comment_id=related_comment,
      )

  @staticmethod
  async def notify_user(
      message: str,
      user_id: int,
      related_project: Optional[int] = None,
      related_comment: Optional[int] = None,
  ):
    await Notification.create(
        user_id=user_id,
        content=message,
        related_project_id=related_project,
        related_comment_id=related_comment,
    )

  @staticmethod
  async def create_broadcast_notification(notification: NotificationBroadcastCreate):
    users = await User.all().only("id")
    # batch create
    await Notification.bulk_create(
        [
            Notification(
                user_id=user.id,
                content=notification.content,
            )
            for user in users
        ]
    )
