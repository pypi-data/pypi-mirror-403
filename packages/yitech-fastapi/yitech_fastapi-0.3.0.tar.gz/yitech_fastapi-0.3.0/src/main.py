from yitool.log import info, setup_logging
from src.app import create_app

# 设置日志
setup_logging()

app = create_app()

# 添加根路径端点
@app.get("/")
async def root():
    """根路径端点，返回应用信息"""
    return {
        "app": "yitech-fastapi",
        "version": "1.0.0",
        "status": "running",
    }

# 应用启动日志
info("🚀 应用启动成功! 欢迎使用 yitech-fastapi")

