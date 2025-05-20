from fastapi import APIRouter
from api.endpoints import auth, users, projects, comments, tags, ratings, notifications, favorites

router = APIRouter()

# 认证路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户路由
router.include_router(users.router, prefix="/users", tags=["用户"])

# 项目路由
router.include_router(projects.router, prefix="/projects", tags=["项目"])

# 评论路由
router.include_router(comments.router, prefix="/comments", tags=["评论"])

# 标签路由
router.include_router(tags.router, prefix="/tags", tags=["标签"])

# 评分路由
router.include_router(ratings.router, prefix="/ratings", tags=["评分"])

# 通知路由
router.include_router(notifications.router,
                      prefix="/notifications", tags=["通知"])

# 收藏路由
router.include_router(favorites.router, prefix="/favorites", tags=["收藏"])
