from elasticsearch.dsl import AsyncSearch
from elasticsearch.dsl.query import MultiMatch, Term, TermsSet
from core.exceptions import ResourceNotFoundError
from models.elastic_models import Project as ESProject
from models.models import Image, Platform, Project, Tag
from schemas.common import PaginatedData
from schemas.projects import (
    ProjectAdminUpdate,
    ProjectCreateModel,
    ProjectOwnerUpdate,
    ProjectPaginationParams,
    ProjectRepoDetail,
    ProjectSearchParams,
)
from utils.database import pagination_query
from utils.gitee_api import GiteeAPI
from utils.github_api import GitHubAPI
from utils.time import now
from tortoise.transactions import atomic
from tortoise.expressions import F


class ProjectService:
  @staticmethod
  async def search_projects(params: ProjectSearchParams) -> list[int]:
    search = AsyncSearch(index="projects")
    if params.programming_language:
      search = search.filter(
          Term(programming_language=params.programming_language))
    if params.license:
      search = search.filter(Term(license=params.license))
    if params.platform:
      search = search.filter(Term(platform=params.platform))
    if params.is_featured is not None:
      search = search.filter(Term(is_featured=params.is_featured))
    if (tags_len := len(params.tags)) > 0:
      search = search.filter(
          TermsSet(tags={"terms": params.tags,
                   "minimum_should_match": tags_len})
      )
    if params.keyword:
      search = search.query(
          MultiMatch(query=params.keyword, fields=[
                     "name^5", "brief^3", "description^1"])
      )
    result = search.source(fields=False)
    result_ids = []
    async for hit in result:
      result_ids.append(int(hit.meta.id))
    return result_ids

  @staticmethod
  async def suggest_projects(keyword: str) -> list[str]:
    return await ProjectService.suggest_projects_through_es(keyword)

  @staticmethod
  async def suggest_projects_through_es(keyword: str) -> list[str]:
    search = AsyncSearch(index="projects")
    search = search.suggest('name', keyword, completion={
                            'field': 'name.suggest'}).source(fields=False)[0:10]
    result = await search.execute()
    return [item.text for item in result.suggest.name[0].options]

  @staticmethod
  async def suggest_projects_through_db(keyword: str) -> list[str]:
    projects = await Project.filter(name__istartswith=keyword).values_list("name", flat=True)
    return projects

  @staticmethod
  async def get_projects(
      params: ProjectPaginationParams,
  ) -> PaginatedData:
    order = params.order_by
    if params.order == "desc":
      order = "-" + order
    query = Project.all().order_by(order).prefetch_related("tags")
    if params.ids:
      query = Project.filter(id__in=params.ids).order_by(
          order).prefetch_related("tags")
    return await pagination_query(params, query)

  @staticmethod
  async def get_my_projects(user_id: int) -> list[Project]:
    return await Project.filter(submitter_id=user_id).prefetch_related("tags").order_by("updated_at")

  @staticmethod
  async def get_project(project_id: int) -> Project:
    result = await Project.get_or_none(id=project_id).prefetch_related(
        "tags", "images", "submitter"
    )
    if result is None:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    return result

  @staticmethod
  async def get_project_shallow(project_id: int) -> Project:
    result = await Project.get_or_none(id=project_id)
    if result is None:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    return result

  @staticmethod
  async def get_repo_detail(platform: Platform, repo_id: str):
    if platform == Platform.GITHUB:
      return await ProjectService.get_github_repo_detail(repo_id)
    elif platform == Platform.GITEE:
      return await ProjectService.get_gitee_repo_detail(repo_id)

  @staticmethod
  async def get_github_repo_detail(repo_id: str):
    repo_detail = await GitHubAPI.get_repo_detail(repo_id)
    contributors = await GitHubAPI.get_repo_contributors(repo_id)
    return ProjectRepoDetail(
        avatar=repo_detail.get(
            "avatar_url", repo_detail["owner"]["avatar_url"]),
        name=repo_detail["name"],
        repo_url=f"https://github.com/{repo_detail['full_name']}",
        website_url=repo_detail["homepage"],
        stars=repo_detail["stargazers_count"],
        forks=repo_detail["forks_count"],
        watchers=repo_detail["subscribers_count"],
        contributors=len(contributors),
        issues=repo_detail["open_issues_count"],
        license=repo_detail["license"]["spdx_id"] if repo_detail["license"] else None,
        programming_language=repo_detail["language"],
        last_commit_at=repo_detail["pushed_at"],
        repo_created_at=repo_detail["created_at"],
        owner_platform_id=repo_detail["owner"]["id"],
    )

  @staticmethod
  async def get_gitee_repo_detail(repo_id: str):
    repo_detail = await GiteeAPI.get_repo_detail(repo_id)
    contributors = await GiteeAPI.get_repo_contributors(repo_id)
    return ProjectRepoDetail(
        avatar=repo_detail.get(
            "avatar_url", repo_detail["owner"]["avatar_url"]),
        name=repo_detail["name"],
        repo_url=f"https://gitee.com/{repo_detail['full_name']}",
        website_url=repo_detail["homepage"],
        stars=repo_detail["stargazers_count"],
        forks=repo_detail["forks_count"],
        watchers=repo_detail["watchers_count"],
        contributors=len(contributors),
        issues=repo_detail["open_issues_count"],
        license=repo_detail["license"],
        programming_language=repo_detail["language"],
        last_commit_at=repo_detail["pushed_at"],
        repo_created_at=repo_detail["created_at"],
        owner_platform_id=repo_detail["owner"]["id"],
    )

  @staticmethod
  @atomic()
  async def create_project(project_create: ProjectCreateModel):
    project = await Project.create(
        **project_create.model_dump(exclude=set(["tag_ids", "image_ids"])),
        updated_at=now(),
    )
    tags = await Tag.filter(id__in=project_create.tag_ids)
    await Image.filter(id__in=project_create.image_ids).update(project=project)
    await project.tags.add(*tags)
    await project.fetch_related("submitter", "tags", "images")
    return project

  @staticmethod
  @atomic()
  async def update_project(project_id: int, project_update: ProjectOwnerUpdate | ProjectAdminUpdate):
    project = await Project.get_or_none(id=project_id)
    if project is None:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    update_dict = project_update.model_dump(
        exclude=set(["tag_ids"]), exclude_unset=True)
    update_dict["updated_at"] = now()
    await project.update_from_dict(update_dict).save()
    if project_update.tag_ids is not None:
      tags = await Tag.filter(id__in=project_update.tag_ids)
      await project.tags.clear()
      await project.tags.add(*tags)
    await project.fetch_related("submitter", "tags", "images")
    return project

  @staticmethod
  async def delete_project(project_id: int):
    await Project.filter(id=project_id).delete()

  @staticmethod
  async def increase_view_count(project_id: int):
    await Project.filter(id=project_id).update(view_count=F("view_count") + 1)

  @staticmethod
  async def delete_project(project_id: int):
    count = await Project.filter(id=project_id).delete()
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
