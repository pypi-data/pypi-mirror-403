"""Celery application configuration"""

from yitool.yi_celery import yi_celery


# 配置 Celery 应用
yi_celery.main = "yitech-fastapi-tasks"
yi_celery.conf.broker_url = "redis://localhost:6379/0"
yi_celery.conf.result_backend = "redis://localhost:6379/0"
yi_celery.conf.include = [
    "src.tasks.example_tasks",
    "src.tasks.email_tasks",
]

# 基本配置
yi_celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_default_queue="default",
)


# 为了方便使用，直接导出应用实例
app = yi_celery


def create_yi_celery_app():
    """创建 Celery 应用实例"""
    return yi_celery


def get_yi_celery_app():
    """获取 Celery 应用实例"""
    return yi_celery


def task(*args, **kwargs):
    """task 装饰器"""
    return yi_celery.task(*args, **kwargs)
