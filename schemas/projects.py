from datetime import datetime
from typing import Literal, Optional
from pydantic import Field, HttpUrl
from pydantic.main import BaseModel

from models.models import Platform
from schemas.common import Order, PaginationParams
from schemas.image import ImageResponse
from schemas.tag import TagResponse
from schemas.users import UserResponse


class ProjectBase(BaseModel):
  """项目基础模型"""

  brief: str = Field("", max_length=255)
  description: str = ""
  code_example: Optional[str] = None
  platform: Platform
  repo_id: str = Field(max_length=255)


class ProjectCreate(ProjectBase):
  """创建项目请求模型"""

  tag_ids: list[int] = []
  image_ids: list[int] = []


class ProjectOwnerUpdate(BaseModel):
  """更新项目请求模型"""

  brief: Optional[str] = Field(None, max_length=255)
  description: Optional[str] = None
  download_url: Optional[HttpUrl] = Field(None, max_length=255)
  code_example: Optional[str] = None
  tag_ids: Optional[list[int]] = None


class ProjectAdminUpdate(ProjectOwnerUpdate):
  """管理员更新项目请求模型"""

  is_approved: Optional[bool] = None
  is_featured: Optional[bool] = None


class ProjectBaseResponse(BaseModel):
  """项目简化响应模型"""

  id: int
  name: str
  brief: str
  description: str
  license: Optional[str] = None
  programming_language: Optional[str] = None
  stars: int
  issues: int
  average_rating: float
  rating_count: int
  view_count: int
  is_approved: bool
  is_featured: bool
  avatar: Optional[str] = None
  platform: Platform
  repo_id: str
  created_at: datetime
  last_commit_at: Optional[datetime] = None
  tags: list[TagResponse]

  class Config:
    from_attributes = True


class ProjectFullResponse(ProjectBaseResponse):
  """项目响应模型"""

  repo_url: str
  website_url: Optional[str] = None
  download_url: Optional[str] = None
  code_example: Optional[str] = None
  forks: int
  watchers: int
  contributors: int
  updated_at: datetime
  repo_created_at: Optional[datetime] = None
  last_sync_at: Optional[datetime] = None
  owner_platform_id: Optional[int] = None
  submitter: UserResponse
  images: list[ImageResponse]


ProjectOrderFields = Literal[
    "id",
    "stars",
    "forks",
    "watchers",
    "contributors",
    "issues",
    "average_rating",
    "rating_count",
    "created_at",
    "updated_at",
    "repo_created_at",
    "last_commit_at",
    "last_sync_at",
    "is_approved",
    "is_featured",
    "view_count",
    "submitter",
    "name",
    "brief",
    "description",
    "website_url",
    "download_url",
    "license",
    "programming_language",
    "code_example",
    "platform",
    "repo_id",
]


class ProjectPaginationParams(PaginationParams):
  order_by: ProjectOrderFields = "id"
  order: Order = "asc"
  ids: Optional[list[int]] = None


class ProjectSearchParams(BaseModel):
  # 与 name brief description 关联
  keyword: Optional[str] = None
  programming_language: Optional[str] = None
  license: Optional[str] = None
  platform: Optional[Platform] = None
  is_featured: Optional[bool] = None
  tags: list[int] = []


class ProjectRepoDetail(BaseModel):
  repo_url: str
  # GitHub: avatar_url
  # Gitee: owner.avatar_url
  avatar: str
  # name
  name: str
  # homepage
  website_url: Optional[str] = None
  # stargazers_count
  stars: int
  # forks_count
  forks: int
  # GitHub: subscribers_count
  # Gitee: watchers_count
  watchers: int
  # repo/contributors
  contributors: int
  # open_issues_count
  issues: int
  # GitHub: license.spdx_id / null
  # Gitee: license / null
  license: Optional[str] = None
  # language / null
  programming_language: Optional[str] = None
  # pushed_at
  last_commit_at: Optional[datetime] = None
  # created_at
  repo_created_at: Optional[datetime] = None
  # owner.id
  owner_platform_id: int


class ProjectCreateModel(ProjectCreate, ProjectRepoDetail):
  submitter_id: int
  pass
