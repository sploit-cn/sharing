import os
from pathlib import Path

from dotenv import load_dotenv

# 从 .env 文件中读取环境变量
load_dotenv()


class Settings:

  BASE_DIR = Path(__file__).parent
  STATIC_DIR = BASE_DIR / "static"
  IMAGES_DIR = STATIC_DIR / "images"

  POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
  POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
  POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
  POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
  POSTGRES_DB = os.getenv("POSTGRES_DB", "opensharing")
  DATABASE_URL = f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

  ELASTIC_HOST = os.getenv("ELASTIC_HOST", "localhost")
  ELASTIC_PORT = os.getenv("ELASTIC_PORT", "9200")
  ELASTIC_APIKEY = os.getenv("ELASTIC_APIKEY")
  ELASTIC_URL = f"https://{ELASTIC_HOST}:{ELASTIC_PORT}"

  GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

  ACCESS_TOKEN_EXPIRE_SECONDS = 7 * 24 * 60 * 60
  JWT_ALGORITHM = "HS256"
  JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

  GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
  GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
  GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")
  # GITHUB_STATE = os.getenv("GITHUB_STATE", "")
  GITEE_CLIENT_ID = os.getenv("GITEE_CLIENT_ID")
  GITEE_CLIENT_SECRET = os.getenv("GITEE_CLIENT_SECRET")
  GITEE_REDIRECT_URI = os.getenv("GITEE_REDIRECT_URI")
  # GITEE_STATE = os.getenv("GITEE_STATE", "")

  SYNC_INTERVAL = 600
  SYNC_FREQUENCY = 86400
