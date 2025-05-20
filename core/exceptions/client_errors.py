from .base import CustomBaseException


class ClientError(CustomBaseException):
  """客户端错误基类"""

  def __init__(self, code=400, message="客户端请求错误", *args, **kwargs):
    super().__init__(code, message, *args, **kwargs)


class ValidationError(ClientError):
  """数据验证错误"""

  def __init__(
      self,
      message="数据验证失败",
      fields: dict[str, str | list[str]] = {},
      *args,
      **kwargs,
  ):
    super().__init__(422, message, *args, **kwargs)
    self.fields = fields

  def to_dict(self):
    result = super().to_dict()
    if self.fields:
      result["fields"] = self.fields
    return result


class AuthenticationError(ClientError):
  """认证失败错误"""

  def __init__(self, message="认证失败", auth="", *args, **kwargs):
    if auth:
      message = f"{auth} {message}"
    super().__init__(401, message, *args, **kwargs)


class PermissionDeniedError(ClientError):
  """权限不足错误"""

  def __init__(self, message="权限不足", *args, **kwargs):
    super().__init__(403, message, *args, **kwargs)


class ResourceNotFoundError(ClientError):
  """资源未找到错误"""

  def __init__(self, message="不存在", resource="资源", *args, **kwargs):
    if resource:
      message = f"{resource} {message}"
    super().__init__(404, message, *args, **kwargs)
