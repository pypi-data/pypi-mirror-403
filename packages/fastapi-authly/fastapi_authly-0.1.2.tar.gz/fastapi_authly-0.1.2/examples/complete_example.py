"""
完整示例：展示如何像原项目一样使用 fastapi-authly 的文档功能
"""

from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs, create_auth_router, AuthConfig, AuthDependencyConfig
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository
from tortoise.contrib.fastapi import register_tortoise, tortoise_exception_handlers
from contextlib import asynccontextmanager

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    yield
    # 关闭时执行

# 创建 FastAPI 应用
app = FastAPI(
    title="Complaint API",
    description="Complaint Data Streaming API",
    version="2.0.1",
    exception_handlers=tortoise_exception_handlers(),
    lifespan=lifespan,
    docs_url="/old_docs",  # 保留旧的 docs，但使用 Scalar
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
# 这会自动挂载静态文件并创建文档页面
setup_scalar_docs(
    app,
    docs_url="/docs",  # 文档页面 URL
    static_url="/static",  # 静态文件 URL 前缀（与原来的保持一致）
)

# 其他 API 路由
@app.get("/")
async def root():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3040,
        loop="uvloop",
    )
