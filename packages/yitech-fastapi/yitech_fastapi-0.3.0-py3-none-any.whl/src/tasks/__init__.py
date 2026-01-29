"""Celery tasks module"""

# 导出创建 Celery 应用实例的函数和路由
from .celery_app import create_yi_celery_app, get_yi_celery_app, task
from .router import router as tasks_router

__all__ = ["create_yi_celery_app", "get_yi_celery_app", "task", "tasks_router"]
