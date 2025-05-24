from tortoise import fields, validators
from tortoise.models import Model

# from tortoise.contrib.pydantic import pydantic_model_creator
from enum import Enum


class CreateTimeMixin:
  created_at = fields.DatetimeField(auto_now_add=True)


class CreateUpdateTimeMixin:
  created_at = fields.DatetimeField(auto_now_add=True)
  updated_at = fields.DatetimeField(auto_now=True)


class Role(str, Enum):
  USER = "user"
  ADMIN = "admin"


class Platform(str, Enum):
  GITHUB = "GitHub"
  GITEE = "Gitee"


class User(CreateTimeMixin, Model):
  """用户实体类"""

  id = fields.IntField(pk=True)
  username = fields.CharField(max_length=20, unique=True)
  password_hash = fields.CharField(max_length=60, description="bcrypt hash")
  email = fields.CharField(max_length=320, unique=True)
  avatar = fields.CharField(max_length=255, null=True)
  bio = fields.TextField(default="")
  role = fields.CharEnumField(Role, default=Role.USER)
  last_login = fields.DatetimeField()
  github_id = fields.IntField(null=True)
  gitee_id = fields.IntField(null=True)
  github_name = fields.CharField(max_length=40, null=True)
  gitee_name = fields.CharField(max_length=40, null=True)
  in_use = fields.BooleanField(default=True)
  updated_at = fields.DatetimeField()

  # 反向关系
  projects: fields.ReverseRelation["Project"]
  ratings: fields.ReverseRelation["Rating"]
  comments: fields.ReverseRelation["Comment"]
  favorites: fields.ReverseRelation["Favorite"]
  notifications: fields.ReverseRelation["Notification"]
  oauth_accounts: fields.ReverseRelation["OAuthAccount"]
  images: fields.ReverseRelation["Image"]

  class Meta(Model.Meta):
    table = "users"
    indexes = ("username",)


class Project(CreateTimeMixin, Model):
  """项目实体类"""

  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=255)
  brief = fields.CharField(max_length=255, default="")
  description = fields.TextField(default="")
  repo_url = fields.CharField(max_length=255, unique=True)
  website_url = fields.CharField(max_length=255, default="")
  download_url = fields.CharField(max_length=255, null=True)
  stars = fields.IntField(default=0)
  forks = fields.IntField(default=0)
  watchers = fields.IntField(default=0)
  contributors = fields.IntField(default=1)
  issues = fields.IntField(default=0)
  license = fields.CharField(max_length=100, null=True)
  programming_language = fields.CharField(max_length=100, null=True)
  code_example = fields.TextField(null=True)
  last_commit_at = fields.DatetimeField(null=True)
  average_rating = fields.FloatField(default=0)
  rating_count = fields.IntField(default=0)
  repo_created_at = fields.DatetimeField(null=True)
  last_sync_at = fields.DatetimeField(null=True)
  platform = fields.CharEnumField(Platform)
  repo_id = fields.CharField(max_length=255)
  owner_platform_id = fields.IntField(null=True)
  submitter: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="projects", on_delete=fields.OnDelete.NO_ACTION
  )
  is_approved = fields.BooleanField(default=False, description="是否审核通过")
  approval_date = fields.DatetimeField(null=True)
  view_count = fields.IntField(default=0)
  is_featured = fields.BooleanField(default=False, description="是否精选")
  avatar = fields.CharField(max_length=255, null=True)
  updated_at = fields.DatetimeField()

  # 反向关系
  tags: fields.ManyToManyRelation["Tag"] = fields.ManyToManyField(
    "models.Tag", related_name="projects", through="project_tags"
  )
  ratings: fields.ReverseRelation["Rating"]
  comments: fields.ReverseRelation["Comment"]
  favorites: fields.ReverseRelation["Favorite"]
  related_notifications: fields.ReverseRelation["Notification"]
  sync_logs: fields.ReverseRelation["SyncLog"]
  images: fields.ReverseRelation["Image"]

  class Meta(Model.Meta):
    table = "projects"
    indexes = (
      "repo_id",
      "programming_language",
      "stars",
      "last_commit_at",
      "created_at",
      "last_sync_at",
    )


class Tag(Model):
  """标签实体类"""

  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=100, unique=True)
  category = fields.CharField(max_length=100, default="默认分类")
  description = fields.CharField(max_length=255, default="")

  # 反向关系
  projects: fields.ManyToManyRelation[Project]

  class Meta(Model.Meta):
    table = "tags"
    indexes = ("name", "category")


class Rating(CreateUpdateTimeMixin, Model):
  """评分实体类"""

  id = fields.IntField(pk=True)
  project: fields.ForeignKeyRelation["Project"] = fields.ForeignKeyField(
    "models.Project", related_name="ratings"
  )
  user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="ratings"
  )
  score = fields.IntField(
    validators=[validators.MinValueValidator(0), validators.MaxValueValidator(10)]
  )
  is_used = fields.BooleanField(default=False)

  class Meta(Model.Meta):
    table = "ratings"
    indexes = ("project_id", "user_id")
    unique_together = (("project_id", "user_id"),)


class Comment(CreateUpdateTimeMixin, Model):
  """评论实体类"""

  id = fields.IntField(pk=True)
  project: fields.ForeignKeyRelation["Project"] = fields.ForeignKeyField(
    "models.Project", related_name="comments"
  )
  user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="comments"
  )
  content = fields.TextField()
  parent: fields.ForeignKeyNullableRelation["Comment"] = fields.ForeignKeyField(
    "models.Comment", related_name="replies", null=True
  )

  # 反向关系
  replies: fields.ReverseRelation["Comment"]
  related_notifications: fields.ReverseRelation["Notification"]

  class Meta(Model.Meta):
    table = "comments"
    indexes = ("project_id", "user_id", "parent_id")


class Favorite(CreateTimeMixin, Model):
  """收藏实体类"""

  id = fields.IntField(pk=True)
  project: fields.ForeignKeyRelation["Project"] = fields.ForeignKeyField(
    "models.Project", related_name="favorites"
  )
  user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="favorites"
  )

  class Meta(Model.Meta):
    table = "favorites"
    unique_together = (("project_id", "user_id"),)
    indexes = ("project_id", "user_id")


class Notification(CreateTimeMixin, Model):
  """通知实体类"""

  id = fields.IntField(pk=True)
  user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="notifications"
  )
  content = fields.TextField()
  is_read = fields.BooleanField(default=False)
  related_project: fields.ForeignKeyNullableRelation["Project"] = (
    fields.ForeignKeyField(
      "models.Project", related_name="related_notifications", null=True
    )
  )
  related_comment: fields.ForeignKeyNullableRelation["Comment"] = (
    fields.ForeignKeyField(
      "models.Comment", related_name="related_notifications", null=True
    )
  )

  class Meta(Model.Meta):
    table = "notifications"
    indexes = ("user_id", "is_read")


class OAuthAccount(CreateUpdateTimeMixin, Model):
  """OAuth账号实体类"""

  id = fields.IntField(pk=True)
  user: fields.ForeignKeyNullableRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="oauth_accounts", null=True
  )
  platform = fields.CharEnumField(Platform)
  platform_id = fields.IntField()
  access_token = fields.CharField(max_length=255)
  refresh_token = fields.CharField(max_length=255, null=True)

  class Meta(Model.Meta):
    table = "oauth_accounts"
    indexes = ("user_id",)


class SyncLog(CreateTimeMixin, Model):
  """同步日志实体类"""

  id = fields.IntField(pk=True)
  project: fields.ForeignKeyRelation["Project"] = fields.ForeignKeyField(
    "models.Project", related_name="sync_logs"
  )
  status = fields.CharField(max_length=20)
  project_detail = fields.JSONField(default=None)

  class Meta(Model.Meta):
    table = "sync_logs"
    indexes = ("project_id",)


class Image(CreateTimeMixin, Model):
  """图片实体类"""

  id = fields.IntField(pk=True)
  file_name = fields.CharField(max_length=255)
  user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
    "models.User", related_name="images", on_delete=fields.OnDelete.NO_ACTION
  )
  project: fields.ForeignKeyNullableRelation["Project"] = fields.ForeignKeyField(
    "models.Project", related_name="images", null=True
  )
  original_name = fields.CharField(max_length=255)
  mime_type = fields.CharField(max_length=50)

  class Meta(Model.Meta):
    table = "images"
    indexes = ("project_id", "user_id", "uuid")
