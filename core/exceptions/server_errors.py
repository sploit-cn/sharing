from .base import CustomBaseException


class ServerError(CustomBaseException):
  """服务器错误基类"""

  def __init__(self, code=500, message="服务器内部错误", *args, **kwargs):
    super().__init__(code, message, *args, **kwargs)


class DatabaseError(ServerError):
  """数据库错误"""

  def __init__(self, message="数据库操作失败", *args, **kwargs):
    super().__init__(500, message, *args, **kwargs)
