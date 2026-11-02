"""汽包/给水侧 IAPWS-IF97 物性，Pa/K输入，焓为kJ/kg。

给水按汽包压力计算压缩液焓；不与反应侧含生成焓的ENTHP基准混用。
外部操作范围仍为4–10 MPa。缓存仅保存按完整温压参数得到的不可变标量。
"""
from functools import lru_cache
import math
from iapws import IAPWS97


def _pressure(p_pa):
    if not math.isfinite(p_pa) or not 4e6 <= p_pa <= 10e6:
        raise ValueError('汽包物性压力必须为4–10 MPa绝压')
    return p_pa / 1e6


@lru_cache(maxsize=128)
def _saturation(p_pa):
    pressure = _pressure(p_pa)
    liquid, vapor = IAPWS97(P=pressure, x=0), IAPWS97(P=pressure, x=1)
    return float(vapor.T), float(liquid.h), float(vapor.h)


def tsat_water(p_pa: float) -> float:
    return _saturation(p_pa)[0]


def h_sat_steam(p_pa: float) -> float:
    return _saturation(p_pa)[2]


def latent_heat(p_pa: float) -> float:
    _, liquid, vapor = _saturation(p_pa)
    return vapor - liquid


@lru_cache(maxsize=256)
def h_feedwater(t_k: float, p_pa: float) -> float:
    """给水压缩液焓；压力必填，禁止默认为大气压或忽略压力。"""
    pressure = _pressure(p_pa)
    if not math.isfinite(t_k) or not 273.15 <= t_k < tsat_water(p_pa):
        raise ValueError('给水温度必须不低于0℃且低于汽包饱和温度')
    return float(IAPWS97(P=pressure, T=t_k).h)


def steam_production(q_w: float, p_drum_pa: float, t_fw_k: float) -> float:
    """回收热负荷W / 汽水焓差J/kg → 饱和蒸汽kg/s。"""
    if not math.isfinite(q_w):
        raise ValueError('回收热负荷必须为有限数')
    delta_h = (h_sat_steam(p_drum_pa) - h_feedwater(t_fw_k, p_drum_pa)) * 1000
    return max(q_w, 0.0) / delta_h
