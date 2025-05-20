from models.models import Tag


class TagService:
  @staticmethod
  async def get_tags():
    tags = await Tag.all()
    return tags
