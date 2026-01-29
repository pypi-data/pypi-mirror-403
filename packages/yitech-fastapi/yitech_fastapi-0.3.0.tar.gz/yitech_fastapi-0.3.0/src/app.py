from os import path
from yitool.yi_fast import YiFast

# 导入路由模块
from src.config import config
from src.health import health_router
from src.routes.auth import auth_router
from src.routes.users import users_router
from src.tasks import tasks_router


# 中间件配置
middlewares = [
]

# 路由配置
routers = [
    health_router,
    auth_router,
    users_router,
    tasks_router,
]


def create_app():
    """创建并初始化 FastAPI 应用"""

    # 创建应用实例
    app = YiFast.from_config(config)
    
    # 初始化应用
    app.bootstrap(middlewares, routers)
    
    return app
