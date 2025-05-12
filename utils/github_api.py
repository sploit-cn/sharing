from typing import Any
from fastapi import status
from config import Settings
from core.exceptions import ApiError
from core.exceptions.client_errors import AuthenticationError
from utils.httpx_client import async_httpx_client as client


class GitHubAPI:
  @staticmethod
  async def get(api: str, access_token: str = "", params: dict = {}):
    headers = {}
    if access_token:
      headers = {"Authorization": f"Bearer {access_token}"}
    request = await client.get(
      "https://api.github.com" + api, headers=headers, params=params
    )
    if request.status_code != status.HTTP_200_OK:
      raise ApiError(api="GitHub API")
    return request.json()

  @staticmethod
  async def get_current_user(access_token: str) -> dict[str, Any]:
    try:
      return await GitHubAPI.get("/user", access_token)
    except Exception:
      raise ApiError(api="GitHub 用户信息")

  @staticmethod
  async def get_current_user_emails(access_token: str) -> list[dict[str, Any]]:
    try:
      return await GitHubAPI.get("/user/emails", access_token)
    except Exception:
      raise ApiError(api="GitHub 用户邮箱信息")

  @staticmethod
  async def get_repo_detail(repo_id: str, access_token: str = ""):
    try:
      return await GitHubAPI.get(f"/repos/{repo_id}", access_token)
    except Exception:
      raise ApiError(api="GitHub 仓库信息")

  @staticmethod
  async def get_repo_contributors(repo_id: str, access_token: str = ""):
    try:
      return await GitHubAPI.get(f"/repos/{repo_id}/contributors", access_token)
    except Exception:
      raise ApiError(api="GitHub 仓库贡献者信息")

  @staticmethod
  async def oauth(code: str):
    try:
      response = await client.post(
        "https://github.com/login/oauth/access_token",
        data={
          "client_id": Settings.GITHUB_CLIENT_ID,
          "client_secret": Settings.GITHUB_CLIENT_SECRET,
          "code": code,
          "redirect_uri": Settings.GITHUB_REDIRECT_URI,
          # "state": Settings.GITHUB_STATE,
        },
        headers={"Accept": "application/json"},
      )
      if response.status_code != 200:
        raise AuthenticationError()
      return response.json()
    except Exception:
      raise AuthenticationError(message="GitHub OAuth 认证失败")
