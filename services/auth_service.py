from core.exceptions.client_errors import AuthenticationError
from models.models import User
from utils.gitee_api import GiteeAPI
from utils.github_api import GitHubAPI
from utils.security import verify_password


class AuthService:
  @staticmethod
  async def authenticate_user(username: str, password: str) -> User | None:
    """验证用户"""
    user = await User.get_or_none(username=username)
    if not user:
      return None
    if not verify_password(password, user.password_hash):
      return None
    return user

  @staticmethod
  async def github_auth(code: str) -> str:
    """通过 GitHub 认证"""
    data = await GitHubAPI.oauth(code)
    if "access_token" not in data:
      raise AuthenticationError(message="GitHub OAuth 认证失败")
    return data["access_token"]

  @staticmethod
  async def gitee_auth(code: str) -> tuple[str, str]:
    """通过 Gitee 认证"""
    data = await GiteeAPI.oauth(code)
    if "access_token" not in data or "refresh_token" not in data:
      raise AuthenticationError(message="Gitee OAuth 认证失败")
    return data["access_token"], data["refresh_token"]
