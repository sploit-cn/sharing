from fastapi import APIRouter, Security

from schemas.common import DataResponse, MessageResponse
from schemas.ratings import RatingCreate, RatingResponse, RatingUpdate
from services.rating_service import RatingService
from utils.security import UserPayloadData, verify_current_admin_user, verify_current_user

router = APIRouter()


@router.get("/sync", response_model=MessageResponse)
async def sync_rating(payload: UserPayloadData = Security(verify_current_admin_user)):
  await RatingService.sync_rating()
  return MessageResponse(message="评分同步成功")
