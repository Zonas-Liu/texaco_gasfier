#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO 纯 HTML 方案 - 数据解析与输出处理

 responsibilities:
 - 解析/写入 data/Datain0.dat
 - 解析 GASTEST.DAT
 - 计算湿合成气组成

本模块仅依赖标准库，便于前后端共用。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 输入参数元数据
# ---------------------------------------------------------------------------
PARAM_INFO: Dict[str, Dict[str, Any]] = {
    # 控制与收敛
    "KTRL": {"cn": "控制参数", "unit": "", "desc": "全局控制开关", "group": "控制与收敛", "type": "int"},
    "ITMAX": {"cn": "最大迭代次数", "unit": "", "desc": "牛顿迭代最大步数", "group": "控制与收敛", "type": "int"},
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

PARAM_LINES: List[tuple] = [
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

DEFAULT_PARAMS: Dict[str, Any] = {k: 0 for k in PARAM_INFO}
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

OUTPUT_LABELS = {
    "Iter": "迭代次数",
    "KONVER": "收敛标志",
    "SUMFE": "气体组分残差",
    "SUMWE": "固体质量流残差",
    "SUMX": "碳转化率残差",
    "SUMT": "温度残差",
    "I": "格子号",
    "H(m)": "高度 (m)",
    "U0(m/s)": "气体速度 (m/s)",
    "ResidenceTime(s)": "停留时间 (s)",
    "WE(kg/s)": "碳质量流 (kg/s)",
    "T(C)": "温度 (°C)",
    "X(%)": "碳转化率 (%)",
    "O2": "氧气 O₂",
    "CH4": "甲烷 CH₄",
    "CO": "一氧化碳 CO",
    "CO2": "二氧化碳 CO₂",
    "H2S": "硫化氢 H₂S",
    "H2": "氢气 H₂",
    "N2": "氮气 N₂",
    "H2O": "水蒸气 H₂O",
}

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
# 数值格式化/解析
# ---------------------------------------------------------------------------
def _parse_float(s: str) -> float:
    try:
        return float(s.replace("D", "E").replace("d", "e"))
    except ValueError:
        return 0.0


def _is_number(s: str) -> bool:
    try:
        float(s.replace("D", "E").replace("d", "e"))
        return True
    except ValueError:
        return False


def _format_value(v: Any) -> str:
    if isinstance(v, (int, bool)) and not isinstance(v, float):
        return str(int(v))
    s = f"{float(v):.6E}"
    return s.replace("E+", "D0").replace("E-", "D-").replace("E", "D")


# ---------------------------------------------------------------------------
# Datain0.dat 读写
# ---------------------------------------------------------------------------
def parse_datain0(path: Path) -> Dict[str, Any]:
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
            # 仅作宽容处理，按顺序取前 N 个
            values = values[: len(line_tuple)]
        for name, val_str in zip(line_tuple, values):
            val = float(val_str.replace("D", "E").replace("d", "e"))
            if PARAM_INFO[name].get("type") == "int":
                val = int(val)
            params[name] = val
    return params


def write_datain0(path: Path, params: Dict[str, Any]) -> None:
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


# ---------------------------------------------------------------------------
# GASTEST.DAT 解析
# ---------------------------------------------------------------------------
def parse_gastest(path: Path) -> Optional[Dict[str, Any]]:
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

    # 1. 运行条件（前 20 行）
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
    table_blocks: List[List[tuple]] = []
    current_block: List[tuple] = []
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


def calculate_wet_syngas(dry_flow: Dict[str, float], gas_profile_last: Dict[str, float]):
    """
    根据干合成气体积流量和最后一个 cell 的湿基气体组成计算湿合成气。
    """
    total_dry = sum(dry_flow.values())
    h2o_frac = gas_profile_last.get("H2O", 0.0) / 100.0

    if h2o_frac <= 0.0 or h2o_frac >= 1.0:
        wet_flow_nms = dict(dry_flow)
        wet_flow_nms["H2O"] = 0.0
        wet_flow_nmh = {k: v * 3600.0 for k, v in wet_flow_nms.items()}
        return wet_flow_nms, wet_flow_nmh, total_dry, total_dry * 3600.0

    total_wet_nms = total_dry / (1.0 - h2o_frac)
    h2o_flow_nms = total_dry * h2o_frac / (1.0 - h2o_frac)

    wet_flow_nms = {}
    for k, v in dry_flow.items():
        wet_flow_nms[k] = v
    wet_flow_nms["H2O"] = h2o_flow_nms

    wet_flow_nmh = {k: v * 3600.0 for k, v in wet_flow_nms.items()}
    return wet_flow_nms, wet_flow_nmh, total_wet_nms, total_wet_nms * 3600.0
