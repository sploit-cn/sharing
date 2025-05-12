from fastapi import APIRouter
from api.endpoints import auth, users, projects, comments, tags

router = APIRouter()

# 认证路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户路由
router.include_router(users.router, prefix="/users", tags=["用户"])

# 项目路由
router.include_router(projects.router, prefix="/projects", tags=["项目"])

# # 评论路由
# router.include_router(comments.router, prefix="/comments", tags=["评论"])

# # 标签路由
# router.include_router(tags.router, prefix="/tags", tags=["标签"])
