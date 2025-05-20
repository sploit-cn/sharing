from .base import CustomBaseException


class BusinessError(CustomBaseException):
  """业务逻辑错误，使用自定义错误码"""

  def __init__(self, code=1000, message="业务处理失败", *args, **kwargs):
    super().__init__(code, message, *args, **kwargs)


class ResourceConflictError(BusinessError):
  """资源冲突错误"""

  def __init__(
      self, code=1001, message="已被占用", resource="请求的资源", *args, **kwargs
  ):
    super().__init__(code, f"{resource} {message}", *args, **kwargs)


class ApiError(BusinessError):
  """API 错误"""

  def __init__(self, code=1002, message="API 错误", api: str = "", *args, **kwargs):
    if api:
      message = f"{api} {message}"
    super().__init__(code, message, *args, **kwargs)


class ResourceExistsError(BusinessError):
  """资源已存在"""

  def __init__(self, code=1003, message="请勿重复操作", *args, **kwargs):
    super().__init__(code, message, *args, **kwargs)
