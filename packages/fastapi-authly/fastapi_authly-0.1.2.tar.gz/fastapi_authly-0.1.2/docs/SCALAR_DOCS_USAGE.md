# Scalar API 文档功能使用指南

## 概述

`fastapi-authly` 现在内置了 Scalar API 文档支持，包含所有必要的静态资源文件。你无需手动复制静态文件，只需一行代码即可启用美观的 API 文档。

## 快速开始

### 基本使用

```python
from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs

app = FastAPI(title="My API")

# 一行代码启用 Scalar 文档
setup_scalar_docs(app)
```

这将会：
- 自动挂载静态文件到 `/static`
- 创建文档页面到 `/docs`
- 使用应用的 `title` 和 `openapi_url`

### 完整示例

```python
from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs, create_auth_router, AuthConfig, AuthDependencyConfig
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI(
    title="Complaint API",
    description="Complaint Data Streaming API",
    version="2.0.1",
)

# 初始化数据库
register_tortoise(
    app,
    db_url="postgres://user:password@localhost:5432/mydb",
    modules={"models": ["fastapi_authly.models.user"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# 配置认证路由
config = AuthConfig()
deps = AuthDependencyConfig(user_repository=TortoiseUserRepository())
auth_router = create_auth_router(config=config, dependencies=deps)
app.include_router(auth_router)

# 设置 Scalar 文档
setup_scalar_docs(app, docs_url="/docs", static_url="/static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 自定义配置

```python
setup_scalar_docs(
    app,
    docs_url="/api-docs",        # 自定义文档 URL
    static_url="/assets",        # 自定义静态文件前缀
    title="Custom API Docs",     # 自定义标题
    openapi_url="/openapi.json"  # 自定义 OpenAPI schema URL
)
```

## 参数说明

- `app` (必需): FastAPI 应用实例
- `docs_url` (可选): 文档页面 URL，默认为 `"/docs"`
- `static_url` (可选): 静态文件 URL 前缀，默认为 `"/static"`
- `title` (可选): 文档标题，默认使用 `app.title`
- `openapi_url` (可选): OpenAPI schema URL，默认使用 `app.openapi_url`

## 注意事项

1. **静态文件位置**: 静态文件已经打包在 `fastapi_authly` 包内，无需手动复制
2. **URL 冲突**: 确保 `docs_url` 和 `static_url` 不与现有路由冲突
3. **OpenAPI Schema**: 确保 FastAPI 应用已启用 OpenAPI schema（默认启用）

## 迁移指南

如果你之前手动配置了 Scalar 文档，可以按以下步骤迁移：

### 之前的方式

```python
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def scalar_html(_app):
    html_content = f"""
    <!DOCTYPE html>
    ...
    """
    return HTMLResponse(content=html_content)
```

### 现在的方式

```python
from fastapi_authly import setup_scalar_docs

# 一行代码替代上面的所有配置
setup_scalar_docs(app, docs_url="/docs", static_url="/static")
```

## 优势

1. **无需手动管理静态文件**: 所有静态资源已打包在包内
2. **简单易用**: 一行代码即可启用
3. **可移植**: 其他项目安装包后即可使用，无需额外配置
4. **可定制**: 支持自定义 URL 和标题
