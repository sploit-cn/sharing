from elasticsearch.dsl import AsyncSearch
from elasticsearch.dsl.query import MultiMatch, Term, TermsSet
from core.exceptions import ResourceNotFoundError, ResourceExistsError
from models.models import Comment, Favorite, Image, Platform, Project, Rating, Tag, User
from schemas.comments import CommentCreate
from schemas.common import PaginatedData
from schemas.projects import (
  ProjectAdminUpdate,
  ProjectCreateModel,
  ProjectOwnerUpdate,
  ProjectPaginationParams,
  ProjectRepoDetail,
  ProjectSearchParams,
)
from schemas.ratings import RatingDistributionResponse, RatingUserResponse
from schemas.users import UserRelatedResponse
from services.user_service import UserService
from utils.database import pagination_query
from utils.gitee_api import GiteeAPI
from utils.github_api import GitHubAPI
from utils.time import now
from tortoise.transactions import atomic
from tortoise.expressions import F
from tortoise.query_utils import Prefetch
from tortoise.exceptions import IntegrityError
from tortoise.functions import Count


class ProjectService:
  @staticmethod
  async def search_projects(params: ProjectSearchParams) -> list[int]:
    search = AsyncSearch(index="projects")
    if params.programming_language:
      search = search.filter(Term(programming_language=params.programming_language))
    if params.license:
      search = search.filter(Term(license=params.license))
    if params.platform:
      search = search.filter(Term(platform=params.platform))
    if params.is_featured is not None:
      search = search.filter(Term(is_featured=params.is_featured))
    if (tags_len := len(params.tags)) > 0:
      search = search.filter(
        TermsSet(tags={"terms": params.tags, "minimum_should_match": tags_len})
      )
    if params.keyword:
      search = search.query(
        MultiMatch(query=params.keyword, fields=["name^5", "brief^3", "description^1"])
      )
    result = search.source(fields=False)
    result_ids = []
    async for hit in result:
      result_ids.append(int(hit.meta.id))
    return result_ids

  @staticmethod
  async def suggest_projects(keyword: str) -> list[str]:
    return await ProjectService.suggest_projects_through_db(keyword)

  @staticmethod
  async def suggest_projects_through_es(keyword: str) -> list[str]:
    if keyword == "":
      return await ProjectService.suggest_projects_through_db("")
    search = AsyncSearch(index="projects")
    search = search.suggest(
      "name", keyword, completion={"field": "name.suggest"}
    ).source(fields=False)[0:10]
    result = await search.execute()
    # pyright: ignore
    return [item.text for item in result.suggest.name[0].options]

  @staticmethod
  async def suggest_projects_through_db(keyword: str) -> list[str]:
    projects = await Project.filter(name__istartswith=keyword).values_list(
      "name", flat=True
    )
    return projects  # pyright: ignore

  @staticmethod
  async def get_projects(
    params: ProjectPaginationParams,
  ) -> PaginatedData:
    order = params.order_by
    if params.order == "desc":
      order = "-" + order
    query = Project.all().order_by(order).prefetch_related("tags")
    if params.ids:
      query = Project.filter(id__in=params.ids).order_by(order).prefetch_related("tags")
    return await pagination_query(params, query)

  @staticmethod
  async def get_my_projects(user_id: int) -> list[Project]:
    submitter_projects = (
      await Project.filter(submitter_id=user_id)
      .prefetch_related("tags")
      .order_by("updated_at")
    )
    user = await UserService.get_user_by_id(user_id)
    owner_github_projects = (
      await Project.filter(platform=Platform.GITHUB, owner_platform_id=user.github_id)
      .prefetch_related("tags")
      .order_by("updated_at")
    )
    owner_gitee_projects = (
      await Project.filter(platform=Platform.GITEE, owner_platform_id=user.gitee_id)
      .prefetch_related("tags")
      .order_by("updated_at")
    )
    return submitter_projects + owner_github_projects + owner_gitee_projects

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
  async def get_unapproved_projects() -> list[Project]:
    return await Project.filter(is_approved=None).prefetch_related("tags")

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
      avatar=repo_detail.get("avatar_url", repo_detail["owner"]["avatar_url"]),
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
      last_sync_at=now(),
    )

  @staticmethod
  async def get_gitee_repo_detail(repo_id: str):
    repo_detail = await GiteeAPI.get_repo_detail(repo_id)
    contributors = await GiteeAPI.get_repo_contributors(repo_id)
    return ProjectRepoDetail(
      avatar=repo_detail.get("avatar_url", repo_detail["owner"]["avatar_url"]),
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
      last_sync_at=now(),
    )

  @staticmethod
  async def get_project_comments(project_id: int) -> list[Comment]:
    return (
      await Comment.filter(project_id=project_id)
      .prefetch_related(
        Prefetch(
          "user", queryset=User.all().only("id", "username", "avatar", "bio", "in_use")
        )
      )
      .order_by("created_at")
    )

  @staticmethod
  async def get_project_ratings(project_id: int):
    ratings = (
      await Rating.filter(project_id=project_id)
      .prefetch_related(
        Prefetch(
          "user", queryset=User.all().only("id", "username", "avatar", "bio", "in_use")
        )
      )
      .order_by("updated_at")
    )
    grouped = (
      await Rating.filter(project_id=project_id)
      .annotate(count=Count("score"))
      .group_by("score")
      .values("score", "count")
    )
    distribution = {item["score"]: item["count"] for item in grouped}
    ratings = [
      RatingUserResponse(
        id=rating.id,
        user=UserRelatedResponse.model_validate(rating.user),
        score=rating.score,
        updated_at=rating.updated_at,
      )
      for rating in ratings
    ]
    return RatingDistributionResponse(
      ratings=ratings,
      distribution=distribution,
    )

  @staticmethod
  async def get_my_rating(project_id: int, user_id: int):
    rating = await Rating.get_or_none(project_id=project_id, user_id=user_id)
    if rating is None:
      raise ResourceNotFoundError(resource=f"用户ID:{user_id} 项目ID:{project_id} 评分")
    return rating

  @staticmethod
  @atomic()
  async def create_project(project_create: ProjectCreateModel):
    try:
      project = await Project.create(
        **project_create.model_dump(exclude=set(["tag_ids", "image_ids"])),
        updated_at=now(),
      )
      tags = await Tag.filter(id__in=project_create.tag_ids)
      await Image.filter(id__in=project_create.image_ids).update(project=project)
      await project.tags.add(*tags)
      await project.fetch_related("submitter", "tags", "images")
      return project
    except IntegrityError:
      raise ResourceExistsError(message="项目已存在")
    except Exception as e:
      raise e

  @staticmethod
  async def create_comment(
    user_id: int, project_id: int, comment_create: CommentCreate
  ):
    comment = await Comment.create(
      user_id=user_id,
      project_id=project_id,
      **comment_create.model_dump(exclude_unset=True),
    )
    await comment.fetch_related("user")
    return comment

  @staticmethod
  @atomic()
  async def update_project(
    project_id: int, project_update: ProjectOwnerUpdate | ProjectAdminUpdate
  ):
    project = await Project.get_or_none(id=project_id)
    if project is None:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    update_dict = project_update.model_dump(
      exclude=set(["tag_ids"]), exclude_unset=True
    )
    update_dict["updated_at"] = now()
    await project.update_from_dict(update_dict).save()
    if project_update.tag_ids is not None:
      tags = await Tag.filter(id__in=project_update.tag_ids)
      await project.tags.clear()
      await project.tags.add(*tags)
    await project.fetch_related("submitter", "tags", "images")
    return project

  @staticmethod
  async def approve_project(project_id: int):
    count = await Project.filter(id=project_id).update(
      is_approved=True, approval_date=now()
    )
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    return await ProjectService.get_project(project_id)

  @staticmethod
  async def reject_project(project_id: int):
    count = await Project.filter(id=project_id).update(is_approved=False)
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    return await ProjectService.get_project(project_id)

  @staticmethod
  async def feature_project(project_id: int):
    count = await Project.filter(id=project_id).update(is_featured=True)
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    return await ProjectService.get_project(project_id)

  @staticmethod
  async def unfeature_project(project_id: int):
    count = await Project.filter(id=project_id).update(is_featured=False)
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
    return await ProjectService.get_project(project_id)

  @staticmethod
  async def increase_view_count(project_id: int):
    count = await Project.filter(id=project_id).update(view_count=F("view_count") + 1)
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")

  @staticmethod
  async def get_project_favorites(project_id: int):
    return (
      await Favorite.filter(project_id=project_id)
      .prefetch_related(
        Prefetch(
          "user", queryset=User.all().only("id", "username", "avatar", "bio", "in_use")
        )
      )
      .order_by("created_at")
    )

  @staticmethod
  async def create_favorite(project_id: int, user_id: int):
    favorite = await Favorite.get_or_none(project_id=project_id, user_id=user_id)
    if favorite:
      raise ResourceExistsError(message="请勿重复收藏")
    favorite = await Favorite.create(project_id=project_id, user_id=user_id)
    return favorite

  @staticmethod
  async def delete_favorite(project_id: int, user_id: int):
    count = await Favorite.filter(project_id=project_id, user_id=user_id).delete()
    if count == 0:
      raise ResourceNotFoundError(resource="收藏")

  @staticmethod
  async def delete_project(project_id: int):
    count = await Project.filter(id=project_id).delete()
    if count == 0:
      raise ResourceNotFoundError(resource=f"项目ID:{project_id}")
