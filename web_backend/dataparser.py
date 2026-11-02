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
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from common.result_io import read_result_text, parse_outlet
from common.input_validation import validate_params
from common.display_units import display_spec
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
    "BSLURRY": {"cn": "水煤浆质量流量", "unit": "kg/s", "desc": "水煤浆总质量流量（含煤和水）", "group": "进料参数"},
    "RATIO_COAL": {"cn": "煤浆煤质量分数", "unit": "", "desc": "干煤占水煤浆总质量的比例", "group": "进料参数"},
    "FOXY": {"cn": "氧煤比", "unit": "kg O₂/kg BSWAF", "desc": "纯氧质量流量与无水无灰煤质量流量之比", "group": "进料参数"},
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

# 追加参数仍按固定行号读写；未改动的可选行原样保留。
OPTIONAL_LINES = [
    ("KMODEL", "P_DRUM", "T_FW"),
    ("TW_WALL", "TW_RSC", "D_RSC", "H_RSC", "N_RSC"),
    ("KRELAX_WGS", "KRELAX_METH"),
    ("RSC_MODE", "T_RSC_OUT_C", "H_RSC_MIN", "H_RSC_MAX"),
    ("FEED_MODE", "T_CHAMBER_C", "EFFECTIVE_GAS_NMH"),
    ("FOXY_MIN", "FOXY_MAX", "SLURRY_MIN", "SLURRY_MAX"),
]
DEFAULT_PARAMS.update({"KMODEL": 0, "P_DRUM": 6.5e6, "T_FW": 423.15,
    "TW_WALL": 1773.0, "TW_RSC": 673.0, "D_RSC": 2.6, "H_RSC": 30.0,
    "N_RSC": 30, "KRELAX_WGS": 2.0, "KRELAX_METH": 0.02,
    "RSC_MODE": 0, "T_RSC_OUT_C": 780.0, "H_RSC_MIN": 1.0, "H_RSC_MAX": 120.0})
for name, cn, unit, desc in [
    ("KMODEL", "炉型", "", "选择 TEXACO 或晋华炉 3.0"),
    ("RSC_MODE", "废锅计算模式", "", "目标温度模式同时求有效高度、回收热量和产汽量"),
    ("T_RSC_OUT_C", "目标出口温度", "°C", "目标温度模式启用；需高于废锅有效壁温"),
    ("H_RSC", "废锅有效高度", "m", "固定高度模式的给定值；目标温度模式的搜索初值"),
    ("P_DRUM", "汽包压力", "Pa", "影响饱和蒸汽焓与产汽量，适用范围 4–10 MPa"),
    ("T_FW", "给水温度", "K", "与饱和蒸汽焓共同决定单位回收热量的产汽量"),
    ("D_RSC", "废锅内径", "m", "影响换热面积与气体速度"),
    ("TW_RSC", "废锅有效壁温", "K", "积灰壁面等效辐射温度"),
    ("TW_WALL", "水冷壁有效壁温", "K", "燃烧室渣层表面温度"),
    ("N_RSC", "废锅网格数", "", "1–30；现有反应参数按 30 格标定"),
    ("KRELAX_WGS", "变换反应松弛系数", "", "辐射废锅水煤气变换反应"),
    ("KRELAX_METH", "甲烷化松弛系数", "", "辐射废锅甲烷化反应"),
    ("H_RSC_MIN", "高度搜索下限", "m", "目标温度模式的搜索边界"),
    ("H_RSC_MAX", "高度搜索上限", "m", "未括住目标时报告失败，不超出范围外推"),
]:
    PARAM_INFO[name] = {"cn": cn, "unit": unit, "desc": desc, "group": "辐射废锅设计"}
for name in ("KMODEL", "RSC_MODE", "N_RSC"):
    PARAM_INFO[name]["type"] = "int"
PARAM_INFO["KMODEL"]["options"] = {"0": "TEXACO", "1": "晋华炉 3.0"}
PARAM_INFO["RSC_MODE"]["options"] = {"0": "固定高度", "1": "目标出口温度"}

DEFAULT_PARAMS.update(FEED_MODE=0, T_CHAMBER_C=1228.0, EFFECTIVE_GAS_NMH=49600.0,
                      FOXY_MIN=0.7, FOXY_MAX=1.3, SLURRY_MIN=5.0, SLURRY_MAX=30.0)
for name, cn, unit, desc in [
    ('FEED_MODE', '进料计算模式', '', '按燃烧室出口温度与 CO+H₂ 标方流量反算氧煤比和水煤浆总量'),
    ('T_CHAMBER_C', '目标燃烧室出口温度', '℃', '允许温差 ±0.5 ℃'),
    ('EFFECTIVE_GAS_NMH', '目标有效气量（CO＋H₂）', 'Nm³/h', '燃烧室出口；沿用模型 22.4 Nm³/kmol；允许误差为目标的 0.1%（最小 1 Nm³/h）'),
    ('FOXY_MIN', '氧煤比搜索下限', 'kg O₂/kg BSWAF', '纯氧 / 无水无灰煤'),
    ('FOXY_MAX', '氧煤比搜索上限', 'kg O₂/kg BSWAF', '纯氧 / 无水无灰煤'),
    ('SLURRY_MIN', '煤浆量搜索下限', 'kg/s', '水煤浆总量，包含煤和水'),
    ('SLURRY_MAX', '煤浆量搜索上限', 'kg/s', '保持煤浆浓度、氧气纯度及其余参数不变'),
]:
    PARAM_INFO[name] = {'cn': cn, 'unit': unit, 'desc': desc, 'group': '燃烧室反算'}
PARAM_INFO['FEED_MODE'].update(type='int', options={'0': '给定进料正算', '1': '温度＋有效气量反算'})
# API/文件仍使用模型单位，前端根据元数据进行可逆转换。
for info in PARAM_INFO.values():
    info['display'] = display_spec(info['unit'])
PARAM_INFO['P_DRUM']['desc'] = '影响饱和蒸汽焓与产汽量；适用范围 3.898675–9.898675 MPaG'

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
    lines = text.splitlines()

    for line_tuple, line in zip(PARAM_LINES + OPTIONAL_LINES, lines):
        numeric_part = line.split("/")[0].strip()
        if not numeric_part:
            continue
        values = [v.strip() for v in numeric_part.split(",")]
        if len(values) != len(line_tuple):
            # 仅作宽容处理，按顺序取前 N 个
            values = values[: len(line_tuple)]
        for name, val_str in zip(line_tuple, values):
            val = float(val_str.replace("D", "E").replace("d", "e"))
            if PARAM_INFO[name].get("type") == "int":
                if not val.is_integer():
                    raise ValueError(f"{name} 必须为整数")
                val = int(val)
            params[name] = val
    return params


def write_datain0(path: Path, params: Dict[str, Any]) -> None:
    """将参数字典写回 Datain0.dat。"""
    validate_params(params)
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
    # 先读取额外参数行（如晋华炉3.0新增的第12-14行），避免GUI保存时丢失
    extra_lines = []
    if path.exists():
        existing = path.read_text(encoding="utf-8").splitlines()
        extra_lines = existing[len(comments):]
    original = parse_datain0(path)
    for offset, names in enumerate(OPTIONAL_LINES):
        if any(params.get(name, original[name]) != original[name] for name in names):
            while len(extra_lines) <= offset:
                missing = OPTIONAL_LINES[len(extra_lines)]
                extra_lines.append(",".join(_format_value(original[name]) for name in missing)
                                   + "/ " + ",".join(missing))
            extra_lines[offset] = ",".join(_format_value(params.get(name, original[name])) for name in names) + "/ " + ",".join(names)
    with open(path, "w", encoding="utf-8") as f:
        for line, cmt in zip(lines, comments):
            f.write(f"{line}/{cmt}\n")
        for extra in extra_lines:
            f.write(extra + "\n")


# ---------------------------------------------------------------------------
# GASTEST.DAT 解析
# ---------------------------------------------------------------------------
def parse_gastest(path: Path) -> Optional[Dict[str, Any]]:
    """解析 GASTEST.DAT，返回结构化结果字典。"""
    if not path.exists():
        return None

    text = read_result_text(path)
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

    result["outlet"] = parse_outlet(text)

    # 晋华炉汇总来自本次输出，而非当前输入，避免改参后混用旧结果与新工况。
    heat_fields = {
        "汽包压力": "drum_pressure_mpa",
        "水冷壁产汽量": "steam_wall_tph",
        "辐射废锅产汽量": "steam_rsc_tph",
        "总产汽量": "steam_total_tph",
        "水冷壁热负荷": "heat_wall_mw",
        "辐射废锅热负荷": "heat_rsc_mw",
    }
    result["heat_recovery"] = {}
    for label, key in heat_fields.items():
        match = re.search(r"^\s*" + re.escape(label) + r":\s*([-+]?\d+(?:\.\d+)?)", text, re.MULTILINE)
        if match:
            result["heat_recovery"][key] = float(match.group(1))

    result["outlet_sections"] = parse_outlet_sections(text, result)
    design_line = re.search(r"^RSC_DESIGN_JSON: (.+)$", text, re.MULTILINE)
    if design_line:
        result["rsc_design"] = json.loads(design_line.group(1))
    feed_line = re.search(r'^FEED_DESIGN_JSON: (.+)$', text, re.MULTILINE)
    if feed_line:
        result['feed_design'] = json.loads(feed_line.group(1))
    result["operating_conditions"] = dict(list(result["operating_conditions"].items())[:10])
    return result


def parse_outlet_sections(text, result):
    """读取 KOLERG 的两出口对照表；只用本次输出，不混用当前输入参数。"""
    gases = ("O2", "CH4", "CO", "CO2", "H2S", "H2", "N2", "H2O")
    profiles = {row["I"]: row for row in result["gas_composition_profile"]}
    internal = {row["I"]: row for row in result["internal_profile"]}
    if not profiles:
        return []
    last = max(profiles)
    is_rsc = bool(result["heat_recovery"]) and last > 30
    locations = [("chamber", "燃烧室出口", 30), ("rsc", "辐射废锅出口", last)] if is_rsc else [
        ("chamber", "气化炉出口", last)]
    flow_pairs = {}
    exact_line = re.search(r'^OUTLET_FLOWS_JSON: (.+)$', text, re.MULTILINE)
    exact = json.loads(exact_line.group(1)) if exact_line else {}
    if "各组分流量对比" in text:
        block = text.split("各组分流量对比", 1)[1].split("总计", 1)[0]
        for line in block.splitlines():
            parts = line.split()
            if len(parts) == 4 and parts[0] in gases and all(_is_number(v) for v in parts[1:]):
                flow_pairs[parts[0]] = [_parse_float(v) for v in parts[1:3]]
    sections = []
    for column, (key, label, cell) in enumerate(locations):
        if cell not in profiles:
            continue
        wet = {g: profiles[cell][g] for g in gases}
        dry_sum = sum(wet[g] for g in gases[:-1])
        dry = {g: wet[g] / dry_sum * 100 if dry_sum > 0 else None for g in gases[:-1]}
        flow = {}
        if is_rsc and len(flow_pairs) == len(gases):
            flow = {g: flow_pairs[g][column] for g in gases}
        elif cell == last and result["volume_flow"]:
            flow, _, _, _ = calculate_wet_syngas(result["volume_flow"], profiles[cell])
        if cell == last and result["syngas_composition"]:
            dry = dict(result["syngas_composition"])
        point = exact.get(str(cell), {})
        molar = point.get('molar_flow_kmol_h', {g: v * 3600 / 22.4 for g, v in flow.items()})
        if point:
            flow = {g: v * 22.4 / 3600 for g, v in molar.items()}
            all_moles = sum(molar.values())
            dry_moles = all_moles - molar['H2O']
            wet = {g: v / all_moles * 100 if all_moles else None for g, v in molar.items()}
            dry = {g: molar[g] / dry_moles * 100 if dry_moles else None for g in gases[:-1]}
        total_dry = sum(flow.get(g, 0) for g in gases[:-1]) if flow else None
        total_wet = sum(flow.values()) if flow else None
        sections.append({
            "key": key, "label": label, "cell": cell,
            "temperature_c": point.get('temperature_c', internal.get(cell, {}).get("T(C)")),
            "dry_composition": dry, "wet_composition": wet,
            "volume_flow": flow, "total_dry_nms": total_dry, "total_wet_nms": total_wet,
            'molar_flow_kmol_h': molar, 'total_molar_kmol_h': sum(molar.values()) if molar else None,
            'ash_kg_h': point.get('ash_kg_h'),
            'effective_gas_nmh': (flow['CO'] + flow['H2']) * 3600 if flow else None,
            "h2_co_ratio": dry["H2"] / dry["CO"] if dry.get("CO") else None,
        })
    return sections


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
