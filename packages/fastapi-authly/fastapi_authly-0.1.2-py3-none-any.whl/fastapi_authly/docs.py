"""API 文档功能模块 - 提供 Scalar API 文档支持"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


def get_static_dir() -> Path:
    """获取包内静态文件目录路径"""
    return Path(__file__).parent / "static"


def setup_scalar_docs(
    app: FastAPI,
    *,
    docs_url: str = "/docs",
    static_url: str = "/static",
    title: Optional[str] = None,
    openapi_url: Optional[str] = None,
) -> None:
    """
    为 FastAPI 应用设置 Scalar API 文档
    
    Args:
        app: FastAPI 应用实例
        docs_url: 文档页面 URL，默认为 "/docs"
        static_url: 静态文件 URL 前缀，默认为 "/static"
        title: 文档标题，默认使用 app.title
        openapi_url: OpenAPI schema URL，默认使用 app.openapi_url
    """
    static_dir = get_static_dir()
    
    # 挂载静态文件
    if os.path.exists(static_dir):
        app.mount(static_url, StaticFiles(directory=str(static_dir)), name="static")
    
    # 设置文档标题和 OpenAPI URL
    doc_title = title or app.title
    api_url = openapi_url or app.openapi_url
    
    # 创建文档路由
    @app.get(docs_url, include_in_schema=False)
    async def scalar_html():
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{doc_title}</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1"/>
            <link rel="stylesheet" href="{static_url}/scalar/style.css">
        </head>
        <body>
            <div id="app"></div>
            <script src="{static_url}/scalar/standalone.js"></script>
            <script>
                Scalar.createApiReference('#app', {{
                    spec: {{
                        url: '{api_url}'
                    }}
                }})
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
