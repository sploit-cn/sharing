from typing import Optional
from fastapi import APIRouter, File, Form, Security, UploadFile
from uuid import uuid4
from pathlib import Path
import os

from config import Settings
from core.exceptions import FileTypeNotAllowedError
from core.exceptions.client_errors import ResourceNotFoundError
from models.models import Image
from schemas.images import ImageResponse
from schemas.common import DataResponse, MessageResponse
from utils.security import UserPayloadData, verify_current_user

router = APIRouter()


@router.post("/upload", response_model=DataResponse[ImageResponse])
async def upload_image(
  file: UploadFile = File(...),
  project_id: Optional[int] = Form(None),
  payload: UserPayloadData = Security(verify_current_user),
):
  suffix = Path(file.filename if file.filename else "").suffix
  file_name = f"{uuid4()}{suffix}"
  file_path = Settings.IMAGES_DIR / file_name
  mime_type = file.content_type
  if not mime_type or not mime_type.startswith("image/"):
    raise FileTypeNotAllowedError(message="文件类型必须为图片")
  with open(file_path, "wb") as f:
    f.write(await file.read())
  image = await Image.create(
    file_name=file_name,
    original_name=file.filename,
    mime_type=mime_type,
    user_id=payload.id,
    project_id=project_id,
  )
  return DataResponse(data=image)


@router.delete("/clean", response_model=MessageResponse)
async def clean_images(payload: UserPayloadData = Security(verify_current_user)):
  images = await Image.filter(user_id=payload.id, project_id=None)
  for image in images:
    os.remove(Settings.IMAGES_DIR / image.file_name)
  await Image.filter(user_id=payload.id, project_id=None).delete()
  return MessageResponse(message="图片清理成功")


@router.delete("/{image_id}", response_model=MessageResponse)
async def delete_image(
  image_id: int, payload: UserPayloadData = Security(verify_current_user)
):
  image = await Image.get_or_none(id=image_id)
  if not image:
    raise ResourceNotFoundError(resource="图片")
  os.remove(Settings.IMAGES_DIR / image.file_name)
  await image.delete()
  return MessageResponse(message="图片删除成功")
