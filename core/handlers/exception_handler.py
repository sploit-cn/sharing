# 自定义异常处理器
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import traceback

from core.exceptions import CustomBaseException


async def custom_exception_handler(request: Request, exc: Exception):
  """处理所有自定义异常"""
  if isinstance(exc, CustomBaseException):
    return JSONResponse(
      status_code=200,  # 统一返回200状态码
      content=exc.to_dict(),
    )
  return JSONResponse(
    status_code=200,
    content={"code": 500, "message": "服务器内部错误"},
  )


# FastAPI验证错误处理器
async def validation_exception_handler(request: Request, exc: Exception):
  """处理FastAPI的请求验证错误"""
  if not isinstance(exc, RequestValidationError):
    return JSONResponse(
      status_code=200,
      content={"code": 422, "message": "请求参数验证失败", "fields": {}},
    )
  fields = {}
  try:
    for error in exc.errors():
      fields["".join(error["loc"])] = error["msg"]
  except Exception:
    fields = {}

  return JSONResponse(
    status_code=200,
    content={"code": 422, "message": "请求参数验证失败", "fields": fields},
  )


# HTTP异常处理器
async def http_exception_handler(request: Request, exc: Exception):
  """处理HTTP异常"""
  if not isinstance(exc, HTTPException):
    return JSONResponse(
      status_code=500,
      content={"code": 500, "message": "服务器内部错误"},
    )
  return JSONResponse(
    status_code=exc.status_code,
    content={"code": exc.status_code, "message": exc.detail},
    headers=exc.headers,
  )


# 通用异常处理器
async def general_exception_handler(request: Request, exc: Exception):
  """处理所有未捕获的异常"""
  traceback.print_exc()
  return JSONResponse(
    status_code=200, content={"code": 500, "message": "服务器内部错误"}
  )
