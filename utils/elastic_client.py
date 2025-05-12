from elasticsearch import AsyncElasticsearch
from config import Settings

async_elastic_client = AsyncElasticsearch(
  hosts=Settings.ELASTIC_URL, api_key=Settings.ELASTIC_APIKEY
)
