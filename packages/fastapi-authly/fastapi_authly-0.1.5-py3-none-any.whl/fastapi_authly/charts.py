# -*- coding: utf-8 -*-
"""
ECharts option 自组装 HTML → 包内 ECharts JS → 本地 Chrome 截图

通用入口：直接传入 ECharts option 字典，不限定图表类型。
- 包内仅包含 echarts.min.js（Chrome/Chromedriver 因体积超 PyPI 限制不随包分发）。
- Chrome 与 ChromeDriver 需本机安装或通过参数传入路径；详见 get_driver / render_option_to_png。
"""

import base64
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

# 包内静态目录（安装后与 charts.py 同属 fastapi_authly 包）
_STATIC_DIR = Path(__file__).resolve().parent / "static"

# 默认路径：包内仅包含 echarts.min.js；Chrome/Chromedriver 不随包分发，存在时才用
_chrome = _STATIC_DIR / "chrome-headless-shell-linux64" / "chrome-headless-shell"
_chromedriver = _STATIC_DIR / "chromedriver-linux64" / "chromedriver"
DEFAULT_CHROME_HEADLESS_PATH: Path | None = _chrome if _chrome.exists() else None
DEFAULT_CHROMEDRIVER_PATH: Path | None = _chromedriver if _chromedriver.exists() else None
DEFAULT_ECHARTS_PATH = _STATIC_DIR / "echarts.min.js"

_CHROME_MISSING_MSG = (
    "ECharts 截图需要 Chrome/Chromedriver。包内未包含（超过 PyPI 100MB 限制）。"
    "请：(1) 本机安装 Chrome 与 ChromeDriver，或 (2) 将 get_driver / render_option_to_png 的 "
    "chrome_headless_path、chromedriver_path 指向本地可执行文件。"
)

# ========== 自定义 Snapshot 脚本 ==========
SNAPSHOT_JS = """
    var ele = document.querySelector('div[_echarts_instance_]');
    var mychart = echarts.getInstanceByDom(ele);
    return mychart.getDataURL({
        type: '%s',
        pixelRatio: %s,
        excludeComponents: ['toolbox']
    });
"""

SNAPSHOT_SVG_JS = """
    var element = document.querySelector('div[_echarts_instance_] div');
    return element.innerHTML;
"""

# 内置配色（用于 build_option）
COLORS = [
    "#5470c6",
    "#91cc75",
    "#fac858",
    "#ee6666",
    "#73c0de",
    "#3ba272",
    "#fc8452",
    "#9a60b4",
    "#ea7ccc",
]


def _get_selenium():
    """延迟导入 selenium，未安装时给出明确提示。"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        return webdriver, Options, Service
    except ImportError as e:
        raise ImportError(
            "ECharts 截图依赖 selenium，请安装： pip install fastapi-authly[charts] 或 pip install selenium"
        ) from e


def get_driver(
    *,
    chrome_headless_path: str | Path | None = None,
    chromedriver_path: str | Path | None = None,
) -> Any:
    """
    创建并返回 Chrome Headless WebDriver 实例。

    Chrome 与 ChromeDriver 不随包分发（体积超 PyPI 限制），需本机安装或传入路径。
    若包内存在（本地开发时）则优先使用；否则必须传入 chrome_headless_path / chromedriver_path。
    """
    webdriver_module, Options, Service = _get_selenium()
    binary = chrome_headless_path or DEFAULT_CHROME_HEADLESS_PATH
    driver_path = chromedriver_path or DEFAULT_CHROMEDRIVER_PATH
    if binary is None or driver_path is None:
        raise FileNotFoundError(_CHROME_MISSING_MSG)
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = str(binary)
    service = Service(executable_path=str(driver_path))
    return webdriver_module.Chrome(service=service, options=options)


def engine_make_snapshot(
    html_path: str,
    file_type: str,
    *,
    pixel_ratio: int = 2,
    delay: float = 2,
    driver: Any = None,
    chrome_headless_path: str | Path | None = None,
    chromedriver_path: str | Path | None = None,
    **kwargs: Any,
) -> str:
    """
    对已存在的 HTML 文件用无头浏览器打开并执行 ECharts 截图脚本，返回 base64 或 SVG 字符串。
    """
    if delay < 0:
        raise ValueError("delay 不能为负数")
    if driver is None:
        driver = get_driver(
            chrome_headless_path=chrome_headless_path,
            chromedriver_path=chromedriver_path,
        )
    if file_type == "svg":
        snapshot_js = SNAPSHOT_SVG_JS
    else:
        snapshot_js = SNAPSHOT_JS % (file_type, pixel_ratio)
    if not html_path.startswith(("http://", "https://", "file://")):
        html_path = "file://" + os.path.abspath(html_path)
    try:
        driver.get(html_path)
        time.sleep(delay)
        return driver.execute_script(snapshot_js)
    finally:
        driver.quit()


def echarts_option_to_html(
    option: dict,
    *,
    width: int = 600,
    height: int = 400,
    title: str = "Chart",
    local_echarts_path: str | Path | None = None,
) -> str:
    """将 ECharts option 字典组装成完整 HTML 字符串。"""
    if local_echarts_path is None:
        local_echarts_path = DEFAULT_ECHARTS_PATH
    option_json = json.dumps(option, ensure_ascii=False)
    js_src = "file://" + str(Path(local_echarts_path).resolve())
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="{js_src}"></script>
</head>
<body>
  <div id="main" style="width:{width}px;height:{height}px;"></div>
  <script>
    var chartDom = document.getElementById("main");
    var myChart = echarts.init(chartDom);
    var option = {option_json};
    myChart.setOption(option);
  </script>
</body>
</html>"""
    return html


def render_option_to_png(
    option: dict,
    output_name: str = "chart.png",
    *,
    width: int = 600,
    height: int = 400,
    title: str = "Chart",
    delay: float = 2,
    pixel_ratio: int = 2,
    is_remove_html: bool = True,
    local_echarts_path: str | Path | None = None,
    chrome_headless_path: str | Path | None = None,
    chromedriver_path: str | Path | None = None,
) -> str:
    """
    将 ECharts option 字典渲染为 PNG 图片。

    不限定图表类型，任意 ECharts 支持的图均可（折线、柱状、饼、散点、地图等）。

    Args:
        option: ECharts 原生 option 字典
        output_name: 输出 PNG 路径
        width: 画布宽度（像素）
        height: 画布高度（像素）
        title: 页面标题
        delay: 打开 HTML 后等待渲染的秒数
        pixel_ratio: 导出图片像素比
        is_remove_html: 是否在完成后删除临时 HTML 文件
        local_echarts_path: ECharts JS 路径，默认使用包内 static/echarts.min.js
        chrome_headless_path: Chrome Headless 可执行文件路径，默认使用包内 static
        chromedriver_path: ChromeDriver 路径，默认使用包内 static

    Returns:
        输出文件的绝对路径
    """
    if not output_name.endswith(".png"):
        output_name = output_name.rstrip(".png") + ".png"
    if local_echarts_path is None:
        local_echarts_path = DEFAULT_ECHARTS_PATH
    html_content = echarts_option_to_html(
        option,
        width=width,
        height=height,
        title=title,
        local_echarts_path=local_echarts_path,
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(html_content)
        html_path = f.name
    try:
        raw = engine_make_snapshot(
            html_path,
            "png",
            delay=delay,
            pixel_ratio=pixel_ratio,
            chrome_headless_path=chrome_headless_path,
            chromedriver_path=chromedriver_path,
        )
        if "," in raw:
            b64 = raw.split(",", 1)[1]
        else:
            b64 = raw
        missing = len(b64) % 4
        if missing:
            b64 += "=" * (4 - missing)
        data = base64.decodebytes(b64.encode("utf-8"))
        with open(output_name, "wb") as f:
            f.write(data)
        return os.path.abspath(output_name)
    finally:
        if is_remove_html and os.path.exists(html_path):
            os.unlink(html_path)


def build_option(
    chart_type: str,
    title: str,
    data: List[Dict],
    *,
    label_key: str = "month_name",
    value_key: str = "count",
) -> dict:
    """根据类型 + 标题 + 数据构建 ECharts option（便捷封装，支持 line / bar / pie）。"""
    labels = [item[label_key] for item in data]
    values = [item[value_key] for item in data]
    data_pair = [{"name": lb, "value": val} for lb, val in zip(labels, values)]
    if chart_type == "line":
        return {
            "title": {"text": title, "left": "center"},
            "color": COLORS,
            "toolbox": {"show": True, "feature": {"saveAsImage": {"show": True}}},
            "grid": {"left": "10%", "right": "10%", "top": "18%", "bottom": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": labels},
            "yAxis": {"type": "value"},
            "series": [
                {
                    "type": "line",
                    "data": values,
                    "smooth": True,
                    "symbol": "circle",
                    "symbolSize": 8,
                    "lineStyle": {"width": 2.5},
                    "itemStyle": {"borderWidth": 2, "borderColor": "#fff"},
                    "areaStyle": {"opacity": 0.15},
                }
            ],
        }
    if chart_type == "bar":
        return {
            "title": {"text": title, "left": "center"},
            "color": COLORS,
            "toolbox": {"show": True, "feature": {"saveAsImage": {"show": True}}},
            "grid": {"left": "10%", "right": "10%", "top": "18%", "bottom": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": labels},
            "yAxis": {"type": "value"},
            "series": [
                {
                    "type": "bar",
                    "data": values,
                    "itemStyle": {"borderRadius": [6, 6, 0, 0], "borderWidth": 0},
                }
            ],
        }
    if chart_type == "pie":
        return {
            "title": {"text": title, "left": "center"},
            "color": COLORS,
            "toolbox": {"show": True, "feature": {"saveAsImage": {"show": True}}},
            "legend": {"orient": "horizontal", "bottom": "5%", "type": "scroll"},
            "series": [
                {
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "center": ["50%", "50%"],
                    "data": data_pair,
                    "itemStyle": {"borderRadius": 8, "borderWidth": 2, "borderColor": "#fff"},
                    "label": {"formatter": "{b}: {c}", "position": "outside"},
                }
            ],
        }
    raise ValueError(f"不支持的图表类型: {chart_type}，仅支持 line / bar / pie")


def render_chart_to_png(
    chart_type: str,
    title: str,
    data: List[Dict],
    output_name: str | None = None,
    *,
    label_key: str = "month_name",
    value_key: str = "count",
    width: int = 600,
    height: int = 400,
    delay: float = 2,
    pixel_ratio: int = 2,
    is_remove_html: bool = True,
    local_echarts_path: str | Path | None = None,
    chrome_headless_path: str | Path | None = None,
    chromedriver_path: str | Path | None = None,
) -> str:
    """便捷封装：先 build_option 再 render_option_to_png。"""
    option = build_option(
        chart_type,
        title,
        data,
        label_key=label_key,
        value_key=value_key,
    )
    if output_name is None:
        output_name = title + ".png"
    return render_option_to_png(
        option,
        output_name=output_name,
        width=width,
        height=height,
        title=title,
        delay=delay,
        pixel_ratio=pixel_ratio,
        is_remove_html=is_remove_html,
        local_echarts_path=local_echarts_path,
        chrome_headless_path=chrome_headless_path,
        chromedriver_path=chromedriver_path,
    )
