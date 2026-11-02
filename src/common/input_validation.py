"""EINGAB 与界面共用的输入边界检查，不改变有效工况的计算公式。"""
import math


def validate_params(params):
    """拒绝非有限数、非整数控制量和会导致除零/越界的输入。"""
    for name, value in params.items():
        if isinstance(value, bool) or not math.isfinite(float(value)):
            raise ValueError(f"{name} 必须是有限数值")
    for name in ("KTRL", "ITMAX", "KMODEL", "N_RSC", "RSC_MODE", "FEED_MODE"):
        if name in params and float(params[name]) != int(params[name]):
            raise ValueError(f"{name} 必须是整数")
    for name in ("KTRL", "KMODEL", "RSC_MODE", "FEED_MODE"):
        if name in params and params[name] not in (0, 1):
            raise ValueError(f"{name} 只能为 0 或 1")
    positive = ("ITMAX", "SKONFE", "SKONWE", "SKONX", "SKONT", "BSLURRY",
                "RATIO_COAL", "PURE_O2", "DP", "HU", "ELC", "PWK", "TU", "TW",
                "PFEED_SL", "TFEED_SL", "PFEED_O2", "TFEED_O2",
                "PFEED_CO2", "TFEED_CO2")
    for name in positive:
        if name in params and params[name] <= 0:
            raise ValueError(f"{name} 必须大于 0")
    for name in ("RATIO_COAL", "PURE_O2", "OX_PART", "XVM", "ELC", "ELH",
                 "ELO", "ELN", "ELS", "ELAS", "ELH2O", "QLOSS"):
        if name in params and not 0 <= params[name] <= 1:
            raise ValueError(f"{name} 必须在 0 到 1 之间")
    for name in ("FOXY", "RATIO_CO2", "KRELAX_WGS", "KRELAX_METH"):
        if name in params and params[name] < 0:
            raise ValueError(f"{name} 不得为负")
    if params.get("ELAS", 0) + params.get("ELH2O", 0) >= 1:
        raise ValueError("灰分与水分之和必须小于 1")
    if params.get("FEED_MODE") == 1:
        if params['T_CHAMBER_C'] <= -273.15 or params['EFFECTIVE_GAS_NMH'] <= 0:
            raise ValueError('燃烧室目标温度必须高于绝对零度，有效气量必须大于 0')
        for low, high, initial in (('FOXY_MIN', 'FOXY_MAX', 'FOXY'),
                                   ('SLURRY_MIN', 'SLURRY_MAX', 'BSLURRY')):
            if not 0 < params[low] < params[high]:
                raise ValueError(f'{low}/{high} 必须满足 0 < 下限 < 上限')
            if not params[low] <= params[initial] <= params[high]:
                raise ValueError(f'{initial} 搜索初值必须在给定范围内')
    if params.get("RSC_MODE") == 1:
        if params.get("KMODEL") != 1:
            raise ValueError("目标出口温度模式仅适用于晋华炉（KMODEL=1）")
        if not 0 < params["H_RSC_MIN"] < params["H_RSC_MAX"]:
            raise ValueError("废锅高度搜索范围必须满足 0 < 下限 < 上限")
        if params["T_RSC_OUT_C"] + 273.15 <= params["TW_RSC"]:
            raise ValueError("目标出口温度必须高于废锅有效壁温")
    if params.get("KMODEL") == 1:
        if not 1 <= params["N_RSC"] <= 30:
            raise ValueError("N_RSC 必须在 1 到 30 之间（NZDIM=61）")
        for name in ("D_RSC", "H_RSC", "TW_WALL", "TW_RSC", "T_FW"):
            if params[name] <= 0:
                raise ValueError(f"{name} 必须大于 0")
        if not 4e6 <= params["P_DRUM"] <= 10e6:
            raise ValueError("P_DRUM 超出物性范围 3.898675–9.898675 MPaG（绝压 4–10 MPa）")
        from functions.steam_props import tsat_water
        if not 273.15 <= params["T_FW"] < tsat_water(params["P_DRUM"]):
            raise ValueError("T_FW 必须为液态给水温度（0℃ 至汽包饱和温度以下）")
