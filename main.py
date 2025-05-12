from contextlib import asynccontextmanager
import logging
from elasticsearch.dsl import async_connections
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import connections
from tortoise.contrib.fastapi import register_tortoise
from config import Settings
from utils.database import TORTOISE_ORM
from api.router import router
from core import register_exception_handlers
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
  # 设置 Tortoise 日志
  logger = logging.getLogger("tortoise")
  logger.setLevel(logging.DEBUG)
  handler = logging.StreamHandler()
  handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
  logger.addHandler(handler)
  # Elastisearch 连接配置
  async_connections.create_connection(
    hosts=Settings.ELASTIC_URL, api_key=Settings.ELASTIC_APIKEY
  )
  yield


app = FastAPI(
  title="开源项目展示平台API",
  description="基于FastAPI和Tortoise-ORM的开源项目展示平台后端API",
  version="0.1.0",
  lifespan=lifespan,
)

origins = [
  "http://localhost",
  "http://localhost:3000",
  "http://localhost:5173",
]

# noinspection PyTypeChecker
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

register_tortoise(
  app,
  config=TORTOISE_ORM,
)
register_exception_handlers(app)

app.include_router(router, prefix="")


@app.get("/")
async def read_root():
  await connections.get("default").execute_query("SELECT 1")
  return {"message": "Hello World"}


if __name__ == "__main__":
  uvicorn.run("main:app", port=8000, reload=True)
