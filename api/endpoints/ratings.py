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


@router.post("/{project_id}", response_model=DataResponse[RatingResponse])
async def create_rating(project_id: int, rating_create: RatingCreate, payload: UserPayloadData = Security(verify_current_user)):
  rating = await RatingService.create_rating(project_id, payload.id, rating_create)
  return DataResponse(data=rating)


@router.put("/{project_id}", response_model=DataResponse[RatingResponse])
async def update_rating(project_id: int, rating_update: RatingUpdate, payload: UserPayloadData = Security(verify_current_user)):
  rating = await RatingService.update_rating(project_id, payload.id, rating_update)
  return DataResponse(data=rating)
