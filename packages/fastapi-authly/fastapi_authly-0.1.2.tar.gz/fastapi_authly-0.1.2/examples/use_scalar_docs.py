"""
使用示例：如何在项目中使用 fastapi-authly 的 Scalar 文档功能
"""

from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs, create_auth_router, AuthConfig, AuthDependencyConfig
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository
from tortoise.contrib.fastapi import register_tortoise

# 创建 FastAPI 应用
app = FastAPI(
    title="My API",
    description="My API with Scalar Documentation",
    version="1.0.0",
)

# 配置认证路由（示例）
config = AuthConfig()
deps = AuthDependencyConfig(user_repository=TortoiseUserRepository())
auth_router = create_auth_router(config=config, dependencies=deps)
app.include_router(auth_router)

# 设置 Scalar 文档
# 这会自动：
# 1. 挂载静态文件到 /static
# 2. 创建文档页面到 /docs
setup_scalar_docs(
    app,
    docs_url="/docs",  # 文档页面 URL
    static_url="/static",  # 静态文件 URL 前缀
)

# 或者自定义配置
# setup_scalar_docs(
#     app,
#     docs_url="/api-docs",  # 自定义文档 URL
#     static_url="/assets",  # 自定义静态文件前缀
#     title="Custom API Docs",  # 自定义标题
#     openapi_url="/openapi.json",  # 自定义 OpenAPI schema URL
# )

# 初始化数据库（示例）
register_tortoise(
    app,
    db_url="postgres://user:password@localhost:5432/mydb",
    modules={"models": ["fastapi_authly.models.user"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
