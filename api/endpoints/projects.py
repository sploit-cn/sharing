from typing import Annotated
from fastapi import APIRouter, Query, Security

from core.exceptions.client_errors import ResourceNotFoundError
from models.models import Platform
from schemas.common import DataResponse, PaginatedResponse
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


@router.get("/search", response_model=DataResponse[list[int]])
async def search_projects(params: Annotated[ProjectSearchParams, Query()]):
  result_ids = await ProjectService.search_projects(params)
  return DataResponse(data=result_ids)


@router.get("/repo_detail")
async def get_repo_detail(platform: Platform, repo_id: str):
  return await ProjectService.get_repo_detail(platform, repo_id)


@router.get("/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def get_project(project_id: int):
  try:
    result = await ProjectService.get_project(project_id)
    return DataResponse(data=result)
  except Exception:
    raise ResourceNotFoundError(resource=f"项目ID:{project_id}")


@router.post("/", response_model=DataResponse[ProjectFullResponse])
async def create_project(
    project_create: ProjectCreate,
    payload: UserPayloadData = Security(verify_current_user),
):
  repo_detail = await ProjectService.get_repo_detail(
      project_create.platform, project_create.repo_id
  )
  project_model = ProjectCreateModel(
      **project_create.model_dump(), **repo_detail.model_dump(), submitter_id=payload.id
  )
  project = await ProjectService.create_project(project_model)
  return DataResponse(data=project)


@router.put("/my/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def update_my_project(
    project_id: int,
    project_update: ProjectOwnerUpdate,
    payload: UserPayloadData = Security(verify_current_user),
):
  try:
    project = await ProjectService.update_project(project_id, project_update)
    return DataResponse(data=project)
  except Exception:
    raise ResourceNotFoundError(resource=f"项目ID:{project_id}")


@router.put("/{project_id}", response_model=DataResponse[ProjectFullResponse])
async def update_project(
    project_id: int,
    project_update: ProjectAdminUpdate,
    payload: UserPayloadData = Security(verify_current_admin_user),
):
  try:
    project = await ProjectService.update_project(project_id, project_update)
    return DataResponse(data=project)
  except Exception:
    raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
