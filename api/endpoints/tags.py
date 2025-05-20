from fastapi import APIRouter, Security

from schemas.common import DataResponse, MessageResponse
from schemas.tags import TagCreate, TagResponse, TagUpdate
from services.tag_service import TagService
from utils.security import UserPayloadData, verify_current_admin_user


router = APIRouter()


@router.get("/", response_model=DataResponse[list[TagResponse]])
async def get_tags():
  result = await TagService.get_tags()
  return DataResponse(data=result)


@router.get("/{tag_id}", response_model=DataResponse[TagResponse])
async def get_tag(tag_id: int):
  result = await TagService.get_tag(tag_id)
  return DataResponse(data=result)


@router.post("/", response_model=DataResponse[TagResponse])
async def create_tag(tag_create: TagCreate, payload: UserPayloadData = Security(verify_current_admin_user)):
  result = await TagService.create_tag(tag_create)
  return DataResponse(data=result)


@router.put("/{tag_id}", response_model=DataResponse[TagResponse])
async def update_tag(tag_id: int, tag_update: TagUpdate, payload: UserPayloadData = Security(verify_current_admin_user)):
  result = await TagService.update_tag(tag_id, tag_update)
  return DataResponse(data=result)


@router.delete("/{tag_id}", response_model=MessageResponse)
async def delete_tag(tag_id: int, payload: UserPayloadData = Security(verify_current_admin_user)):
  await TagService.delete_tag(tag_id)
  return MessageResponse(message="标签删除成功")
