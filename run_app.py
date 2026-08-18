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

IS_WINDOWS = sys.platform.startswith("win")
IS_FROZEN = getattr(sys, "frozen", False)

# ---------------------------------------------------------------------------
# 日志重定向：--windowed 模式下 stdout/stderr 会被丢弃，必须写进文件才能排错
# ---------------------------------------------------------------------------
if IS_FROZEN:
    LOG_DIR = Path(sys.executable).resolve().parent
else:
    LOG_DIR = Path.cwd()
LOG_FILE = LOG_DIR / "texaco_debug.log"

_ORIG_STDOUT = sys.stdout
_ORIG_STDERR = sys.stderr


class _LogFileWrapper:
    """把输出同时写入日志文件；如果原流不可用则只写文件。"""

    def __init__(self, name: str, orig_stream):
        self.name = name
        self.orig_stream = orig_stream
        try:
            self._file = open(LOG_FILE, "a", encoding="utf-8", errors="replace")
        except Exception as exc:
            # 目录不可写时退化为只使用原流
            self._file = None
            if orig_stream is not None:
                try:
                    orig_stream.write(f"[WARN] 无法打开日志文件 {LOG_FILE}: {exc}\n")
                except Exception:
                    pass

    def write(self, s: str) -> int:
        if self._file is not None:
            try:
                self._file.write(s)
                self._file.flush()
            except Exception:
                pass
        if self.orig_stream is not None:
            try:
                return self.orig_stream.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self) -> None:
        if self._file is not None:
            try:
                self._file.flush()
            except Exception:
                pass
        if self.orig_stream is not None:
            try:
                self.orig_stream.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:
        if self.orig_stream is not None:
            try:
                return self.orig_stream.fileno()
            except Exception:
                pass
        raise OSError(f"{self.name} wrapper has no fileno")


sys.stdout = _LogFileWrapper("stdout", _ORIG_STDOUT)
sys.stderr = _LogFileWrapper("stderr", _ORIG_STDERR)


def _show_error_box(message: str) -> None:
    """在 Windows 窗体模式下弹出错误对话框，让用户直接看到致命错误。"""
    if not IS_WINDOWS:
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "TEXACO_GUI 启动失败", 0x10)
    except Exception:
        pass


def log(msg: str) -> None:
    """同时输出到 stdout（已被重定向到日志文件）和原 stderr。"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)


def log_exception(exc: BaseException) -> None:
    """记录异常信息到日志。"""
    log("----- Exception -----")
    log("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    log("---------------------")


def _global_excepthook(exc_type, exc_value, exc_tb):
    log("----- Uncaught Exception -----")
    log("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    log("------------------------------")
    if exc_value is not None and not isinstance(exc_value, SystemExit):
        _show_error_box(f"程序发生未捕获错误：\n{exc_value}")


sys.excepthook = _global_excepthook

# Python 3.8+ 线程未捕获异常也需要记录
try:

    def _threading_excepthook(args):
        log("----- Thread Exception -----")
        log(
            "".join(
                traceback.format_exception(
                    args.exc_type, args.exc_value, args.exc_traceback
                )
            )
        )
        log("----------------------------")
        if args.exc_value is not None:
            _show_error_box(f"后台线程发生错误：\n{args.exc_value}")

    threading.excepthook = _threading_excepthook
except Exception as e:
    log(f"注册 threading.excepthook 失败: {e}")


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

    if not IS_FROZEN:
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
        log(f"sys.frozen = {IS_FROZEN}")
        log(f"sys._MEIPASS = {getattr(sys, '_MEIPASS', 'N/A')}")
        log(f"sys.executable = {sys.executable}")
        log(f"当前工作目录 = {os.getcwd()}")
        log(f"日志文件 = {LOG_FILE}")

        app_path = resolve_path("app.py")

        # 检查关键文件是否存在
        for name in ["app.py", "src", "data"]:
            p = Path(resolve_path(name))
            log(f"检查资源 {name}: exists={p.exists()}, path={p}")

        # 启动浏览器线程（因为下面 headless=true 会关闭 Streamlit 自带的浏览器打开）
        url = "http://localhost:8501"
        browser_thread = threading.Thread(
            target=open_browser_when_ready,
            args=(url,),
            daemon=True,
        )
        browser_thread.start()

        # 关键：headless=true 会跳过首次运行的邮件激活提示；showEmailPrompt=false 再保险
        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--global.developmentMode=false",
            "--server.headless=true",
            "--server.showEmailPrompt=false",
            "--browser.gatherUsageStats=false",
        ]
        log(f"即将调用 streamlit.web.cli.main()，argv={sys.argv}")

        # 必须先 patch static 目录再导入 streamlit.web.cli
        _patch_streamlit_for_pyinstaller()

        import streamlit.web.cli as stcli

        return stcli.main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        log(f"启动过程中发生 SystemExit，exit code={code}")
        _show_error_box(f"启动失败（SystemExit）：\nexit code = {code}")
        return code
    except Exception as exc:
        log("启动过程中发生异常")
        log_exception(exc)
        _show_error_box(f"启动失败：\n{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
