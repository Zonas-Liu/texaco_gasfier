#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO 纯 HTML 方案 - Flask 后端

职责：
- 提供静态 HTML/CSS/JS 资源
- 暴露 REST API：参数读写、启动模拟、进度查询、结果解析、原始输出

运行方式：
    python web_backend/app.py
默认监听 http://127.0.0.1:5000
"""

import os
import subprocess
import sys
import threading
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

# ---------------------------------------------------------------------------
# 项目路径
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from common.result_io import read_result_text
from common.input_validation import validate_params
from common.progress import clear_progress, read_progress  # noqa: E402
from web_backend.dataparser import (  # noqa: E402
    PARAM_INFO,
    PARAM_LINES,
    calculate_wet_syngas,
    parse_datain0,
    parse_gastest,
    write_datain0,
)

DATA_FILE = ROOT / "data" / "Datain0.dat"
OUTPUT_FILE = ROOT / "GASTEST.DAT"

# ---------------------------------------------------------------------------
# Flask 应用
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder=str(ROOT / "web" / "static"),
    static_url_path="/static",
    template_folder=str(ROOT / "web"),
)
app.config["JSON_AS_ASCII"] = False

# 模拟运行状态（单进程 Flask 开发服务器下共享）
_sim_lock = threading.RLock()
_sim_state = {
    "process": None,
    "stdout_path": None,
    "stderr_path": None,
    "started_at": None,
    "completed": False,
    "returncode": None,
    "stdout": "",
    "stderr": "",
}


def _is_running() -> bool:
    with _sim_lock:
        proc = _sim_state["process"]
        if proc is None:
            return False
        if proc.poll() is None:
            return True
        return False


def _serialized_write(func):
    """检查、参数写入和启动共用一把锁（单进程服务）。"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        with _sim_lock:
            if _is_running():
                return jsonify({"error": "已有模拟任务正在运行"}), 409
            try:
                return func(*args, **kwargs)
            except (TypeError, ValueError, OverflowError) as exc:
                return jsonify({"error": str(exc)}), 400
    return wrapped


def _update_params():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError("请求体必须是 JSON 对象")
    unknown = set(payload) - set(PARAM_INFO)
    if unknown:
        raise ValueError("未知参数: " + ", ".join(sorted(unknown)))
    params = parse_datain0(DATA_FILE)
    for name, value in payload.items():
        if isinstance(value, bool):
            raise ValueError(f"{name} 必须为数值")
        params[name] = float(value)
    validate_params(params)
    for name in PARAM_INFO:
        if PARAM_INFO[name].get("type") == "int":
            params[name] = int(params[name])
    if payload:
        write_datain0(DATA_FILE, params)
    return params


def _ordered_groups():
    groups = []
    seen = set()
    for name, info in PARAM_INFO.items():
        g = info["group"]
        if g not in seen:
            seen.add(g)
            groups.append(g)
    return groups


def _grouped_params(params):
    groups = {}
    for name, info in PARAM_INFO.items():
        groups.setdefault(info["group"], []).append(name)
    return groups


# ---------------------------------------------------------------------------
# API 路由
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(str(ROOT / "web"), "index.html")


@app.route("/api/params", methods=["GET"])
def get_params():
    with _sim_lock:
        params = parse_datain0(DATA_FILE)
    return jsonify({
        "info": PARAM_INFO,
        "lines": PARAM_LINES,
        "values": params,
        "groups": _ordered_groups(),
        "grouped": _grouped_params(params),
    })


@app.route("/api/params", methods=["POST"])
@_serialized_write
def set_params():
    return jsonify({"values": _update_params()})


@app.route("/api/run", methods=["POST"])
@_serialized_write
def run_simulation():
    _update_params()
    clear_progress(ROOT / "simulation_progress.json")

    python_exe = sys.executable
    main_py = ROOT / "src" / "main.py"
    stdout_path = ROOT / ".simulation_stdout.log"
    stderr_path = ROOT / ".simulation_stderr.log"

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    with _sim_lock:
        _sim_state["stdout_path"] = stdout_path
        _sim_state["stderr_path"] = stderr_path
        _sim_state["started_at"] = time.time()
        _sim_state["completed"] = False
        _sim_state["returncode"] = None
        _sim_state["stdout"] = ""
        _sim_state["stderr"] = ""
        try:
            with open(stdout_path, "w", encoding="utf-8") as stdout_file, open(stderr_path, "w", encoding="utf-8") as stderr_file:
                _sim_state["process"] = subprocess.Popen(
                    [python_exe, str(main_py)], cwd=str(ROOT),
                    stdout=stdout_file, stderr=stderr_file, env=env,
                )
        except OSError as exc:
            _sim_state.update(process=None, completed=True, returncode=1)
            return jsonify({"error": f"无法启动模拟: {exc}"}), 500


    return jsonify({
        "status": "started",
        "pid": _sim_state["process"].pid,
        "data_file": str(DATA_FILE),
    })


@app.route("/api/progress", methods=["GET"])
def get_progress():
    progress = read_progress(ROOT / "simulation_progress.json") or {
        "iteration": 0,
        "max_iterations": 0,
        "progress": 0.0,
        "residuals": {},
        "status": "idle",
        "message": "等待运行",
    }

    with _sim_lock:
        proc = _sim_state["process"]
        if proc is None:
            progress["running"] = False
            progress["completed"] = _sim_state["completed"]
        elif proc.poll() is None:
            progress["running"] = True
            progress["completed"] = False
        else:
            progress["running"] = False
            progress["completed"] = True
            if not _sim_state["completed"]:
                _sim_state["returncode"] = proc.returncode
                try:
                    _sim_state["stdout"] = _sim_state["stdout_path"].read_text(
                        encoding="utf-8", errors="ignore"
                    )
                except Exception:
                    _sim_state["stdout"] = ""
                try:
                    _sim_state["stderr"] = _sim_state["stderr_path"].read_text(
                        encoding="utf-8", errors="ignore"
                    )
                except Exception:
                    _sim_state["stderr"] = ""
                _sim_state["completed"] = True
            progress["returncode"] = _sim_state["returncode"]
            progress["stdout"] = _sim_state["stdout"]
            progress["stderr"] = _sim_state["stderr"]

    return jsonify(progress)


@app.route("/api/results", methods=["GET"])
def get_results():
    result = parse_gastest(OUTPUT_FILE)
    if result is None:
        return jsonify({"error": "尚未生成 GASTEST.DAT"}), 404

    syngas = result.get("syngas_composition") or {}
    volume = result.get("volume_flow") or {}
    gas_prof = result.get("gas_composition_profile") or []
    if syngas and volume and gas_prof:
        wet_nms, wet_nmh, total_wet_nms, total_wet_nmh = calculate_wet_syngas(volume, gas_prof[-1])
        result["wet_syngas"] = {
            "wet_flow_nms": wet_nms,
            "wet_flow_nmh": wet_nmh,
            "total_wet_nms": total_wet_nms,
            "total_wet_nmh": total_wet_nmh,
            "h2o_frac": gas_prof[-1].get("H2O", 0.0) / 100.0,
        }
    return jsonify(result)


@app.route("/api/output", methods=["GET"])
def get_output_raw():
    if not OUTPUT_FILE.exists():
        return jsonify({"error": "尚未生成 GASTEST.DAT"}), 404
    text = read_result_text(OUTPUT_FILE)
    return jsonify({"text": text})


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
def main():
    # 确保工作目录为项目根目录，输出文件会落在正确位置
    os.chdir(str(ROOT))
    # threaded=True 为默认行为，显式写出便于阅读
    app.run(host="127.0.0.1", port=5000, threaded=True, debug=False)


if __name__ == "__main__":
    main()
