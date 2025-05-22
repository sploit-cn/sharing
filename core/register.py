from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from core.exceptions import CustomBaseException
from core.handlers import (
    custom_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


def register_exception_handlers(app: FastAPI):
  app.add_exception_handler(CustomBaseException, custom_exception_handler)
  app.add_exception_handler(RequestValidationError,
                            validation_exception_handler)
  app.add_exception_handler(HTTPException, http_exception_handler)
  app.add_exception_handler(Exception, general_exception_handler)
