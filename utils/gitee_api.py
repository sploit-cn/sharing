from typing import Any
from fastapi import status
from config import Settings
from core.exceptions import ApiError
from core.exceptions.client_errors import AuthenticationError
from utils.httpx_client import async_httpx_client as client


class GiteeAPI:
  @staticmethod
  async def get(api: str, access_token: str = "", params: dict = {}):
    if access_token:
      params["access_token"] = access_token
    request = await client.get(
      f"https://gitee.com/api/v5{api}",
      params=params,
    )
    if request.status_code != status.HTTP_200_OK:
      raise ApiError(api="Gitee API")
    return request.json()

  @staticmethod
  async def get_current_user(access_token: str) -> dict[str, Any]:
    try:
      return await GiteeAPI.get("/user", access_token=access_token)
    except Exception:
      raise ApiError(api="Gitee 用户信息")

  @staticmethod
  async def get_current_user_emails(access_token: str) -> list[dict[str, Any]]:
    try:
      return await GiteeAPI.get("/emails", access_token=access_token)
    except Exception:
      raise ApiError(api="Gitee 用户邮箱信息")

  @staticmethod
  async def get_repo_detail(repo_id: str):
    try:
      return await GiteeAPI.get(f"/repos/{repo_id}")
    except Exception:
      raise ApiError(api="Gitee 仓库信息")

  @staticmethod
  async def get_repo_contributors(repo_id: str):
    try:
      return await GiteeAPI.get(f"/repos/{repo_id}/contributors")
    except Exception:
      raise ApiError(api="Gitee 仓库贡献者信息")

  @staticmethod
  async def oauth(code: str):
    try:
      response = await client.post(
        "https://gitee.com/oauth/token",
        data={
          "client_id": Settings.GITEE_CLIENT_ID,
          "client_secret": Settings.GITEE_CLIENT_SECRET,
          "code": code,
          "grant_type": "authorization_code",
          "redirect_uri": Settings.GITEE_REDIRECT_URI,
        },
        headers={"Accept": "application/json"},
      )
      if response.status_code != 200:
        raise AuthenticationError()
      return response.json()
    except Exception:
      raise AuthenticationError(message="Gitee OAuth 认证失败")
