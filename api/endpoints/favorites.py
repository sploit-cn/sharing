from fastapi import APIRouter, Security

from models.models import Favorite
from schemas.common import DataResponse
from schemas.favorites import FavoriteProjectResponse
from utils.security import UserPayloadData, verify_current_user

router = APIRouter()


@router.get("/", response_model=DataResponse[list[FavoriteProjectResponse]])
async def get_favorites(payload: UserPayloadData = Security(verify_current_user)):
  favorites = await Favorite.filter(user=payload.id).all().prefetch_related("project__tags")
  return DataResponse(data=favorites)
