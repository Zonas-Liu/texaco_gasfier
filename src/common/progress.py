#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO 模拟进度报告工具

在 Streamlit 前端与后台计算进程之间传递迭代进度。
后台进程将进度写入 JSON 文件，前端轮询读取并更新进度条。
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, Optional

# 进度文件放在项目根目录（与 GASTEST.DAT 同级），便于前后端统一访问
DEFAULT_PROGRESS_FILE = Path("simulation_progress.json")

_progress_path: Path = DEFAULT_PROGRESS_FILE
_lock = threading.Lock()


def set_progress_file(path: os.PathLike) -> None:
    """设置进度文件路径（主要用于测试）。"""
    global _progress_path
    _progress_path = Path(path)


def get_progress_file() -> Path:
    """获取当前进度文件路径。"""
    return _progress_path


def write_progress(
    iteration: int,
    max_iterations: int,
    residuals: Optional[Dict[str, float]] = None,
    status: str = "running",
    message: str = "",
) -> None:
    """
    写入当前模拟进度到 JSON 文件。

    参数:
        iteration: 当前迭代次数
        max_iterations: 最大迭代次数
        residuals: 残差字典，例如 {"SUMFE": 1e-3, ...}
        status: 状态，可选 "running" / "completed" / "error"
        message: 额外状态信息
    """
    data = {
        "iteration": iteration,
        "max_iterations": max_iterations,
        "progress": iteration / max_iterations if max_iterations > 0 else 0.0,
        "residuals": residuals or {},
        "status": status,
        "message": message,
    }
    with _lock:
        try:
            _progress_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            # 进度写入失败不应影响主计算流程
            pass


def read_progress(path: Optional[os.PathLike] = None) -> Optional[Dict]:
    """
    读取进度文件内容。

    返回:
        进度字典；若文件不存在或读取失败则返回 None。
    """
    target = Path(path) if path is not None else _progress_path
    try:
        if not target.exists():
            return None
        text = target.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception:
        return None


def clear_progress(path: Optional[os.PathLike] = None) -> None:
    """清除进度文件。"""
    target = Path(path) if path is not None else _progress_path
    try:
        if target.exists():
            target.unlink()
    except Exception:
        pass
