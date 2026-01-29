"""yifast CLI 主入口"""

import click
import os
import shutil
import secrets
import json
import subprocess
from typing import Optional
from src.templates.manager import template_manager


def get_project_root():
    """获取项目根目录
    
    Returns:
        str: 项目根目录的绝对路径
    """
    return os.path.abspath(os.getcwd())


def get_cli_root():
    """获取 CLI 工具根目录
    
    Returns:
        str: CLI 工具根目录的绝对路径
    """
    return os.path.abspath(os.path.dirname(__file__))


def ensure_dir(path):
    """确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 是否成功创建目录
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        click.echo(f"错误: 创建目录失败: {e}", err=True)
        return False


@click.group()
@click.version_option(version="1.0.0", prog_name="yifast")
def cli() -> None:
    """yifast - FastAPI 脚手架工具
    
    用于快速创建、管理和扩展 FastAPI 项目的命令行工具。
    """
    pass


@cli.command()
@click.argument("name", required=False, default=".")
@click.option("--template", "-t", default="default", help="项目模板类型")
@click.option("--python-version", "-p", default="3.12", help="Python 版本")
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有目录")
def init(name: str, template: str, python_version: str, force: bool) -> None:
    """初始化一个新的 FastAPI 项目
    
    NAME: 项目名称或目录路径，默认为当前目录
    """
    click.echo(f"初始化项目: {name}")
    click.echo(f"使用模板: {template}")
    click.echo(f"Python 版本: {python_version}")
    click.echo(f"强制模式: {force}")
    
    try:
        # 检查目录是否存在
        if os.path.exists(name) and not force:
            click.echo("错误: 目录已存在，请使用 --force 选项强制覆盖")
            return
        
        # 创建项目目录
        if os.path.exists(name) and force:
            try:
                shutil.rmtree(name)
            except Exception as e:
                click.echo(f"错误: 无法删除现有目录: {e}", err=True)
                return
        try:
            os.makedirs(name, exist_ok=True)
        except Exception as e:
            click.echo(f"错误: 创建目录失败: {e}", err=True)
            return
        
        # 获取项目目录的绝对路径
        project_dir = os.path.abspath(name)
        click.echo(f"项目目录: {project_dir}")
        
        # 生成随机密钥
        secret_key = secrets.token_urlsafe(32)
        
        # 项目配置
        project_name = os.path.basename(project_dir)
        
        # 渲染模板
        context = {
            "project_name": project_name,
            "python_version": python_version,
            "secret_key": secret_key,
            "year": 2026,
        }
        
        # 渲染 pyproject.toml
        pyproject_path = os.path.join(name, "pyproject.toml")
        try:
            template_manager.render_file("pyproject.toml.j2", pyproject_path, context)
            click.echo(f"✓ 创建 pyproject.toml")
        except Exception as e:
            click.echo(f"错误: 创建 pyproject.toml 失败: {e}", err=True)
            return
        
        # 渲染 application.yml
        app_yml_path = os.path.join(name, "application.yml")
        try:
            template_manager.render_file("application.yml.j2", app_yml_path, context)
            click.echo(f"✓ 创建 application.yml")
        except Exception as e:
            click.echo(f"错误: 创建 application.yml 失败: {e}", err=True)
            return
        
        # 创建 README.md
        readme_path = os.path.join(name, "README.md")
        readme_content = f"""# {project_name}

基于 FastAPI 构建的现代后端服务。

## 快速开始

### 安装依赖

```bash
uv install
uv install -g dev
```

### 运行服务

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 项目结构

- `src/` - 源代码目录
- `tests/` - 测试代码目录
- `alembic/` - 数据库迁移目录
- `bin/` - 脚本目录
"""
        try:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            click.echo(f"✓ 创建 README.md")
        except Exception as e:
            click.echo(f"错误: 创建 README.md 失败: {e}", err=True)
            return
        
        # 创建 .gitignore
        gitignore_path = os.path.join(name, ".gitignore")
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
.venv/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Build
dist/
build/
*.egg-info/
*.egg

# Testing
coverage.xml
.pytest_cache/
.tox/

# Environment
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# Docker
docker-compose.override.yml
"""
        try:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(gitignore_content)
            click.echo(f"✓ 创建 .gitignore")
        except Exception as e:
            click.echo(f"错误: 创建 .gitignore 失败: {e}", err=True)
            return
        
        click.echo("\n项目初始化完成！")
        click.echo(f"\n下一步：")
        click.echo(f"1. 进入项目目录: cd {name}")
        click.echo(f"2. 安装依赖: uv install")
        click.echo(f"3. 运行服务: python -m uvicorn src.main:app --reload")
    except Exception as e:
        click.echo(f"错误: 初始化项目失败: {e}", err=True)
        return


@cli.command()
@click.argument("type")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有文件")
def generate(type: str, name: str, force: bool) -> None:
    """生成代码文件
    
    TYPE: 生成类型 (api, model, service, schema, test)
    NAME: 生成的名称
    """
    click.echo(f"生成 {type}: {name}")
    click.echo(f"强制模式: {force}")
    
    try:
        # 验证类型
        valid_types = ["api", "model", "service", "schema", "test"]
        if type not in valid_types:
            click.echo(f"错误: 无效的类型，支持的类型: {', '.join(valid_types)}", err=True)
            return
        
        # 处理名称格式
        api_name = name.capitalize()
        api_name_lower = api_name.lower()
        
        # 生成 API 相关文件
        if type == "api":
            # 创建目录结构
            api_dir = os.path.join("src", "routes", api_name_lower)
            try:
                os.makedirs(api_dir, exist_ok=True)
            except Exception as e:
                click.echo(f"错误: 创建目录失败: {e}", err=True)
                return
            
            # 生成 __init__.py
            init_path = os.path.join(api_dir, "__init__.py")
            init_content = f"""from .router import router
from .models import {api_name}
from .schemas import {api_name}Create, {api_name}Update, {api_name}Response

__all__ = ["router", "{api_name}", "{api_name}Create", "{api_name}Update", "{api_name}Response"]
"""
            if not os.path.exists(init_path) or force:
                try:
                    with open(init_path, "w", encoding="utf-8") as f:
                        f.write(init_content)
                    click.echo(f"✓ 创建 {api_name_lower}/__init__.py")
                except Exception as e:
                    click.echo(f"错误: 创建 __init__.py 失败: {e}", err=True)
                    return
            
            # 生成 models.py
            models_path = os.path.join(api_dir, "models.py")
            if not os.path.exists(models_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/models.py.j2", models_path, context)
                    click.echo(f"✓ 创建 {api_name_lower}/models.py")
                except Exception as e:
                    click.echo(f"错误: 创建 models.py 失败: {e}", err=True)
                    return
            
            # 生成 schemas.py
            schemas_path = os.path.join(api_dir, "schemas.py")
            if not os.path.exists(schemas_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/schemas.py.j2", schemas_path, context)
                    click.echo(f"✓ 创建 {api_name_lower}/schemas.py")
                except Exception as e:
                    click.echo(f"错误: 创建 schemas.py 失败: {e}", err=True)
                    return
            
            # 生成 service.py
            service_path = os.path.join(api_dir, "service.py")
            if not os.path.exists(service_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/service.py.j2", service_path, context)
                    click.echo(f"✓ 创建 {api_name_lower}/service.py")
                except Exception as e:
                    click.echo(f"错误: 创建 service.py 失败: {e}", err=True)
                    return
            
            # 生成 router.py
            router_path = os.path.join(api_dir, "router.py")
            if not os.path.exists(router_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/router.py.j2", router_path, context)
                    click.echo(f"✓ 创建 {api_name_lower}/router.py")
                except Exception as e:
                    click.echo(f"错误: 创建 router.py 失败: {e}", err=True)
                    return
            
            # 提示更新路由注册
            click.echo("\n✓ API 模块生成完成！")
            click.echo("\n请记得在 src/app.py 中注册路由：")
            click.echo(f"1. 添加导入: from src.routes.{api_name_lower} import router as {api_name_lower}_router")
            click.echo(f"2. 在 routers 列表中添加: {api_name_lower}_router")
        
        elif type == "model":
            # 生成独立模型文件
            models_dir = os.path.join("src", "models")
            try:
                os.makedirs(models_dir, exist_ok=True)
            except Exception as e:
                click.echo(f"错误: 创建目录失败: {e}", err=True)
                return
            
            model_path = os.path.join(models_dir, f"{api_name_lower}.py")
            if not os.path.exists(model_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/models.py.j2", model_path, context)
                    click.echo(f"✓ 创建 models/{api_name_lower}.py")
                except Exception as e:
                    click.echo(f"错误: 创建模型文件失败: {e}", err=True)
                    return
        
        elif type == "service":
            # 生成独立服务文件
            services_dir = os.path.join("src", "services")
            try:
                os.makedirs(services_dir, exist_ok=True)
            except Exception as e:
                click.echo(f"错误: 创建目录失败: {e}", err=True)
                return
            
            service_path = os.path.join(services_dir, f"{api_name_lower}.py")
            if not os.path.exists(service_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/service.py.j2", service_path, context)
                    click.echo(f"✓ 创建 services/{api_name_lower}.py")
                except Exception as e:
                    click.echo(f"错误: 创建服务文件失败: {e}", err=True)
                    return
        
        elif type == "schema":
            # 生成独立 schema 文件
            schemas_dir = os.path.join("src", "schemas")
            try:
                os.makedirs(schemas_dir, exist_ok=True)
            except Exception as e:
                click.echo(f"错误: 创建目录失败: {e}", err=True)
                return
            
            schema_path = os.path.join(schemas_dir, f"{api_name_lower}.py")
            if not os.path.exists(schema_path) or force:
                try:
                    context = {"api_name": api_name}
                    template_manager.render_file("src/routes/api/schemas.py.j2", schema_path, context)
                    click.echo(f"✓ 创建 schemas/{api_name_lower}.py")
                except Exception as e:
                    click.echo(f"错误: 创建 schema 文件失败: {e}", err=True)
                    return
        
        elif type == "test":
            # 生成测试文件
            test_dir = os.path.join("tests", "api")
            try:
                os.makedirs(test_dir, exist_ok=True)
            except Exception as e:
                click.echo(f"错误: 创建目录失败: {e}", err=True)
                return
            
            test_path = os.path.join(test_dir, f"test_{api_name_lower}.py")
            if not os.path.exists(test_path) or force:
                test_content = f"""import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app


async def test_create_{api_name_lower}(async_test_client):
    '测试创建 {api_name}'
    test_data = {
        "name": "测试{api_name}",
        "description": "测试{api_name}描述",
        "is_active": True
    }
    
    response = await async_test_client.post(f"/api/{api_name_lower}", json=test_data)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == test_data["name"]


async def test_get_{api_name_lower}_list(async_test_client):
    '测试获取 {api_name} 列表'
    response = await async_test_client.get(f"/api/{api_name_lower}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_{api_name_lower}(async_test_client):
    '测试获取单个 {api_name}'
    # 先创建一个 {api_name}
    test_data = {
        "name": "测试{api_name}",
        "description": "测试{api_name}描述",
        "is_active": True
    }
    create_response = await async_test_client.post(f"/api/{api_name_lower}", json=test_data)
    {api_name_lower}_id = create_response.json()["data"]["id"]
    
    # 获取 {api_name}
    response = await async_test_client.get(f"/api/{api_name_lower}/{{{api_name_lower}_id}}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == {api_name_lower}_id


async def test_update_{api_name_lower}(async_test_client):
    '测试更新 {api_name}'
    # 先创建一个 {api_name}
    test_data = {
        "name": "测试{api_name}",
        "description": "测试{api_name}描述",
        "is_active": True
    }
    create_response = await async_test_client.post(f"/api/{api_name_lower}", json=test_data)
    {api_name_lower}_id = create_response.json()["data"]["id"]
    
    # 更新 {api_name}
    update_data = {
        "name": "更新测试{api_name}",
        "description": "更新测试{api_name}描述"
    }
    response = await async_test_client.put(f"/api/{api_name_lower}/{{{api_name_lower}_id}}", json=update_data)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == update_data["name"]


async def test_delete_{api_name_lower}(async_test_client):
    '测试删除 {api_name}'
    # 先创建一个 {api_name}
    test_data = {
        "name": "测试{api_name}",
        "description": "测试{api_name}描述",
        "is_active": True
    }
    create_response = await async_test_client.post(f"/api/{api_name_lower}", json=test_data)
    {api_name_lower}_id = create_response.json()["data"]["id"]
    
    # 删除 {api_name}
    response = await async_test_client.delete(f"/api/{api_name_lower}/{{{api_name_lower}_id}}")
    assert response.status_code == 204
"""
                try:
                    with open(test_path, "w", encoding="utf-8") as f:
                        f.write(test_content)
                    click.echo(f"✓ 创建 tests/api/test_{api_name_lower}.py")
                except Exception as e:
                    click.echo(f"错误: 创建测试文件失败: {e}", err=True)
                    return
    except Exception as e:
        click.echo(f"错误: 生成代码失败: {e}", err=True)
        return


@cli.command()
@click.argument("module")
@click.option("--version", "-v", help="模块版本")
def add(module: str, version: Optional[str]) -> None:
    """添加新模块或功能
    
    MODULE: 模块名称
    """
    click.echo(f"添加模块: {module}")
    if version:
        click.echo(f"版本: {version}")
    
    try:
        # 实现模块添加逻辑
        # 1. 检查模块是否存在
        # 2. 下载或复制模块文件
        # 3. 更新项目配置
        # 4. 安装依赖
        
        # 检查模块是否为有效的模块名称
        valid_modules = ["auth", "users", "tasks", "events", "health"]
        if module not in valid_modules:
            click.echo(f"错误: 无效的模块名称，支持的模块: {', '.join(valid_modules)}", err=True)
            return
        
        # 创建模块目录
        module_dir = os.path.join("src", "routes", module)
        try:
            os.makedirs(module_dir, exist_ok=True)
        except Exception as e:
            click.echo(f"错误: 创建模块目录失败: {e}", err=True)
            return
        
        # 生成模块文件
        init_path = os.path.join(module_dir, "__init__.py")
        router_path = os.path.join(module_dir, "router.py")
        models_path = os.path.join(module_dir, "models.py")
        schemas_path = os.path.join(module_dir, "schemas.py")
        service_path = os.path.join(module_dir, "service.py")
        
        # 生成 __init__.py
        try:
            with open(init_path, "w", encoding="utf-8") as f:
                f.write(f"""from .router import router

__all__ = ["router"]
""")
            click.echo(f"✓ 创建 {module}/__init__.py")
        except Exception as e:
            click.echo(f"错误: 创建 __init__.py 失败: {e}", err=True)
            return
        
        # 生成 router.py
        try:
            with open(router_path, "w", encoding="utf-8") as f:
                f.write(f"""from fastapi import APIRouter

router = APIRouter(prefix="/{module}", tags=["{module}"])


@router.get("/")
async def get_{module}():
    '获取 {module} 列表'
    return {"message": "Get {module} list"}


@router.get("/{{{module}_id}}")
async def get_{module}_by_id({module}_id: int):
    '获取单个 {module}'
    return {{"message": "Get {module} by id: {{{module}_id}}"}}
""")
            click.echo(f"✓ 创建 {module}/router.py")
        except Exception as e:
            click.echo(f"错误: 创建 router.py 失败: {e}", err=True)
            return
        
        click.echo(f"\n✓ 模块 {module} 添加完成！")
        click.echo(f"\n请记得在 src/app.py 中注册路由：")
        click.echo(f"1. 添加导入: from src.routes.{module} import router as {module}_router")
        click.echo(f"2. 在 routers 列表中添加: {module}_router")
    except Exception as e:
        click.echo(f"错误: 添加模块失败: {e}", err=True)
        return


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "-l", is_flag=True, help="列出所有配置")
def config(key: Optional[str], value: Optional[str], list: bool) -> None:
    """管理项目配置
    
    KEY: 配置键
    VALUE: 配置值
    """
    try:
        # 配置文件路径
        config_dir = os.path.join(os.getcwd(), ".yifast")
        config_file = os.path.join(config_dir, "config.json")
        
        # 确保配置目录存在
        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            click.echo(f"错误: 创建配置目录失败: {e}", err=True)
            return
        
        # 加载现有配置
        config_data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception as e:
                click.echo(f"错误: 加载配置文件失败: {e}", err=True)
                return
        
        if list:
            click.echo("列出所有配置:")
            if config_data:
                for k, v in config_data.items():
                    click.echo(f"  {k}: {v}")
            else:
                click.echo("  无配置项")
        elif key and value:
            click.echo(f"设置配置: {key} = {value}")
            # 更新配置
            config_data[key] = value
            # 保存配置
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2)
                click.echo("✓ 配置设置成功！")
            except Exception as e:
                click.echo(f"错误: 保存配置失败: {e}", err=True)
                return
        elif key:
            click.echo(f"获取配置: {key}")
            if key in config_data:
                click.echo(f"  {key}: {config_data[key]}")
            else:
                click.echo(f"  配置项不存在")
        else:
            click.echo("请提供配置键或使用 --list 选项", err=True)
    except Exception as e:
        click.echo(f"错误: 管理配置失败: {e}", err=True)
        return


def main():
    """主入口函数"""
    cli()


if __name__ == "__main__":
    main()
