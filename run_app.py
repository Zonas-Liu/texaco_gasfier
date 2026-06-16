#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller 入口点：启动 Streamlit 服务并自动打开浏览器。

打包命令示例（调试版）：
    pyinstaller --name TEXACO_GUI_DEBUG --onefile --console \
        --additional-hooks-dir=./hooks \
        --collect-data streamlit \
        --add-data "app.py;." \
        --add-data "src;src" \
        --add-data "data;data" \
        run_app.py

打包命令示例（发布版）：
    pyinstaller --name TEXACO_GUI --onefile --windowed \
        --additional-hooks-dir=./hooks \
        --collect-data streamlit \
        --add-data "app.py;." \
        --add-data "src;src" \
        --add-data "data;data" \
        run_app.py
"""

import os
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

# 调试日志：写入当前工作目录下的 texaco_debug.log，方便 --windowed 模式排错
LOG_FILE = Path("texaco_debug.log")


def log(msg: str) -> None:
    """同时输出到 stdout 和日志文件。"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except Exception as e:
        print(f"[WARN] 写入日志失败: {e}", flush=True)


def log_exception(exc: Exception) -> None:
    """记录异常信息到日志。"""
    log("----- Exception -----")
    log("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    log("---------------------")


def resolve_path(path: str) -> str:
    """解析 PyInstaller 临时目录或当前工作目录下的路径。"""
    base_path = getattr(sys, "_MEIPASS", os.getcwd())
    return str(Path(base_path) / path)


def open_browser_when_ready(url: str, timeout: float = 15.0):
    """后台线程：等待 Streamlit 服务就绪后打开系统默认浏览器。"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1):
                webbrowser.open(url)
                return
        except Exception:
            time.sleep(0.5)
    # 超时后仍然尝试打开一次
    webbrowser.open(url)


def _patch_streamlit_for_pyinstaller():
    """PyInstaller onefile 模式下修复 streamlit 运行环境：

    1. streamlit/file_util.py 的 get_static_dir() 在 PyInstaller 环境下会指向 PYZ
       归档内部，导致找不到真实的 static 目录，根路径返回 404。
       这里将其重定向到 sys._MEIPASS/streamlit/static。

    2. config._global_development_mode() 在 PyInstaller 环境下会检测到 __file__
       不在 site-packages 中而默认返回 True，导致不挂载 static routes。
       这里直接修改配置模板和当前配置中 global.developmentMode 的取值函数，
       确保无论后续如何深拷贝/重新解析，结果都是 False。
    """
    import streamlit.file_util as _st_file_util
    import streamlit.config as _st_config

    if not getattr(sys, "frozen", False):
        return

    # Patch 1: static 目录
    _orig_get_static_dir = _st_file_util.get_static_dir

    def _patched_get_static_dir() -> str:
        meipass = getattr(sys, "_MEIPASS", os.getcwd())
        static_dir = os.path.normpath(os.path.join(meipass, "streamlit", "static"))
        if os.path.isdir(static_dir):
            return static_dir
        return _orig_get_static_dir()

    _st_file_util.get_static_dir = _patched_get_static_dir

    # Patch 2: 强制关闭 development mode
    dev_mode_option = _st_config._config_options_template.get("global.developmentMode")
    if dev_mode_option is not None:
        dev_mode_option._get_val_func = lambda: False
    if _st_config._config_options is not None:
        dev_mode_option_live = _st_config._config_options.get("global.developmentMode")
        if dev_mode_option_live is not None:
            dev_mode_option_live._get_val_func = lambda: False

    log("已强制 global.developmentMode = false")
    log(f"验证 static_dir = {_st_file_util.get_static_dir()}")


def main() -> int:
    try:
        log("=" * 60)
        log("TEXACO_GUI 启动")
        log(f"sys.frozen = {getattr(sys, 'frozen', False)}")
        log(f"sys._MEIPASS = {getattr(sys, '_MEIPASS', 'N/A')}")
        log(f"sys.executable = {sys.executable}")
        log(f"当前工作目录 = {os.getcwd()}")

        app_path = resolve_path("app.py")

        # 检查关键文件是否存在
        for name in ["app.py", "src", "data"]:
            p = Path(resolve_path(name))
            log(f"检查资源 {name}: exists={p.exists()}, path={p}")

        # 启动浏览器线程
        url = "http://localhost:8501"
        browser_thread = threading.Thread(
            target=open_browser_when_ready,
            args=(url,),
            daemon=True,
        )
        browser_thread.start()

        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--global.developmentMode=false",
            "--server.headless=false",
        ]
        log(f"即将调用 streamlit.web.cli.main()，argv={sys.argv}")

        # 必须先 patch static 目录再导入 streamlit.web.cli
        _patch_streamlit_for_pyinstaller()

        import streamlit.web.cli as stcli
        return stcli.main()
    except Exception as exc:
        log("启动过程中发生异常")
        log_exception(exc)
        # 在 --console 模式下让用户能看到错误停留一会儿
        time.sleep(10)
        return 1


if __name__ == "__main__":
    sys.exit(main())
