from core.exceptions import ResourceNotFoundError
from models.models import Tag
from schemas.tags import TagCreate, TagUpdate


class TagService:
  @staticmethod
  async def get_tags():
    tags = await Tag.all()
    return tags

  @staticmethod
  async def get_tag(tag_id: int):
    tag = await Tag.get_or_none(id=tag_id)
    if tag is None:
      raise ResourceNotFoundError(resource=f"标签ID:{tag_id}")
    return tag

  @staticmethod
  async def create_tag(tag_create: TagCreate):
    tag = await Tag.create(**tag_create.model_dump())
    return tag

  @staticmethod
  async def update_tag(tag_id: int, tag_update: TagUpdate):
    tag = await Tag.get_or_none(id=tag_id)
    if tag is None:
      raise ResourceNotFoundError(resource=f"标签ID:{tag_id}")
    print(tag_update.model_dump(exclude_unset=True))
    await tag.update_from_dict(tag_update.model_dump(exclude_unset=True)).save()
    return tag

  @staticmethod
  async def delete_tag(tag_id: int):
    tag = await Tag.get_or_none(id=tag_id)
    if tag is None:
      raise ResourceNotFoundError(resource="标签")
    await tag.delete()
