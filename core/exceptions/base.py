class CustomBaseException(Exception):
  def __init__(self, code=500, message="服务器内部错误", *args, **kwargs):
    self.code = code
    self.message = message
    super().__init__(message, *args, **kwargs)

  def __str__(self):
    return f"[{self.code}] {self.message}"

  def to_dict(self):
    """转换为字典格式，方便序列化为JSON响应"""
    return {"code": self.code, "message": self.message}
