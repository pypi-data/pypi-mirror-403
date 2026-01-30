# Scalar 文档功能集成说明

## 改动概述

已将 Scalar API 文档功能集成到 `fastapi-authly` 包中，包含所有必要的静态资源文件。用户只需导入并使用 `setup_scalar_docs` 函数即可启用文档功能，无需手动管理静态文件。

## 新增文件

1. **`src/fastapi_authly/docs.py`**: 文档功能模块
   - `setup_scalar_docs()`: 主要函数，用于设置 Scalar 文档
   - `get_static_dir()`: 获取包内静态文件目录路径

2. **`src/fastapi_authly/static/scalar/`**: 静态资源目录
   - `standalone.js`: Scalar JavaScript 文件
   - `style.css`: Scalar CSS 样式文件

3. **示例文件**:
   - `examples/use_scalar_docs.py`: 基本使用示例
   - `examples/complete_example.py`: 完整使用示例
   - `docs/SCALAR_DOCS_USAGE.md`: 详细使用文档

## 修改文件

1. **`src/fastapi_authly/__init__.py`**:
   - 添加 `setup_scalar_docs` 的导入和导出

2. **`README.md` 和 `README.zh.md`**:
   - 添加 Scalar 文档功能的使用说明

## 使用方法

### 基本使用

```python
from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs

app = FastAPI(title="My API")
setup_scalar_docs(app)
```

### 自定义配置

```python
setup_scalar_docs(
    app,
    docs_url="/api-docs",
    static_url="/assets",
    title="Custom API Docs",
    openapi_url="/openapi.json"
)
```

## 优势

1. **零配置**: 无需手动复制静态文件
2. **可移植**: 安装包后即可使用
3. **简单**: 一行代码启用
4. **灵活**: 支持自定义 URL 和配置

## 构建和发布

静态文件会自动包含在构建的包中，因为它们在 `src/fastapi_authly/static/` 目录下，属于包的一部分。

构建和发布流程不变：

```bash
uv build
uv publish --token your-token
```

## 测试

安装包后，可以这样测试：

```python
from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs

app = FastAPI(title="Test API")
setup_scalar_docs(app)

# 运行应用后，访问 http://localhost:8000/docs 即可看到文档
```
