from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Query, Security

from core.exceptions import PermissionDeniedError
from models.models import Platform, SyncLog
from schemas.comments import CommentCreate, CommentResponse
from schemas.common import DataResponse, MessageResponse, PaginatedResponse
from schemas.favorites import FavoriteResponse, FavoriteUserResponse
from schemas.projects import (
  ProjectAdminUpdate,
  ProjectBaseResponse,
  ProjectCreate,
  ProjectCreateModel,
  ProjectFullResponse,
  ProjectOwnerUpdate,
  ProjectPaginationParams,
  ProjectRepoDetail,
  ProjectSearchParams,
)
from schemas.ratings import (
  RatingCreate,
  RatingDistributionResponse,
  RatingModifiedResponse,
  RatingResponse,
  RatingUpdate,
)
from services.comment_service import CommentService
from services.notification_service import NotificationService
from services.project_service import ProjectService
from services.rating_service import RatingService
from services.user_service import UserService
from tasks.elastic_sync import delete_project_from_es, sync_project_to_es
from utils.security import (
  UserPayloadData,
  verify_current_admin_user,
  verify_current_user,
)


router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProjectBaseResponse])
async def get_projects(params: Annotated[ProjectPaginationParams, Query()]):
  result = await ProjectService.get_projects(params)
  return PaginatedResponse(data=result)


@router.get("/suggest", response_model=DataResponse[list[str]])
async def get_project_suggest(keyword: str):
  result = await ProjectService.suggest_projects(keyword)
  return DataResponse(data=result)


@router.get("/search", response_model=DataResponse[list[int]])
async def search_projects(params: Annotated[ProjectSearchParams, Query()]):
  result_ids = await ProjectService.search_projects(params)
  return DataResponse(data=result_ids)


@router.get("/related", response_model=DataResponse[list[ProjectBaseResponse]])
async def get_related_projects(project_id: int):
  result = await ProjectService.get_related_projects(project_id)
  return DataResponse(data=result)


@router.get("/repo_detail", response_model=DataResponse[ProjectRepoDetail])
async def get_repo_detail(platform: Platform, repo_id: str):
  result = await ProjectService.get_repo_detail(platform, repo_id)
  return DataResponse(data=result)


@router.get("/my", response_model=DataResponse[list[ProjectBaseResponse]])
async def get_my_projects(payload: UserPayloadData = Security(verify_current_user)):
  result = await ProjectService.get_my_projects(payload.id)
  return DataResponse(data=result)


@router.get("/unapproved", response_model=DataResponse[list[ProjectBaseResponse]])
async def get_unapproved_projects(
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  result = await ProjectService.get_unapproved_projects()
  return DataResponse(data=result)


@router.get(
  "/{project_id}/comments", response_model=DataResponse[list[CommentResponse]]
)
async def get_project_comments(project_id: int):
  result = await ProjectService.get_project_comments(project_id)
  return DataResponse(data=result)


@router.get(
  "/{project_id}/favorites", response_model=DataResponse[list[FavoriteUserResponse]]
)
async def get_project_favorites(project_id: int):
  result = await ProjectService.get_project_favorites(project_id)
  return DataResponse(data=result)


@router.get(
  "/{project_id}/ratings", response_model=DataResponse[RatingDistributionResponse]
)
async def get_project_ratings(project_id: int):
  result = await ProjectService.get_project_ratings(project_id)
  return DataResponse(data=result)


@router.get("/{project_id}/my-rating", response_model=DataResponse[RatingResponse])
async def get_my_rating(
  project_id: int, payload: UserPayloadData = Security(verify_current_user)
):
  result = await ProjectService.get_my_rating(project_id, payload.id)
  return DataResponse(data=result)


@router.get("/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def get_project(project_id: int):
  result = await ProjectService.get_project(project_id)
  await ProjectService.increase_view_count(project_id)
  return DataResponse(data=result)


@router.post("", response_model=DataResponse[ProjectFullResponse])
async def create_project(
  project_create: ProjectCreate,
  background_tasks: BackgroundTasks,
  payload: UserPayloadData = Security(verify_current_user),
):
  repo_detail = await ProjectService.get_repo_detail(
    project_create.platform, project_create.repo_id
  )
  project_model = ProjectCreateModel(
    **project_create.model_dump(), **repo_detail.model_dump(), submitter_id=payload.id
  )
  project = await ProjectService.create_project(project_model)
  await SyncLog.create(
    project=project, status="success", project_detail=repo_detail.model_dump()
  )
  await NotificationService.notify_admins(
    f"项目 {project.name} 已提交审核", related_project=project.id
  )
  await NotificationService.notify_user(
    f"你的项目 {project.name} 已提交审核",
    user_id=payload.id,
    related_project=project.id,
  )
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


@router.post("/{project_id}/favorite", response_model=DataResponse[FavoriteResponse])
async def create_favorite(
  project_id: int, payload: UserPayloadData = Security(verify_current_user)
):
  favorite = await ProjectService.create_favorite(project_id, payload.id)
  return DataResponse(data=favorite)


@router.post("/{project_id}/comment", response_model=DataResponse[CommentResponse])
async def create_comment(
  project_id: int,
  comment_create: CommentCreate,
  payload: UserPayloadData = Security(verify_current_user),
):
  comment = await ProjectService.create_comment(payload.id, project_id, comment_create)
  project = await ProjectService.get_project_shallow(project_id)
  if comment_create.parent_id is not None:
    parent_comment = await CommentService.get_comment(comment_create.parent_id)
    await NotificationService.notify_user(
      f"您在项目 {project.name} 的评论有新的回复",
      user_id=parent_comment.user_id,
      related_project=comment.project_id,
      related_comment=comment.id,
    )
  else:
    await NotificationService.notify_user(
      f"您分享的项目 {project.name} 有新的评论",
      user_id=project.submitter_id,
      related_project=comment.project_id,
      related_comment=comment.id,
    )
  return DataResponse(data=comment)


@router.post(
  "/{project_id}/rating", response_model=DataResponse[RatingModifiedResponse]
)
async def create_rating(
  project_id: int,
  rating_create: RatingCreate,
  payload: UserPayloadData = Security(verify_current_user),
):
  rating = await RatingService.create_rating(project_id, payload.id, rating_create)
  return DataResponse(data=rating)


@router.put("/my/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def update_my_project(
  project_id: int,
  project_update: ProjectOwnerUpdate,
  background_tasks: BackgroundTasks,
  payload: UserPayloadData = Security(verify_current_user),
):
  project = await ProjectService.get_project_shallow(project_id)
  user = await UserService.get_user_by_id(payload.id)
  if (
    project.platform == Platform.GITHUB and user.github_id == project.owner_platform_id
  ) or (
    project.platform == Platform.GITEE and user.gitee_id == project.owner_platform_id
  ):
    # 所有者
    pass
  elif project.submitter_id == payload.id:
    # 推荐者
    if project.is_approved == True:
      raise PermissionDeniedError(message="项目已通过审核，非所有者无权更改")
  else:
    raise PermissionDeniedError(message="非项目推荐者或所有者，无权更改")
  project = await ProjectService.update_project(project_id, project_update)
  await NotificationService.notify_admins(
    f"项目 {project.name} 已被推荐者/所有者更新", related_project=project.id
  )
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


@router.put("/{project_id}/approve", response_model=DataResponse[ProjectFullResponse])
async def approve_project(
  project_id: int, payload: UserPayloadData = Security(verify_current_admin_user)
):
  project = await ProjectService.approve_project(project_id)
  await NotificationService.notify_user(
    f"您分享的项目 {project.name} 已通过审核",
    user_id=project.submitter_id,
    related_project=project.id,
  )
  return DataResponse(data=project)


@router.put("/{project_id}/reject", response_model=DataResponse[ProjectFullResponse])
async def reject_project(
  project_id: int, payload: UserPayloadData = Security(verify_current_admin_user)
):
  project = await ProjectService.reject_project(project_id)
  await NotificationService.notify_user(
    f"您分享的项目 {project.name} 未通过审核",
    user_id=project.submitter_id,
    related_project=project.id,
  )
  return DataResponse(data=project)


@router.put("/{project_id}/feature", response_model=DataResponse[ProjectFullResponse])
async def feature_project(
  project_id: int,
  background_tasks: BackgroundTasks,
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  project = await ProjectService.feature_project(project_id)
  await NotificationService.notify_user(
    f"您分享的项目 {project.name} 已设置为精选",
    user_id=project.submitter_id,
    related_project=project.id,
  )
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


@router.put("/{project_id}/unfeature", response_model=DataResponse[ProjectFullResponse])
async def unfeature_project(
  project_id: int,
  background_tasks: BackgroundTasks,
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  project = await ProjectService.unfeature_project(project_id)
  await NotificationService.notify_user(
    f"您分享的项目 {project.name} 已取消精选",
    user_id=project.submitter_id,
    related_project=project.id,
  )
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


@router.put("/{project_id}/rating", response_model=DataResponse[RatingModifiedResponse])
async def update_rating(
  project_id: int,
  rating_update: RatingUpdate,
  payload: UserPayloadData = Security(verify_current_user),
):
  rating = await RatingService.update_rating(project_id, payload.id, rating_update)
  return DataResponse(data=rating)


@router.put("/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def update_project(
  project_id: int,
  project_update: ProjectAdminUpdate,
  background_tasks: BackgroundTasks,
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  project = await ProjectService.update_project(project_id, project_update)
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


@router.delete("/{project_id}/favorite", response_model=MessageResponse)
async def delete_favorite(
  project_id: int, payload: UserPayloadData = Security(verify_current_user)
):
  await ProjectService.delete_favorite(project_id, payload.id)
  return MessageResponse(message="取消收藏成功")


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
  project_id: int,
  background_tasks: BackgroundTasks,
  payload: UserPayloadData = Security(verify_current_admin_user),
):
  await ProjectService.delete_project(project_id)
  background_tasks.add_task(delete_project_from_es, project_id)
  return MessageResponse(message="项目删除成功")
