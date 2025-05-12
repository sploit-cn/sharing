from utils.httpx_client import async_httpx_client
from utils.elastic_client import async_elastic_client


async def httpx_client():
  return async_httpx_client


async def elastic_client():
  return async_elastic_client
