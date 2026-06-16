#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO 气化炉 Streamlit 前端界面

功能：
- 编辑输入参数 (Datain0.dat)
- 运行 Python 模拟
- 展示 GASTEST.DAT 输出结果

运行方式：
    .venv\\Scripts\\streamlit run app.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.resolve()
DATA_FILE = ROOT / "data" / "Datain0.dat"
OUTPUT_FILE = ROOT / "GASTEST.DAT"

# ---------------------------------------------------------------------------
# Datain0.dat 读写
# ---------------------------------------------------------------------------
DEFAULT_PARAMS = {
    "KTRL": {"value": 1, "type": "int", "desc": "控制参数"},
    "ITMAX": {"value": 100, "type": "int", "desc": "最大迭代次数"},
    "SKONFE": {"value": 5.0e-4, "type": "float", "desc": "气体组分收敛阈值"},
    "SKONWE": {"value": 5.0e-4, "type": "float", "desc": "固体质量流收敛阈值"},
    "SKONX": {"value": 5.0e-4, "type": "float", "desc": "碳转化率收敛阈值"},
    "SKONT": {"value": 5.0e-3, "type": "float", "desc": "温度收敛阈值"},
    "BSLURRY": {"value": 14.0, "type": "float", "desc": "煤浆浓度 (%煤)"},
    "RATIO_COAL": {"value": 0.6, "type": "float", "desc": "煤浆中煤的质量分数"},
    "FOXY": {"value": 0.98, "type": "float", "desc": "氧煤比 (kg O2/kg BSWAF)"},
    "PURE_O2": {"value": 0.996, "type": "float", "desc": "氧气纯度"},
    "OX_PART": {"value": 1.0, "type": "float", "desc": "一次氧气比例"},
    "RATIO_CO2": {"value": 0.0, "type": "float", "desc": "CO2 比例"},
    "PFEED_SL": {"value": 81.0e5, "type": "float", "desc": "煤浆压力 (Pa)"},
    "TFEED_SL": {"value": 318.15, "type": "float", "desc": "煤浆温度 (K)"},
    "PFEED_O2": {"value": 81.0e5, "type": "float", "desc": "氧气压力 (Pa)"},
    "TFEED_O2": {"value": 293.15, "type": "float", "desc": "氧气温度 (K)"},
    "PFEED_CO2": {"value": 81.0e5, "type": "float", "desc": "CO2 压力 (Pa)"},
    "TFEED_CO2": {"value": 293.15, "type": "float", "desc": "CO2 温度 (K)"},
    "DP": {"value": 100.0e-6, "type": "float", "desc": "颗粒直径 (m)"},
    "HU": {"value": 25900.0, "type": "float", "desc": "煤热值 (kJ/kg)"},
    "XVM": {"value": 0.28, "type": "float", "desc": "挥发分含量"},
    "ELC": {"value": 0.6802, "type": "float", "desc": "煤中 C 质量分数"},
    "ELH": {"value": 0.0404, "type": "float", "desc": "煤中 H 质量分数"},
    "ELO": {"value": 0.0985, "type": "float", "desc": "煤中 O 质量分数"},
    "ELN": {"value": 0.0249, "type": "float", "desc": "煤中 N 质量分数"},
    "ELS": {"value": 0.006, "type": "float", "desc": "煤中 S 质量分数"},
    "ELAS": {"value": 0.15, "type": "float", "desc": "煤中灰分质量分数"},
    "ELH2O": {"value": 0.0, "type": "float", "desc": "煤中 H2O 质量分数"},
    "TU": {"value": 298.15, "type": "float", "desc": "环境温度 (K)"},
    "TW": {"value": 2200.0, "type": "float", "desc": "壁面温度 (K)"},
    "PWK": {"value": 67.0e5, "type": "float", "desc": "操作压力 (Pa)"},
    "QLOSS": {"value": 0.03, "type": "float", "desc": "热损失系数"},
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


def parse_datain0(path):
    """解析 Datain0.dat，返回参数字典。"""
    params = {}
    if not path.exists():
        return {k: v["value"] for k, v in DEFAULT_PARAMS.items()}

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line_tuple, line in zip(PARAM_LINES, lines):
        # 去掉注释部分，只保留斜杠前的数值
        numeric_part = line.split("/")[0].strip()
        values = [v.strip() for v in numeric_part.split(",")]
        if len(values) != len(line_tuple):
            st.warning(f"行解析长度不匹配: {line} -> 期望 {len(line_tuple)} 个值")
        for name, val_str in zip(line_tuple, values):
            typ = DEFAULT_PARAMS[name]["type"]
            val = float(val_str.replace("D", "E").replace("d", "e"))
            params[name] = int(val) if typ == "int" else val
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
    # 使用 E 指数格式，避免 Python 默认的 e+xx 被 Fortran 误解
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

    # 1. 运行条件：前 20 行中提取带 % 或冒号后的数值
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

    # 3. 识别连续的数字表格行
    # 表格1：7 列（内部参数），表格2：9 列（气体成分）
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

    # 取最长的 7 列表格作为内部参数，最长的 9 列表格作为气体成分
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

    # 4. 合成气成分和体积流量：在气体成分表之后，寻找 8 列数据行
    keys = ["O2", "CH4", "CO", "CO2", "H2S", "H2", "N2"]
    found_gas_table_end = False
    for i, line in enumerate(lines):
        # 气体成分表头
        if line.strip().startswith("I") and "O2" in line and "H2O" in line:
            found_gas_table_end = True
            continue
        if not found_gas_table_end:
            continue
        parts = line.split()
        # 跳过表格数据行（第一列为整数）和表头行（第二列不是数字）
        if (len(parts) >= 8 and not parts[0].isdigit() and
                _is_number(parts[1])):
            vals = [_parse_float(v) for v in parts[1:8]]
            if all(v >= 0 for v in vals):
                if not result["syngas_composition"]:
                    result["syngas_composition"] = dict(zip(keys, vals))
                elif not result["volume_flow"]:
                    result["volume_flow"] = dict(zip(keys, vals))

    # 5. 出口温度和碳转化率：文件最后几行
    for line in lines[-5:]:
        # 温度形如 "1315.072 C"
        m = re.search(r"(\d+\.\d+)\s*C", line)
        if m:
            val = _parse_float(m.group(1))
            if val > 100:  # 排除室温等较小值
                result["outlet"]["Temperature(C)"] = val
        # 碳转化率：查找 0-1 之间的数字
        nums = re.findall(r"\d+\.\d+", line)
        for n in nums:
            val = _parse_float(n)
            if 0 <= val <= 1.5:
                result["outlet"]["CarbonConversion"] = val

    # 简化运行条件
    result["operating_conditions"] = dict(list(result["operating_conditions"].items())[:10])

    return result

def _parse_float(s):
    """安全解析浮点数。"""
    try:
        return float(s.replace("D", "E").replace("d", "e"))
    except ValueError:
        return 0.0


def _is_number(s):
    """判断字符串是否为数值。"""
    try:
        float(s.replace("D", "E").replace("d", "e"))
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# 运行模拟
# ---------------------------------------------------------------------------
def run_simulation():
    """调用 src/main.py 运行模拟。"""
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
# Streamlit 页面
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="TEXACO 气化炉模拟", layout="wide")
    st.title("🔥 TEXACO 气化炉 CFD 模拟前端")

    # -----------------------------------------------------------------------
    # 侧边栏：输入参数
    # -----------------------------------------------------------------------
    st.sidebar.header("⚙️ 输入参数")
    st.sidebar.markdown("编辑 `data/Datain0.dat` 并运行模拟")

    params = parse_datain0(DATA_FILE)

    # 分组展示
    with st.sidebar.expander("控制与收敛", expanded=True):
        params["KTRL"] = st.number_input("KTRL", value=params["KTRL"], step=1)
        params["ITMAX"] = st.number_input("ITMAX", value=params["ITMAX"], step=1)
        params["SKONFE"] = st.number_input("SKONFE", value=params["SKONFE"], format="%.2e")
        params["SKONWE"] = st.number_input("SKONWE", value=params["SKONWE"], format="%.2e")
        params["SKONX"] = st.number_input("SKONX", value=params["SKONX"], format="%.2e")
        params["SKONT"] = st.number_input("SKONT", value=params["SKONT"], format="%.2e")

    with st.sidebar.expander("进料参数", expanded=True):
        params["BSLURRY"] = st.number_input("BSLURRY (%)", value=params["BSLURRY"])
        params["RATIO_COAL"] = st.number_input("RATIO_COAL", value=params["RATIO_COAL"], min_value=0.0, max_value=1.0)
        params["FOXY"] = st.number_input("FOXY (kg O2/kg BSWAF)", value=params["FOXY"])
        params["PURE_O2"] = st.number_input("PURE_O2", value=params["PURE_O2"], min_value=0.0, max_value=1.0)
        params["OX_PART"] = st.number_input("OX_PART", value=params["OX_PART"], min_value=0.0, max_value=1.0)
        params["RATIO_CO2"] = st.number_input("RATIO_CO2", value=params["RATIO_CO2"], min_value=0.0, max_value=1.0)

    with st.sidebar.expander("状态与几何", expanded=True):
        params["PFEED_SL"] = st.number_input("PFEED_SL (Pa)", value=params["PFEED_SL"], format="%.2e")
        params["TFEED_SL"] = st.number_input("TFEED_SL (K)", value=params["TFEED_SL"])
        params["PFEED_O2"] = st.number_input("PFEED_O2 (Pa)", value=params["PFEED_O2"], format="%.2e")
        params["TFEED_O2"] = st.number_input("TFEED_O2 (K)", value=params["TFEED_O2"])
        params["PFEED_CO2"] = st.number_input("PFEED_CO2 (Pa)", value=params["PFEED_CO2"], format="%.2e")
        params["TFEED_CO2"] = st.number_input("TFEED_CO2 (K)", value=params["TFEED_CO2"])
        params["DP"] = st.number_input("DP (m)", value=params["DP"], format="%.2e")

    with st.sidebar.expander("煤质与操作", expanded=True):
        params["HU"] = st.number_input("HU (kJ/kg)", value=params["HU"])
        params["XVM"] = st.number_input("XVM", value=params["XVM"], min_value=0.0, max_value=1.0)
        params["ELC"] = st.number_input("ELC", value=params["ELC"], min_value=0.0, max_value=1.0)
        params["ELH"] = st.number_input("ELH", value=params["ELH"], min_value=0.0, max_value=1.0)
        params["ELO"] = st.number_input("ELO", value=params["ELO"], min_value=0.0, max_value=1.0)
        params["ELN"] = st.number_input("ELN", value=params["ELN"], min_value=0.0, max_value=1.0)
        params["ELS"] = st.number_input("ELS", value=params["ELS"], min_value=0.0, max_value=1.0)
        params["ELAS"] = st.number_input("ELAS", value=params["ELAS"], min_value=0.0, max_value=1.0)
        params["ELH2O"] = st.number_input("ELH2O", value=params["ELH2O"], min_value=0.0, max_value=1.0)
        params["TU"] = st.number_input("TU (K)", value=params["TU"])
        params["TW"] = st.number_input("TW (K)", value=params["TW"])
        params["PWK"] = st.number_input("PWK (Pa)", value=params["PWK"], format="%.2e")
        params["QLOSS"] = st.number_input("QLOSS", value=params["QLOSS"], min_value=0.0, max_value=1.0)

    col1, col2 = st.sidebar.columns(2)
    save_clicked = col1.button("💾 保存输入")
    run_clicked = col2.button("🚀 运行模拟")

    if save_clicked:
        write_datain0(DATA_FILE, params)
        st.sidebar.success("输入参数已保存")

    # -----------------------------------------------------------------------
    # 主区域
    # -----------------------------------------------------------------------
    if run_clicked:
        write_datain0(DATA_FILE, params)
        with st.spinner("正在运行 TEXACO 模拟，请稍候..."):
            process = run_simulation()
        if process.returncode != 0:
            st.error("运行失败")
            st.code(process.stderr or process.stdout)
        else:
            st.success("模拟运行完成")
            if process.stdout:
                with st.expander("控制台输出"):
                    st.code(process.stdout)

    # 展示结果
    result = parse_gastest(OUTPUT_FILE)
    if result is None:
        st.info("尚未生成 `GASTEST.DAT`，请点击侧边栏的「运行模拟」。")
        return

    # -----------------------------------------------------------------------
    # 结果摘要卡片
    # -----------------------------------------------------------------------
    st.header("📊 模拟结果摘要")

    outlet = result.get("outlet", {})
    syngas = result.get("syngas_composition", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("出口温度", f"{outlet.get('Temperature(C)', 0):.2f} °C")
    c2.metric("碳转化率", f"{outlet.get('CarbonConversion', 0):.4f}")
    c3.metric("收敛迭代", len(result.get("convergence_history", [])))

    # -----------------------------------------------------------------------
    # 收敛历史
    # -----------------------------------------------------------------------
    st.subheader("📈 收敛历史")
    hist = result.get("convergence_history", [])
    if hist:
        df_hist = pd.DataFrame(hist)
        tab1, tab2 = st.tabs(["表格", "曲线"])
        with tab1:
            st.dataframe(df_hist, use_container_width=True)
        with tab2:
            st.line_chart(df_hist.set_index("Iter")[["SUMFE", "SUMWE", "SUMX"]])
            st.line_chart(df_hist.set_index("Iter")[["SUMT"]])
    else:
        st.warning("未解析到收敛历史")

    # -----------------------------------------------------------------------
    # 合成气成分
    # -----------------------------------------------------------------------
    st.subheader("🧪 合成气成分")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**干气成分 (%)**")
        df_syngas = pd.DataFrame([syngas])
        st.dataframe(df_syngas, use_container_width=True)
    with col_g2:
        st.markdown("**体积流量 (Nm³/s)**")
        df_vol = pd.DataFrame([result.get("volume_flow", {})])
        st.dataframe(df_vol, use_container_width=True)

    if syngas:
        st.bar_chart(pd.Series(syngas), use_container_width=True)

    # -----------------------------------------------------------------------
    # 沿炉膛分布
    # -----------------------------------------------------------------------
    st.subheader("🏭 沿炉膛分布")

    internal = result.get("internal_profile", [])
    gas_prof = result.get("gas_composition_profile", [])

    if internal:
        df_internal = pd.DataFrame(internal)
        tab3, tab4 = st.tabs(["内部参数", "气体成分"])
        with tab3:
            st.dataframe(df_internal, use_container_width=True)
            st.line_chart(df_internal.set_index("I")[["T(C)", "U0(m/s)", "X(%)"]])
            st.line_chart(df_internal.set_index("I")[["WE(kg/s)"]])
        with tab4:
            df_gas = pd.DataFrame(gas_prof)
            st.dataframe(df_gas, use_container_width=True)
            st.line_chart(df_gas.set_index("I")[["CO", "CO2", "H2", "CH4"]])
            st.line_chart(df_gas.set_index("I")[["O2", "H2O", "N2", "H2S"]])
    else:
        st.warning("未解析到沿炉膛分布数据")

    # -----------------------------------------------------------------------
    # 原始输出
    # -----------------------------------------------------------------------
    with st.expander("📝 原始 GASTEST.DAT"):
        if OUTPUT_FILE.exists():
            st.text(OUTPUT_FILE.read_text(encoding="gbk", errors="ignore"))


if __name__ == "__main__":
    main()
