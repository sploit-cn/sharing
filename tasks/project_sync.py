import asyncio
from datetime import timedelta

from models.models import Project, SyncLog
from services.project_service import ProjectService
from utils.time import now


async def sync_projects(interval: float = 600, frequency: float = 86400):
  while True:
    try:
      await asyncio.sleep(interval)
      projects = await Project.filter(last_sync_at__lt=now() - timedelta(seconds=frequency)).only("id", "name", "repo_id", "platform")
      for project in projects:
        project_detail = await ProjectService.get_repo_detail(project.platform, project.repo_id)
        await Project.filter(id=project.id).update(**project_detail.model_dump())
        await SyncLog.create(project=project, status="success", project_detail=project_detail.model_dump())
        print(f"{now()} 同步项目 {project.name} 成功")
    except Exception as e:
      print(f"{now()} 同步项目失败: {e}")
