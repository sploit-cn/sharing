from core.exceptions import ResourceConflictError, ResourceNotFoundError, DatabaseError
from models.models import User
from schemas.common import PaginatedData
from schemas.users import (
    UserPaginationParams,
    UserUpdate,
    UserUpdateByAdmin,
)
from utils.database import pagination_query
from utils.security import get_password_hash


class UserService:
  @staticmethod
  async def get_users(params: UserPaginationParams) -> PaginatedData:
    order = params.order_by
    if params.order == "desc":
      order = "-" + order
    query = User.all().order_by(order)
    data = await pagination_query(params, query)
    return data

  @staticmethod
  async def get_user_by_id(user_id: int) -> User:
    data = await User.get_or_none(id=user_id)
    if data is None:
      raise ResourceNotFoundError(resource=f"用户ID:{user_id}")
    return data

  @staticmethod
  async def update_user(user_id: int, update_fields: UserUpdate | UserUpdateByAdmin):
    # 检查邮箱是否已存在
    if update_fields.email:
      existing = await User.filter(email=update_fields.email).first()
      if existing and existing.id != user_id:
        raise ResourceConflictError(resource="email")
    status = await User.filter(id=user_id).update(
        **update_fields.model_dump(exclude_unset=True)
    )
    if status == 0:
      raise ResourceNotFoundError(resource=f"用户ID:{user_id}")
    user = await User.get(id=user_id)
    return user

  @staticmethod
  async def update_user_password(user_id: int, password: str):
    password_hash = get_password_hash(password)
    status = await User.filter(id=user_id).update(password_hash=password_hash)
    if status == 0:
      raise ResourceNotFoundError(resource=f"用户ID:{user_id}")
