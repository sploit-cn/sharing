from models.models import Project, Rating
from schemas.ratings import RatingCreate, RatingModifiedResponse, RatingUpdate
from services.project_service import ProjectService
from tortoise.transactions import atomic
from core.exceptions import ResourceConflictError, ResourceNotFoundError
from tortoise.exceptions import IntegrityError
from tortoise.functions import Avg, Count


class RatingService:
  @staticmethod
  async def sync_rating():
    averages = await Rating.annotate(avg_score=Avg('score'), count=Count('score')).group_by('project_id').values('project_id', 'avg_score', 'count')
    projects_to_update = []
    for average in averages:
      project_id = average['project_id']
      average_rating = average['avg_score']
      rating_count = average['count']
      projects_to_update.append(Project(
          id=project_id, average_rating=average_rating, rating_count=rating_count))
    await Project.bulk_update(projects_to_update, fields=['average_rating', 'rating_count'])

  @staticmethod
  async def get_rating(project_id: int, user_id: int):
    rating = await Rating.get_or_none(project_id=project_id, user_id=user_id)
    if rating is None:
      raise ResourceNotFoundError(
          resource=f"评分不存在,项目ID:{project_id} 用户ID:{user_id}")
    return rating

  @staticmethod
  @atomic()
  async def create_rating(project_id: int, user_id: int, rating_create: RatingCreate):
    project = await ProjectService.get_project_shallow(project_id)
    project.average_rating = (project.average_rating*project.rating_count +
                              rating_create.score) / (project.rating_count + 1)
    project.rating_count += 1
    await project.save()
    rating = Rating(project_id=project_id, user_id=user_id,
                    **rating_create.model_dump())
    try:
      await rating.save()
    except IntegrityError:
      raise ResourceConflictError(message="已存在", resource="评分")
    return RatingModifiedResponse(average_rating=project.average_rating, rating_count=project.rating_count)

  @staticmethod
  @atomic()
  async def update_rating(project_id: int, user_id: int, rating_update: RatingUpdate):
    rating = await RatingService.get_rating(project_id, user_id)
    if rating_update.score is not None:
      project = await ProjectService.get_project_shallow(project_id)
      project.average_rating = (project.average_rating*project.rating_count -
                                rating.score + rating_update.score) / project.rating_count
      await project.save()
    await rating.update_from_dict(
        rating_update.model_dump(exclude_unset=True)).save()
    return RatingModifiedResponse(average_rating=project.average_rating, rating_count=project.rating_count)
