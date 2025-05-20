from fastapi import APIRouter

from schemas.common import DataResponse
from schemas.tag import TagResponse
from services.tag_service import TagService


router = APIRouter()


@router.get("/", response_model=DataResponse[list[TagResponse]])
async def get_tags():
  result = await TagService.get_tags()
  return DataResponse(data=result)
