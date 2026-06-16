#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO 气化炉 Streamlit 前端界面

功能：
- 编辑输入参数 (Datain0.dat)
- 运行 Python 模拟
- 可视化展示 GASTEST.DAT 输出结果

运行方式：
    .venv\\Scripts\\streamlit run app.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.resolve()
DATA_FILE = ROOT / "data" / "Datain0.dat"
OUTPUT_FILE = ROOT / "GASTEST.DAT"

# ---------------------------------------------------------------------------
# 输入参数元数据（中文说明）
# ---------------------------------------------------------------------------
PARAM_INFO = {
    # 控制与收敛
    "KTRL": {"cn": "控制参数", "unit": "", "desc": "全局控制开关", "group": "控制与收敛"},
    "ITMAX": {"cn": "最大迭代次数", "unit": "", "desc": "牛顿迭代最大步数", "group": "控制与收敛"},
    "SKONFE": {"cn": "气体组分收敛阈值", "unit": "", "desc": "SUMFE 收敛判据", "group": "控制与收敛"},
    "SKONWE": {"cn": "固体质量流收敛阈值", "unit": "", "desc": "SUMWE 收敛判据", "group": "控制与收敛"},
    "SKONX": {"cn": "碳转化率收敛阈值", "unit": "", "desc": "SUMX 收敛判据", "group": "控制与收敛"},
    "SKONT": {"cn": "温度收敛阈值", "unit": "", "desc": "SUMT 收敛判据", "group": "控制与收敛"},
    # 进料参数
    "BSLURRY": {"cn": "水煤浆浓度", "unit": "%", "desc": "煤浆中煤的质量百分比", "group": "进料参数"},
    "RATIO_COAL": {"cn": "煤浆煤质量分数", "unit": "", "desc": "干煤占水煤浆总质量的比例", "group": "进料参数"},
    "FOXY": {"cn": "氧煤比", "unit": "kg O₂/kg BSWAF", "desc": "氧气流量与煤浆流量之比", "group": "进料参数"},
    "PURE_O2": {"cn": "氧气纯度", "unit": "", "desc": "工业氧气中 O₂ 的摩尔分数", "group": "进料参数"},
    "OX_PART": {"cn": "一次氧气比例", "unit": "", "desc": "一次氧气占总氧气比例", "group": "进料参数"},
    "RATIO_CO2": {"cn": "CO₂ 比例", "unit": "", "desc": "进料 CO₂ 比例", "group": "进料参数"},
    # 状态与几何
    "PFEED_SL": {"cn": "煤浆进料压力", "unit": "Pa", "desc": "水煤浆喷嘴前压力", "group": "状态与几何"},
    "TFEED_SL": {"cn": "煤浆进料温度", "unit": "K", "desc": "水煤浆入口温度", "group": "状态与几何"},
    "PFEED_O2": {"cn": "氧气进料压力", "unit": "Pa", "desc": "氧气喷嘴前压力", "group": "状态与几何"},
    "TFEED_O2": {"cn": "氧气进料温度", "unit": "K", "desc": "氧气入口温度", "group": "状态与几何"},
    "PFEED_CO2": {"cn": "CO₂ 进料压力", "unit": "Pa", "desc": "CO₂ 喷嘴前压力", "group": "状态与几何"},
    "TFEED_CO2": {"cn": "CO₂ 进料温度", "unit": "K", "desc": "CO₂ 入口温度", "group": "状态与几何"},
    "DP": {"cn": "煤粉颗粒直径", "unit": "m", "desc": "颗粒平均直径", "group": "状态与几何"},
    # 煤质与操作
    "HU": {"cn": "煤低位热值", "unit": "kJ/kg", "desc": "收到基低位发热量", "group": "煤质与操作"},
    "XVM": {"cn": "挥发分含量", "unit": "", "desc": "煤中挥发分质量分数", "group": "煤质与操作"},
    "ELC": {"cn": "煤中 C 含量", "unit": "", "desc": "干燥无灰基碳质量分数", "group": "煤质与操作"},
    "ELH": {"cn": "煤中 H 含量", "unit": "", "desc": "干燥无灰基氢质量分数", "group": "煤质与操作"},
    "ELO": {"cn": "煤中 O 含量", "unit": "", "desc": "干燥无灰基氧质量分数", "group": "煤质与操作"},
    "ELN": {"cn": "煤中 N 含量", "unit": "", "desc": "干燥无灰基氮质量分数", "group": "煤质与操作"},
    "ELS": {"cn": "煤中 S 含量", "unit": "", "desc": "干燥无灰基硫质量分数", "group": "煤质与操作"},
    "ELAS": {"cn": "煤中灰分含量", "unit": "", "desc": "灰分质量分数", "group": "煤质与操作"},
    "ELH2O": {"cn": "煤中 H₂O 含量", "unit": "", "desc": "煤中水分质量分数", "group": "煤质与操作"},
    "TU": {"cn": "环境温度", "unit": "K", "desc": "参考环境温度", "group": "煤质与操作"},
    "TW": {"cn": "壁面温度", "unit": "K", "desc": "气化炉壁面温度", "group": "煤质与操作"},
    "PWK": {"cn": "炉膛操作压力", "unit": "Pa", "desc": "气化炉内操作压力", "group": "煤质与操作"},
    "QLOSS": {"cn": "热损失系数", "unit": "", "desc": "除壁面辐射外的附加热损失比例", "group": "煤质与操作"},
}

PARAM_LINES = [
    ("KTRL",),
    ("ITMAX", "SKONFE", "SKONWE", "SKONX", "SKONT"),
    ("BSLURRY", "RATIO_COAL"),
    ("FOXY", "PURE_O2", "OX_PART", "RATIO_CO2"),
    ("PFEED_SL", "TFEED_SL", "PFEED_O2", "TFEED_O2"),
    ("PFEED_CO2", "TFEED_CO2"),
    ("DP",),
    ("HU", "XVM"),
    ("ELC", "ELH", "ELO", "ELN", "ELS", "ELAS", "ELH2O"),
    ("TU", "TW", "PWK"),
    ("QLOSS",),
]

DEFAULT_PARAMS = {k: 0 for k in PARAM_INFO}
DEFAULT_PARAMS.update({
    "KTRL": 1, "ITMAX": 100,
    "SKONFE": 5.0e-4, "SKONWE": 5.0e-4, "SKONX": 5.0e-4, "SKONT": 5.0e-3,
    "BSLURRY": 14.0, "RATIO_COAL": 0.6,
    "FOXY": 0.98, "PURE_O2": 0.996, "OX_PART": 1.0, "RATIO_CO2": 0.0,
    "PFEED_SL": 81.0e5, "TFEED_SL": 318.15, "PFEED_O2": 81.0e5, "TFEED_O2": 293.15,
    "PFEED_CO2": 81.0e5, "TFEED_CO2": 293.15,
    "DP": 100.0e-6,
    "HU": 25900.0, "XVM": 0.28,
    "ELC": 0.6802, "ELH": 0.0404, "ELO": 0.0985, "ELN": 0.0249,
    "ELS": 0.006, "ELAS": 0.15, "ELH2O": 0.0,
    "TU": 298.15, "TW": 2200.0, "PWK": 67.0e5,
    "QLOSS": 0.03,
})

# ---------------------------------------------------------------------------
# 输出变量中文标签
# ---------------------------------------------------------------------------
OUTPUT_LABELS = {
    # 收敛历史
    "Iter": "迭代次数",
    "KONVER": "收敛标志",
    "SUMFE": "气体组分残差",
    "SUMWE": "固体质量流残差",
    "SUMX": "碳转化率残差",
    "SUMT": "温度残差",
    # 内部参数分布
    "I": "格子号",
    "H(m)": "高度 (m)",
    "U0(m/s)": "气体速度 (m/s)",
    "ResidenceTime(s)": "停留时间 (s)",
    "WE(kg/s)": "碳质量流 (kg/s)",
    "T(C)": "温度 (°C)",
    "X(%)": "碳转化率 (%)",
    # 气体成分
    "O2": "氧气 O₂",
    "CH4": "甲烷 CH₄",
    "CO": "一氧化碳 CO",
    "CO2": "二氧化碳 CO₂",
    "H2S": "硫化氢 H₂S",
    "H2": "氢气 H₂",
    "N2": "氮气 N₂",
    "H2O": "水蒸气 H₂O",
}

# 图表配色
COLOR_PALETTE = px.colors.qualitative.G10
GAS_COLORS = {
    "O2": "#E45756",
    "CH4": "#F58518",
    "CO": "#72B7B2",
    "CO2": "#54A24B",
    "H2S": "#B279A2",
    "H2": "#4C78A8",
    "N2": "#79706E",
    "H2O": "#D67195",
}


# ---------------------------------------------------------------------------
# Datain0.dat 读写
# ---------------------------------------------------------------------------
def parse_datain0(path):
    """解析 Datain0.dat，返回参数字典。"""
    params = dict(DEFAULT_PARAMS)
    if not path.exists():
        return params

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line_tuple, line in zip(PARAM_LINES, lines):
        numeric_part = line.split("/")[0].strip()
        values = [v.strip() for v in numeric_part.split(",")]
        if len(values) != len(line_tuple):
            st.warning(f"行解析长度不匹配: {line} -> 期望 {len(line_tuple)} 个值")
        for name, val_str in zip(line_tuple, values):
            params[name] = float(val_str.replace("D", "E").replace("d", "e"))
            if PARAM_INFO[name].get("type") == "int":
                params[name] = int(params[name])
    return params


def write_datain0(path, params):
    """将参数字典写回 Datain0.dat。"""
    lines = []
    for line_tuple in PARAM_LINES:
        values = [params[name] for name in line_tuple]
        line = ",".join(_format_value(v) for v in values)
        lines.append(line)

    comments = [
        "------------------------------------------------KTRL",
        "-------------------ITMAX,SKONFE,SKONWE,SKONX,SKONT",
        "---------------------------------------BSLURRY,RATIO_COAL",
        "-----------------------------FOXY,PURE_O2,OX_PART,RATIO_CO2",
        "------------PFEED_SL,TFEED_SL,PFEED_O2,TFEED_O2",
        "-------------------------------PFEED_CO2,TFEED_CO2",
        "-----------------------------------------DP",
        "-----------------------------------HU,XVM",
        "----ELC,ELH,ELO,ELN,ELS,ELAS,ELH2O",
        "------------------------TU,TW,PWK",
        "--------------------------------------------QLOSS",
    ]
    with open(path, "w", encoding="utf-8") as f:
        for line, cmt in zip(lines, comments):
            f.write(f"{line}/{cmt}\n")


def _format_value(v):
    """格式化数值为 Fortran 风格。"""
    if isinstance(v, int):
        return str(v)
    s = f"{v:.6E}"
    return s.replace("E+", "D0").replace("E-", "D-").replace("E", "D")


# ---------------------------------------------------------------------------
# GASTEST.DAT 解析
# ---------------------------------------------------------------------------
def parse_gastest(path):
    """解析 GASTEST.DAT，返回结构化结果字典。"""
    if not path.exists():
        return None

    text = path.read_text(encoding="gbk", errors="ignore")
    lines = text.splitlines()

    result = {
        "operating_conditions": {},
        "convergence_history": [],
        "internal_profile": [],
        "gas_composition_profile": [],
        "syngas_composition": {},
        "volume_flow": {},
        "outlet": {},
    }

    # 1. 运行条件
    for i, line in enumerate(lines[:20]):
        m = re.search(r"(-?\d+\.?\d*)\s*%", line)
        if m:
            result["operating_conditions"][f"param_{i}"] = float(m.group(1))
        else:
            m = re.search(r":\s*(-?\d+\.?\d*(?:[eEdD][+-]?\d+)?)", line)
            if m:
                result["operating_conditions"][f"param_{i}"] = _parse_float(m.group(1))

    # 2. 收敛历史
    in_history = False
    for line in lines:
        if "Iter" in line and "KONVER" in line:
            in_history = True
            continue
        if in_history:
            parts = line.split()
            if len(parts) >= 6 and parts[0].isdigit():
                result["convergence_history"].append({
                    "Iter": int(parts[0]),
                    "KONVER": int(parts[1]),
                    "SUMFE": _parse_float(parts[2]),
                    "SUMWE": _parse_float(parts[3]),
                    "SUMX": _parse_float(parts[4]),
                    "SUMT": _parse_float(parts[5]),
                })
            elif "Converged" in line or "收敛" in line or "MAX" in line or line.strip().startswith("="):
                in_history = False

    # 3. 连续数字表格识别（7 列内部参数 / 9 列气体成分）
    table_blocks = []
    current_block = []
    for line in lines:
        parts = line.split()
        if len(parts) in (7, 9) and parts[0].isdigit():
            current_block.append((len(parts), parts))
        else:
            if current_block:
                table_blocks.append(current_block)
                current_block = []
    if current_block:
        table_blocks.append(current_block)

    for block in table_blocks:
        ncols = block[0][0]
        if ncols == 7 and len(block) > len(result["internal_profile"]):
            result["internal_profile"] = [
                {
                    "I": int(parts[0]),
                    "H(m)": _parse_float(parts[1]),
                    "U0(m/s)": _parse_float(parts[2]),
                    "ResidenceTime(s)": _parse_float(parts[3]),
                    "WE(kg/s)": _parse_float(parts[4]),
                    "T(C)": _parse_float(parts[5]),
                    "X(%)": _parse_float(parts[6]),
                }
                for _, parts in block
            ]
        elif ncols == 9 and len(block) > len(result["gas_composition_profile"]):
            result["gas_composition_profile"] = [
                {
                    "I": int(parts[0]),
                    "O2": _parse_float(parts[1]),
                    "CH4": _parse_float(parts[2]),
                    "CO": _parse_float(parts[3]),
                    "CO2": _parse_float(parts[4]),
                    "H2S": _parse_float(parts[5]),
                    "H2": _parse_float(parts[6]),
                    "N2": _parse_float(parts[7]),
                    "H2O": _parse_float(parts[8]),
                }
                for _, parts in block
            ]

    # 4. 合成气成分和体积流量
    keys = ["O2", "CH4", "CO", "CO2", "H2S", "H2", "N2"]
    found_gas_table_end = False
    for line in lines:
        if line.strip().startswith("I") and "O2" in line and "H2O" in line:
            found_gas_table_end = True
            continue
        if not found_gas_table_end:
            continue
        parts = line.split()
        if len(parts) >= 8 and not parts[0].isdigit() and _is_number(parts[1]):
            vals = [_parse_float(v) for v in parts[1:8]]
            if all(v >= 0 for v in vals):
                if not result["syngas_composition"]:
                    result["syngas_composition"] = dict(zip(keys, vals))
                elif not result["volume_flow"]:
                    result["volume_flow"] = dict(zip(keys, vals))

    # 5. 出口温度和碳转化率
    for line in lines[-5:]:
        m = re.search(r"(\d+\.\d+)\s*C", line)
        if m:
            val = _parse_float(m.group(1))
            if val > 100:
                result["outlet"]["Temperature(C)"] = val
        nums = re.findall(r"\d+\.\d+", line)
        for n in nums:
            val = _parse_float(n)
            if 0 <= val <= 1.5:
                result["outlet"]["CarbonConversion"] = val

    result["operating_conditions"] = dict(list(result["operating_conditions"].items())[:10])
    return result


def _parse_float(s):
    try:
        return float(s.replace("D", "E").replace("d", "e"))
    except ValueError:
        return 0.0


def _is_number(s):
    try:
        float(s.replace("D", "E").replace("d", "e"))
        return True
    except ValueError:
        return False


def calculate_wet_syngas(dry_flow, gas_profile_last):
    """
    根据干合成气体积流量和第30个cell的湿基气体组成，计算湿合成气组成。

    原理：
    - 非水组分的湿基流量等于干基流量（水蒸气的加入不改变其他组分的量）
    - 湿基总流量 = 干基总流量 / (1 - y_H2O)
    - H2O 湿基流量 = 干基总流量 * y_H2O / (1 - y_H2O)

    参数：
        dry_flow: dict, 干基体积流量 (Nm³/s)
        gas_profile_last: dict, 最后一个格子（出口）的湿基气体体积分数 (%)

    返回：
        wet_flow_nms: dict, 湿基体积流量 (Nm³/s)
        wet_flow_nmh: dict, 湿基体积流量 (Nm³/h)
        total_wet_nms: float, 湿基总体积流量 (Nm³/s)
        total_wet_nmh: float, 湿基总体积流量 (Nm³/h)
    """
    total_dry = sum(dry_flow.values())
    h2o_frac = gas_profile_last.get("H2O", 0.0) / 100.0

    if h2o_frac <= 0.0 or h2o_frac >= 1.0:
        # 无水分数据或数据异常，退化为干气
        wet_flow_nms = dict(dry_flow)
        wet_flow_nms["H2O"] = 0.0
        wet_flow_nmh = {k: v * 3600.0 for k, v in wet_flow_nms.items()}
        return wet_flow_nms, wet_flow_nmh, total_dry, total_dry * 3600.0

    total_wet_nms = total_dry / (1.0 - h2o_frac)
    h2o_flow_nms = total_dry * h2o_frac / (1.0 - h2o_frac)

    wet_flow_nms = {}
    for k, v in dry_flow.items():
        wet_flow_nms[k] = v  # 非水组分湿基流量 = 干基流量
    wet_flow_nms["H2O"] = h2o_flow_nms

    wet_flow_nmh = {k: v * 3600.0 for k, v in wet_flow_nms.items()}
    return wet_flow_nms, wet_flow_nmh, total_wet_nms, total_wet_nms * 3600.0


# ---------------------------------------------------------------------------
# 运行模拟
# ---------------------------------------------------------------------------
class _MockProcess:
    """用于模拟 subprocess.CompletedProcess 的简单容器。"""
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _run_simulation_direct():
    """在 PyInstaller 打包环境中直接调用 src.main.main()。"""
    import io

    src_path = str(ROOT / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # 确保工作目录为项目根目录，以便生成 GASTEST.DAT 等文件
    original_cwd = os.getcwd()
    os.chdir(str(ROOT))

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr

    try:
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        from src.main import main as texaco_main
        texaco_main()
        return _MockProcess(0, stdout_capture.getvalue(), stderr_capture.getvalue())
    except Exception as exc:
        stderr_capture.write(f"\n{exc.__class__.__name__}: {exc}\n")
        import traceback
        stderr_capture.write(traceback.format_exc())
        return _MockProcess(1, stdout_capture.getvalue(), stderr_capture.getvalue())
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        os.chdir(original_cwd)


def run_simulation():
    """调用 src/main.py 运行模拟。"""
    # PyInstaller 打包后 sys.executable 指向 exe 自身，无法再用子进程调用 Python
    if getattr(sys, "frozen", False):
        return _run_simulation_direct()

    python_exe = sys.executable
    main_py = ROOT / "src" / "main.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.run(
        [python_exe, str(main_py)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        env=env,
    )
    return process


# ---------------------------------------------------------------------------
# 美化辅助函数
# ---------------------------------------------------------------------------
def rename_columns(df, labels):
    """将 DataFrame 列名替换为中文标签。"""
    return df.rename(columns={k: labels.get(k, k) for k in df.columns})


def style_dataframe(df, precision=4):
    """对 DataFrame 进行简单样式美化。"""
    fmt = {col: f"{{:.{precision}f}}" for col in df.select_dtypes(include="number").columns}
    return df.style.format(fmt).set_properties(**{
        "text-align": "center",
        "font-size": "14px"
    }).set_table_styles([
        {"selector": "th", "props": [("text-align", "center"), ("font-weight", "bold"), ("background-color", "#f0f2f6")]}
    ])


def plot_line(df, x, y_list, title, y_title, color_map=None):
    """使用 Plotly 绘制交互式折线图。"""
    fig = go.Figure()
    for y in y_list:
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines+markers",
            name=OUTPUT_LABELS.get(y, y),
            line=dict(width=2.5),
            marker=dict(size=6),
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        xaxis_title=OUTPUT_LABELS.get(x, x),
        yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=60, r=40, t=80, b=60),
    )
    if color_map:
        for trace in fig.data:
            key = next((k for k in color_map if OUTPUT_LABELS.get(k, k) == trace.name), None)
            if key:
                trace.line.color = color_map[key]
                trace.marker.color = color_map[key]
    return fig


def plot_bar(data_dict, title, y_title):
    """使用 Plotly 绘制柱状图。"""
    labels = [OUTPUT_LABELS.get(k, k) for k in data_dict.keys()]
    values = list(data_dict.values())
    colors = [GAS_COLORS.get(k, COLOR_PALETTE[i % len(COLOR_PALETTE)]) for i, k in enumerate(data_dict.keys())]

    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[f"{v:.4f}" for v in values],
        textposition="outside",
    )])
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        xaxis_title="组分",
        yaxis_title=y_title,
        template="plotly_white",
        margin=dict(l=60, r=40, t=80, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# Streamlit 页面
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="TEXACO 气化炉模拟", layout="wide", initial_sidebar_state="expanded")

    # 页面标题与说明
    st.markdown("""
    <h1 style='text-align: center; color: #1f77b4;'>🔥 TEXACO 气化炉 CFD 模拟平台</h1>
    <p style='text-align: center; color: #666; font-size: 16px;'>
        交互式编辑输入参数、运行模拟并可视化 GASTEST.DAT 输出结果
    </p>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 侧边栏：输入参数
    # -----------------------------------------------------------------------
    st.sidebar.header("⚙️ 输入参数编辑")
    st.sidebar.markdown("修改 `data/Datain0.dat` 中的运行参数，点击保存或运行。")

    params = parse_datain0(DATA_FILE)

    # 按分组渲染输入控件
    groups = {}
    for name, info in PARAM_INFO.items():
        groups.setdefault(info["group"], []).append(name)

    for group_name, names in groups.items():
        with st.sidebar.expander(f"📁 {group_name}", expanded=(group_name == "进料参数")):
            for name in names:
                info = PARAM_INFO[name]
                label = f"{info['cn']} ({name})"
                val = params[name]

                # 根据数值范围决定输入控件
                if info["unit"] == "":
                    help_text = info["desc"]
                else:
                    help_text = f"{info['desc']}，单位：{info['unit']}"

                if isinstance(val, int):
                    params[name] = st.number_input(
                        label,
                        value=int(val),
                        step=1,
                        help=help_text,
                        key=f"input_{name}",
                    )
                else:
                    # 对 0-1 之间的参数使用更精细的步长
                    step = 0.001 if 0 <= val <= 1 else (0.01 if abs(val) < 100 else 1.0)
                    format_str = "%.6f" if abs(val) < 1 else "%.2f"
                    params[name] = st.number_input(
                        label,
                        value=float(val),
                        step=float(step),
                        format=format_str,
                        help=help_text,
                        key=f"input_{name}",
                    )

    col1, col2 = st.sidebar.columns(2)
    save_clicked = col1.button("💾 保存输入", use_container_width=True)
    run_clicked = col2.button("🚀 运行模拟", use_container_width=True, type="primary")

    if save_clicked:
        write_datain0(DATA_FILE, params)
        st.sidebar.success("✅ 输入参数已保存到 data/Datain0.dat")

    # -----------------------------------------------------------------------
    # 主区域：运行模拟
    # -----------------------------------------------------------------------
    if run_clicked:
        write_datain0(DATA_FILE, params)
        with st.spinner("正在运行 TEXACO 模拟，请稍候..."):
            process = run_simulation()
        if process.returncode != 0:
            st.error("❌ 模拟运行失败")
            st.code(process.stderr or process.stdout)
            return
        else:
            st.success("✅ 模拟运行完成")
            if process.stdout:
                with st.expander("🖥️ 控制台输出"):
                    st.code(process.stdout)

    # -----------------------------------------------------------------------
    # 主区域：结果展示
    # -----------------------------------------------------------------------
    result = parse_gastest(OUTPUT_FILE)
    if result is None:
        st.info("📭 尚未生成 `GASTEST.DAT`，请在侧边栏点击「运行模拟」。")
        return

    # 结果摘要卡片
    outlet = result.get("outlet", {})
    hist = result.get("convergence_history", [])
    last_iter = hist[-1]["Iter"] if hist else 0
    converged = "✅ 已收敛" if hist and hist[-1].get("KONVER") == 0 else "⚠️ 未收敛"

    st.markdown("---")
    st.header("📊 模拟结果摘要")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("出口温度", f"{outlet.get('Temperature(C)', 0):.2f} °C")
    c2.metric("碳转化率", f"{outlet.get('CarbonConversion', 0) * 100:.2f}%")
    c3.metric("收敛迭代", f"{last_iter} 次")
    c4.metric("收敛状态", converged)

    # 结果详情页签
    tab1, tab2, tab3, tab4 = st.tabs(["📈 收敛历史", "🧪 合成气成分", "🏭 沿炉膛分布", "📝 原始输出"])

    # -----------------------------------------------------------------------
    # Tab 1: 收敛历史
    # -----------------------------------------------------------------------
    with tab1:
        if hist:
            df_hist = pd.DataFrame(hist)
            df_hist_cn = rename_columns(df_hist, OUTPUT_LABELS)

            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown("#### 收敛历史数据")
                st.dataframe(
                    style_dataframe(df_hist_cn, precision=4),
                    use_container_width=True,
                    height=500,
                )
            with col_b:
                st.markdown("#### 残差收敛曲线")
                fig = plot_line(
                    df_hist, "Iter",
                    ["SUMFE", "SUMWE", "SUMX"],
                    "气体组分 / 固体质量流 / 碳转化率 残差收敛曲线",
                    "残差 (log 尺度)",
                )
                fig.update_yaxes(type="log")
                st.plotly_chart(fig, use_container_width=True)

                fig2 = plot_line(
                    df_hist, "Iter",
                    ["SUMT"],
                    "温度残差收敛曲线",
                    "温度残差",
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("未解析到收敛历史")

    # -----------------------------------------------------------------------
    # Tab 2: 合成气成分
    # -----------------------------------------------------------------------
    with tab2:
        syngas = result.get("syngas_composition", {})
        volume = result.get("volume_flow", {})
        gas_prof = result.get("gas_composition_profile", [])

        if syngas:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### 干煤气成分")
                df_syn = pd.DataFrame([syngas])
                df_syn_cn = rename_columns(df_syn, OUTPUT_LABELS)
                st.dataframe(style_dataframe(df_syn_cn, precision=4), use_container_width=True)
                fig = plot_bar(syngas, "干煤气成分占比", "体积百分比 (%)")
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                st.markdown("#### 干基体积流量")
                df_vol = pd.DataFrame([volume])
                df_vol_cn = rename_columns(df_vol, OUTPUT_LABELS)
                st.dataframe(style_dataframe(df_vol_cn, precision=4), use_container_width=True)
                fig2 = plot_bar(volume, "各组分干基体积流量", "流量 (Nm³/s)")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("未解析到合成气成分")

        # 湿合成气组成计算
        if gas_prof and volume:
            gas_last = gas_prof[-1]  # 第30个cell的湿基气体组成
            wet_nms, wet_nmh, total_wet_nms, total_wet_nmh = calculate_wet_syngas(volume, gas_last)

            st.markdown("---")
            st.markdown("#### 💧 湿合成气组成（含 H₂O）")
            st.markdown(
                f"基于第 **30** 个格子湿基气体组成（H₂O = **{gas_last.get('H2O', 0):.3f}%**）换算，"
                f"湿基总流量 = **{total_wet_nmh:.1f} Nm³/h**（{total_wet_nms:.4f} Nm³/s）"
            )

            wet_df = pd.DataFrame({
                "组分": [OUTPUT_LABELS.get(k, k) for k in wet_nmh.keys()],
                "湿基流量 (Nm³/s)": list(wet_nms.values()),
                "湿基流量 (Nm³/h)": list(wet_nmh.values()),
                "湿基体积分数 (%)": [v / total_wet_nms * 100.0 if total_wet_nms > 0 else 0.0 for v in wet_nms.values()],
            })

            col_c, col_d = st.columns([3, 2])
            with col_c:
                st.dataframe(
                    wet_df.style.format({
                        "湿基流量 (Nm³/s)": "{:.4f}",
                        "湿基流量 (Nm³/h)": "{:.2f}",
                        "湿基体积分数 (%)": "{:.3f}",
                    }).set_properties(**{"text-align": "center"}).set_table_styles([
                        {"selector": "th", "props": [("text-align", "center"), ("font-weight", "bold"), ("background-color", "#f0f2f6")]}
                    ]),
                    use_container_width=True,
                    height=340,
                )
            with col_d:
                fig_wet = plot_bar(wet_nmh, "湿合成气各组分流量", "流量 (Nm³/h)")
                st.plotly_chart(fig_wet, use_container_width=True)
        else:
            st.info("缺少第30个格子的气体分布数据，无法计算湿合成气组成。")

    # -----------------------------------------------------------------------
    # Tab 3: 沿炉膛分布
    # -----------------------------------------------------------------------
    with tab3:
        internal = result.get("internal_profile", [])
        gas_prof = result.get("gas_composition_profile", [])

        if internal:
            df_internal = pd.DataFrame(internal)
            df_internal_cn = rename_columns(df_internal, OUTPUT_LABELS)

            st.markdown("#### 内部参数分布")
            st.dataframe(style_dataframe(df_internal_cn, precision=3), use_container_width=True, height=380)

            col_c, col_d = st.columns(2)
            with col_c:
                fig_temp = plot_line(
                    df_internal, "I",
                    ["T(C)"],
                    "沿炉膛温度分布",
                    "温度 (°C)",
                )
                st.plotly_chart(fig_temp, use_container_width=True)

                fig_we = plot_line(
                    df_internal, "I",
                    ["WE(kg/s)"],
                    "沿炉膛碳质量流分布",
                    "碳质量流 (kg/s)",
                )
                st.plotly_chart(fig_we, use_container_width=True)

            with col_d:
                fig_x = plot_line(
                    df_internal, "I",
                    ["X(%)"],
                    "沿炉膛碳转化率分布",
                    "碳转化率 (%)",
                )
                st.plotly_chart(fig_x, use_container_width=True)

                fig_u0 = plot_line(
                    df_internal, "I",
                    ["U0(m/s)"],
                    "沿炉膛气体速度分布",
                    "气体速度 (m/s)",
                )
                st.plotly_chart(fig_u0, use_container_width=True)

            st.markdown("#### 气体成分分布")
            if gas_prof:
                df_gas = pd.DataFrame(gas_prof)
                df_gas_cn = rename_columns(df_gas, OUTPUT_LABELS)
                st.dataframe(style_dataframe(df_gas_cn, precision=3), use_container_width=True, height=380)

                col_e, col_f = st.columns(2)
                with col_e:
                    fig_main = plot_line(
                        df_gas, "I",
                        ["CO", "CO2", "H2", "CH4"],
                        "主要可燃/含碳组分沿炉膛分布",
                        "体积百分比 (%)",
                        color_map=GAS_COLORS,
                    )
                    st.plotly_chart(fig_main, use_container_width=True)
                with col_f:
                    fig_other = plot_line(
                        df_gas, "I",
                        ["O2", "H2O", "N2", "H2S"],
                        "其他组分沿炉膛分布",
                        "体积百分比 (%)",
                        color_map=GAS_COLORS,
                    )
                    st.plotly_chart(fig_other, use_container_width=True)
        else:
            st.warning("未解析到沿炉膛分布数据")

    # -----------------------------------------------------------------------
    # Tab 4: 原始输出
    # -----------------------------------------------------------------------
    with tab4:
        if OUTPUT_FILE.exists():
            st.markdown("#### GASTEST.DAT 原始文本")
            st.text(OUTPUT_FILE.read_text(encoding="gbk", errors="ignore"))


if __name__ == "__main__":
    main()
