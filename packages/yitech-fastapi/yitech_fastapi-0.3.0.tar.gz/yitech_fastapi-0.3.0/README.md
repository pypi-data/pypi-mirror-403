# Yitech FastAPI

一个基于 FastAPI 构建的现代后端服务框架，采用分层架构设计，支持异步操作、事件驱动和任务队列。

## 🚀 技术栈

### 核心框架
- **FastAPI** `>=0.128.0` - 高性能异步 Web 框架
- **Python** `>=3.12` - 编程语言

### 数据库
- **yi_db** (集成在 yitool 中) - 统一数据库抽象层，支持多种数据库后端
- **SQLAlchemy** `>=2.0.45` - 异步 ORM (yi_db 内部使用)
- **Alembic** `>=1.17.2` - 数据库迁移工具

### 缓存与会话
- **Redis** `>=7.1.0` - 缓存和会话存储
- **aioredis** `>=2.0.1` - Redis 异步客户端

### 任务队列
- **Celery** `>=5.3.1` - 分布式任务队列

### 认证与安全
- **python-jose** `>=3.5.0` - JWT 认证
- **passlib** `>=1.7.4` - 密码哈希
- **bcrypt** `==4.0.1` - 密码加密算法

### 数据验证
- **Pydantic** `>=2.12.5` - 数据验证和设置管理
- **pydantic-settings** `>=2.12.0` - 配置管理
- **email-validator** `>=2.3.0` - 邮箱验证

### 开发工具
- **Ruff** `>=0.6.0` - 代码检查器
- **Mypy** `>=1.19.1` - 静态类型检查
- **Pytest** `>=9.0.2` - 测试框架
- **pytest-asyncio** `>=1.3.0` - 异步测试支持
- **HTTPX** `>=0.28.1` - HTTP 客户端
- **UV** - 依赖管理工具

## 📦 快速开始

### 安装依赖

```bash
# 使用 UV 安装依赖
uv install

# 安装开发依赖
uv install -g dev
```

### 配置环境变量

创建 `.env` 文件并配置必要的环境变量：

```bash
# 复制示例配置
cp application.yml.example application.yml

# 编辑配置文件
vim application.yml
```

### 数据库迁移

```bash
# 创建迁移脚本
uv run alembic revision --autogenerate -m "Initial migration"

# 执行迁移
uv run alembic upgrade head
```

### 启动服务

```bash
# 启动 Web 服务
./bin/run_fast.sh

# 启动 Celery Worker
./bin/run_celery.sh
```

### 访问 API 文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📁 项目结构

```
├── alembic/              # 数据库迁移
├── bin/                  # 脚本文件
├── src/                  # 主代码目录
│   ├── events/           # 事件系统
│   ├── health/           # 健康检查
│   ├── helpers/          # 辅助功能
│   ├── routes/           # 路由模块
│   │   ├── auth/         # 认证模块
│   │   └── users/        # 用户模块
│   ├── tasks/            # 异步任务
│   ├── utils/            # 工具函数
│   ├── app.py            # 应用配置
│   ├── config.py         # 配置管理
│   └── main.py           # 应用入口
├── tests/                # 测试代码
│   ├── api/              # API 测试
│   └── unit/             # 单元测试
├── alembic.ini           # Alembic 配置
├── application.yml       # 应用配置
├── pyproject.toml        # 项目元数据和依赖
└── uv.lock               # 依赖锁定
```

## 🛠️ 开发流程

### 代码检查

```bash
# 运行 Ruff 代码检查
./bin/run_lint.sh
```

### 类型检查

```bash
uv run mypy src/
```

### 运行测试

```bash
# 运行所有测试
./bin/run_test.sh
```

## 🧪 测试

项目使用 Pytest 进行测试，支持异步测试。测试文件位于 `tests/` 目录下，主要包括：

- 单元测试
- 集成测试
- API 测试

### 测试配置

测试使用内存数据库和内存会话存储，避免外部依赖。配置文件位于 `tests/conftest.py`。

## 🚀 部署

### 生产环境

```bash
# 安装生产依赖
uv install --no-dev

# 启动生产服务
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 部署

```bash
# 构建 Docker 镜像
docker build -t yitech-fastapi .

# 运行 Docker 容器
docker run -d -p 8000:8000 --env-file .env yitech-fastapi
```

## 🔧 核心功能

### 用户认证与授权
- JWT 认证
- 密码哈希与验证
- 权限控制

### 用户管理
- 用户创建、查询、更新和删除
- 用户信息验证
- 用户密码重置

### 会话管理
- 基于 yitool 的会话管理
- 会话过期管理
- 会话验证

### 异步任务处理
- Celery 任务队列
- 定时任务
- 任务结果跟踪

### 事件系统
- 事件发布与订阅
- 事件处理
- 异步事件支持

### 中间件
- 请求 ID 跟踪
- 请求日志记录
- CORS 支持
- 会话管理

## 📝 贡献指南

### 开发规范

1. **代码风格**：遵循 PEP 8 规范，使用 Ruff 进行检查
2. **类型注解**：所有函数和方法都必须添加类型注解
3. **文档字符串**：所有公共函数和类都必须添加文档字符串
4. **测试覆盖**：新功能必须添加相应的测试用例

### 提交规范

使用 Conventional Commits 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建或工具相关

## 📄 许可证

MIT License

## 🤝 联系我们

如有任何问题或建议，请提交 Issue 或 Pull Request。

---

**Yitech FastAPI** - 现代化的异步后端服务框架