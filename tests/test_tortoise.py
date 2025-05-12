import asyncio
from tortoise import Tortoise

from models.models import *


async def init_db():
  await Tortoise.init(
      db_url="postgres://postgres:@127.0.0.1:5432/opensharing",
      modules={"models": ["__main__"]},
  )


async def main():
  await init_db()
  await Tortoise.close_connections()


if __name__ == "__main__":
  asyncio.run(main())
