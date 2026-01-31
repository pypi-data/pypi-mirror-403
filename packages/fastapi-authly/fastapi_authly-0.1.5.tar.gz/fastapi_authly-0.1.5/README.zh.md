# fastapi-authly

一个可插拔的 FastAPI 认证模块，默认提供基于 JWT 的登录 / 刷新 / 找回密码 / 用户管理，支持通过依赖注入覆盖所有核心实现。内置 Tortoise + Postgres 的默认用户仓储，开箱可用。

## ✨ 特性
- JWT 登录 / 刷新 / 验证
- 用户注册、当前用户信息
- 密码重置（需要自定义 Mailer）
- 可配置路由前缀 / 标签 / 过期时间
- 依赖注入：UserRepository / Mailer / PasswordHasher / TokenService 可替换
- 内置 Tortoise + Postgres 默认实现

## 🚀 快速开始（Tortoise + Postgres 默认实现）

安装：
```bash
uv pip install fastapi-authly
# 或
pip install fastapi-authly
```

最小示例：
```python
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi_authly import AuthConfig, AuthDependencyConfig, create_auth_router
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository

app = FastAPI()

# 初始化 Tortoise + Postgres
register_tortoise(
    app,
    db_url="postgres://user:password@localhost:5432/mydb",
    modules={"models": ["fastapi_authly.models.user"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# 组装路由；若使用默认 /login 路由，建议设置 token_url="login"
config = AuthConfig(token_url="login")
deps = AuthDependencyConfig(user_repository=TortoiseUserRepository())
app.include_router(create_auth_router(config=config, dependencies=deps))

# 可选：设置 Scalar API 文档（内置静态资源，无需手动配置）
from fastapi_authly import setup_scalar_docs
setup_scalar_docs(app, docs_url="/docs", static_url="/static")
```

## 🔌 自定义实现示例

实现 `interfaces.py` 中的协议，传入 `AuthDependencyConfig` 即可：
```python
from fastapi_authly import AuthConfig, AuthDependencyConfig, create_auth_router
from fastapi_authly.interfaces import UserRepository, Mailer

class MyRepo(UserRepository):
    async def get_by_name(self, username: str): ...
    async def get_by_id(self, user_id: str | int): ...
    async def create_user(self, user): ...
    async def to_public(self, user): ...

class MyMailer(Mailer):
    async def send_password_reset(self, request, token): ...
    async def send_verification(self, email, token): ...

config = AuthConfig(router_prefix="/api/auth", token_url="login")
deps = AuthDependencyConfig(user_repository=MyRepo(), mailer=MyMailer())
router = create_auth_router(config=config, dependencies=deps)
```

## 📚 API 文档功能

`fastapi-authly` 内置了 Scalar API 文档支持，包含所有必要的静态资源，无需手动配置：

```python
from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs

app = FastAPI(title="My API")

# 一行代码启用 Scalar 文档
# 自动挂载静态文件到 /static，创建文档页面到 /docs
setup_scalar_docs(app)

# 自定义配置
setup_scalar_docs(
    app,
    docs_url="/api-docs",      # 自定义文档 URL
    static_url="/assets",      # 自定义静态文件前缀
    title="Custom API Docs",   # 自定义标题
    openapi_url="/openapi.json" # 自定义 OpenAPI schema URL
)
```

## 📊 ECharts 图表截图

将 ECharts option 渲染为 PNG 图片，支持任意 ECharts 图表类型（折线、柱状、饼图等）。包内仅包含 `echarts.min.js`；Chrome 与 ChromeDriver 因体积超过 PyPI 单文件 100MB 限制**不随包分发**，需本机安装或通过参数传入路径。

**安装（含图表截图依赖）：**
```bash
pip install fastapi-authly[charts]
# 或
uv pip install "fastapi-authly[charts]"
```

**使用方式一：直接传 ECharts option（通用）：**
```python
from fastapi_authly import render_option_to_png

option = {
    "title": {"text": "案件数量变化趋势", "left": "center"},
    "xAxis": {"type": "category", "data": ["2024-01", "2024-02", "2024-03"]},
    "yAxis": {"type": "value"},
    "series": [{"type": "line", "data": [8, 1, 5], "smooth": True}],
}
path = render_option_to_png(option, "案件数量变化趋势.png", title="案件数量变化趋势")
# path 为输出 PNG 的绝对路径
```

**使用方式二：类型 + 标题 + 数据（便捷封装 line / bar / pie）：**
```python
from fastapi_authly import render_chart_to_png

data = [
    {"month_name": "2024-01", "count": 8},
    {"month_name": "2024-02", "count": 1},
    {"month_name": "2024-03", "count": 5},
]
path = render_chart_to_png("bar", "案件数量变化趋势", data, output_name="趋势柱状图.png")
```

**Chrome/Chromedriver：** 包内不包含，需本机安装（如 `apt install chromium-browser chromium-chromedriver` 或从 [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) 下载）后使用系统路径，或调用时传入 `chrome_headless_path`、`chromedriver_path`。ECharts JS 使用包内 `echarts.min.js`，也可通过 `local_echarts_path` 覆盖。

## 📋 主要接口

- `POST /auth/login`：登录，返回 access_token（可选 refresh_token）
- `POST /auth/token/verify`：验证 token
- `POST /auth/token/refresh`：刷新 access token
- `POST /auth/register`：注册（需要实现 `UserRepository.create_user`）
- `GET /auth/me`：当前用户信息
- `POST /auth/password/reset-request`：请求重置密码（需 Mailer）
- `POST /auth/password/reset`：提交重置密码

> 说明：`OAuth2PasswordBearer` 的 `tokenUrl` 使用 `AuthConfig.token_url`，若使用 `/login` 路由，建议配置 `token_url="login"`。

## ⚙️ 配置项（AuthConfig 部分）

| 参数 | 类型 | 默认值 | 说明 |
| ---- | ---- | ---- | ---- |
| secret_key | str | `"your-secret-key-change-in-production"` | JWT 密钥 |
| algorithm | str | `"HS256"` | JWT 算法 |
| access_token_expire_minutes | int | `30` | Access 过期分钟 |
| refresh_token_expire_days | int | `7` | Refresh 过期天数 |
| router_prefix | str | `"/auth"` | 路由前缀 |
| router_tags | List[str] | `["authentication"]` | 路由标签 |
| token_url | str | `"token"` | OAuth2 tokenUrl（若用 /login，请设为 `"login"`） |
| enable_password_recovery | bool | `True` | 启用找回密码 |
| enable_user_registration | bool | `True` | 启用注册 |
| enable_token_refresh | bool | `True` | 启用刷新 |
| email_from / email_from_name | str | `"noreply@example.com"` / `"Auth System"` | 邮件发件人信息 |

依赖注入容器 `AuthDependencyConfig`：`user_repository` / `password_hasher` / `token_service` / `mailer` 均可传入自定义实现（默认使用包内的密码哈希与 token 实现，user_repository 若未传会默认实例化 `TortoiseUserRepository`）。

## 🏗️ 目录结构
```
fastapi_authly/
├── auth.py                    # 路由组装
├── schemas/                   # Pydantic 请求/响应模型
│   └── user.py
├── models/                    # DB 模型（Tortoise）
│   └── user.py
├── contrib/
│   └── tortoise_pg.py         # 默认 Tortoise Postgres 仓储
├── core/                      # 配置与安全工具
│   ├── config.py
│   ├── security.py
├── interfaces.py              # Protocol 定义
├── __init__.py                # 包导出
└── __about__.py               # 版本
```

## 🧪 测试
```bash
uv pip install -e ".[test]"
uv run pytest
```

## 📦 构建与发布（uv）
```bash
# 构建
uv build

# 发布到 PyPI（需设置 token：UV_PUBLISH_TOKEN 或 --token）
uv publish --token pypi-你的token

# 如需 TestPyPI，请在 pyproject.toml 配置 [[tool.uv.index]] 后：
uv publish --index testpypi --token pypi-你的testpypi-token
```

## 依赖说明
- FastAPI / Pydantic v2
- `tortoise-orm[psycopg]`（默认 Postgres 支持）
- `python-jose`、`passlib` 等安全依赖

## 常见说明
- 登录路由为 `/auth/login`；`token_url` 需与之匹配（设为 `"login"`），否则 OAuth2 依赖的 tokenUrl 会指向 `/auth/token`。
- 密码哈希与 token 生成已内置；用户仓储、邮件发送需按需提供或使用默认 Tortoise 仓储。
- 若出现 passlib 的 `crypt` 弃用警告，可在 pytest `filterwarnings` 中忽略，不影响功能。

## 贡献
欢迎提 Issue / PR。
