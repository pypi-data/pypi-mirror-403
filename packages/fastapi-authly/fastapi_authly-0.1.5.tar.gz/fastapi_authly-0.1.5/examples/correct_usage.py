"""
正确的使用方式示例
"""

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi_authly import (
    AuthConfig, 
    AuthDependencyConfig, 
    create_auth_router,
    JwtConfig,
    setup_scalar_docs
)
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository

app = FastAPI(title="FastAPI Authly 测试应用")

# 初始化 Tortoise + Postgres
register_tortoise(
    app,
    db_url="postgres://user:password@localhost:5432/testdb",
    modules={"models": ["fastapi_authly.models.user"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# 方式 1: 使用 JwtConfig 实例（推荐）
config = AuthConfig(
    jwt=JwtConfig(
        secret_key="your-secret-key-change-in-production",
        algorithm="HS256",
        access_token_expires_minutes=30,
        refresh_token_expire_days=7,
    ),
    router_prefix="/auth",
    token_url="login",
)

# 方式 2: 使用字典更新（也可以）
# config = AuthConfig(
#     jwt={
#         "secret_key": "your-secret-key-change-in-production",
#         "algorithm": "HS256",
#         "access_token_expires_minutes": 30,
#     },
#     router_prefix="/auth",
#     token_url="login",
# )

# 方式 3: 使用默认配置，然后通过环境变量覆盖
# 设置环境变量: AUTH_JWT__SECRET_KEY=your-secret-key
# config = AuthConfig(
#     router_prefix="/auth",
#     token_url="login",
# )

deps = AuthDependencyConfig(
    user_repository=TortoiseUserRepository(),
)

# 注册认证路由
auth_router = create_auth_router(config=config, dependencies=deps)
app.include_router(auth_router)

# 设置 Scalar 文档
setup_scalar_docs(app, docs_url="/docs", static_url="/static")

@app.get("/")
async def root():
    return {"message": "FastAPI Authly 测试应用已启动"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
