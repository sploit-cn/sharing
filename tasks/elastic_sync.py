from models.models import Project
from models.elastic_models import Project as ESProject
from elasticsearch.exceptions import NotFoundError


async def sync_project_to_es(project: Project):
  if project.is_approved == True:
    await submit_project_to_es(project)
  else:
    await delete_project_from_es(project.id)


async def submit_project_to_es(project: Project):
  tag_ids = [tag.id for tag in project.tags]
  es_project = ESProject(
      meta={"id": project.id},
      name=project.name,
      brief=project.brief,
      description=project.description,
      programming_language=project.programming_language,
      license=project.license,
      platform=project.platform,
      is_featured=project.is_featured,
      tags=tag_ids,
  )
  await es_project.save()


async def delete_project_from_es(project_id: int):
  try:
    doc = await ESProject.get(id=project_id)
    if doc:
      await doc.delete()
  except NotFoundError:
    pass
