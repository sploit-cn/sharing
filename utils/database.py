from typing import TYPE_CHECKING, TypeVar

from tortoise.queryset import QuerySet
from config import Settings
from schemas.common import PaginatedData, PaginationParams

# 定义模型模块
TORTOISE_ORM = {
  "connections": {"default": Settings.DATABASE_URL},
  "apps": {
    "models": {
      "models": ["models.models", "aerich.models"],
      "default_connection": "default",
    },
  },
  "use_tz": True,
  "timezone": "Asia/Shanghai",
}

if TYPE_CHECKING:  # pragma: nocoverage
  from tortoise.models import Model
MODEL = TypeVar("MODEL", bound="Model")


async def pagination_query(
  pagination_params: PaginationParams, query: QuerySet[MODEL]
) -> PaginatedData[MODEL]:
  page, page_size = pagination_params.page, pagination_params.page_size
  offset = (page - 1) * page_size
  results = await query.offset(offset).limit(page_size)
  total = await query.count()
  return PaginatedData(
    items=results,
    total=total,
    page=page,
    page_size=page_size,
    pages=(total + page_size - 1) // page_size,
  )
