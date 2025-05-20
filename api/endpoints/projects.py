from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Query, Security

from core.exceptions import PermissionDeniedError, ResourceNotFoundError
from models.models import Platform
from schemas.common import DataResponse, MessageResponse, PaginatedResponse
from schemas.projects import (
    ProjectAdminUpdate,
    ProjectBaseResponse,
    ProjectCreate,
    ProjectCreateModel,
    ProjectFullResponse,
    ProjectOwnerUpdate,
    ProjectPaginationParams,
    ProjectSearchParams,
)
from services.project_service import ProjectService
from services.user_service import UserService
from tasks.elastic_sync import delete_project_from_es, sync_project_to_es
from utils.security import (
    UserPayloadData,
    verify_current_admin_user,
    verify_current_user,
)


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectBaseResponse])
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


@router.get("/repo_detail")
async def get_repo_detail(platform: Platform, repo_id: str):
  return await ProjectService.get_repo_detail(platform, repo_id)


@router.get("/my", response_model=DataResponse[list[ProjectBaseResponse]])
async def get_my_projects(payload: UserPayloadData = Security(verify_current_user)):
  result = await ProjectService.get_my_projects(payload.id)
  return DataResponse(data=result)


@router.get("/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def get_project(project_id: int):
  result = await ProjectService.get_project(project_id)
  await ProjectService.increase_view_count(project_id)
  return DataResponse(data=result)


@router.post("/", response_model=DataResponse[ProjectFullResponse])
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
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


@router.put("/my/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def update_my_project(
    project_id: int,
    project_update: ProjectOwnerUpdate,
    background_tasks: BackgroundTasks,
    payload: UserPayloadData = Security(verify_current_user),
):

  project = await ProjectService.get_project_shallow(project_id)
  if project.submitter_id != payload.id:
    raise PermissionDeniedError(message="非项目提交者，无权更改")
  user = await UserService.get_user_by_id(payload.id)
  if project.is_approved == True:
    if project.platform == Platform.GITHUB:
      if user.github_id != project.owner_platform_id:
        raise PermissionDeniedError(message="项目已通过审核，非所有者无权更改")
    elif project.platform == Platform.GITEE:
      if user.gitee_id != project.owner_platform_id:
        raise PermissionDeniedError(message="项目已通过审核，非所有者无权更改")
  project = await ProjectService.update_project(project_id, project_update)
  background_tasks.add_task(sync_project_to_es, project)
  return DataResponse(data=project)


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


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(project_id: int, background_tasks: BackgroundTasks, payload: UserPayloadData = Security(verify_current_admin_user)):
  await ProjectService.delete_project(project_id)
  background_tasks.add_task(delete_project_from_es, project_id)
  return MessageResponse(message="项目删除成功")
