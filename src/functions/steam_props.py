#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
晋华炉3.0 - 饱和蒸汽物性与产汽量计算 (jinhualu分支新增)

适用范围: 汽包压力 4~10 MPa，简化关联式误差 <2%
数据来源: 饱和水蒸气表拟合
"""
import math


def tsat_water(p_pa: float) -> float:
    """
    饱和温度 [K]，由压力计算
    拟合点: 4MPa→523.5K, 6.5MPa→554.2K, 8MPa→568.2K, 10MPa→584.1K
    """
    p_mpa = max(p_pa / 1.0e6, 0.1)
    return 431.9 + 66.1 * math.log(p_mpa)


def h_sat_steam(p_pa: float) -> float:
    """
    饱和蒸汽焓 h″ [kJ/kg]
    拟合点: 4MPa→2801, 6.5MPa→2773, 8MPa→2758, 10MPa→2725
    """
    p_mpa = max(p_pa / 1.0e6, 0.1)
    return 2852.0 - 12.67 * p_mpa


def latent_heat(p_pa: float) -> float:
    """
    汽化潜热 r [kJ/kg]
    拟合点: 4MPa→1714, 6.5MPa→1500, 8MPa→1441, 10MPa→1318
    """
    p_mpa = max(p_pa / 1.0e6, 0.1)
    return 2312.0 - 431.7 * math.log(p_mpa)


def h_feedwater(t_k: float) -> float:
    """
    给水(未饱和水)焓 [kJ/kg]，近似 cp≈4.186 kJ/(kg·K)
    """
    return 4.186 * (t_k - 273.15)


def steam_production(q_w: float, p_drum_pa: float, t_fw_k: float) -> float:
    """
    由回收热量计算饱和蒸汽产量

    参数:
        q_w: 回收热负荷 [W]
        p_drum_pa: 汽包压力 [Pa]
        t_fw_k: 给水温度 [K]

    返回:
        蒸汽产量 [kg/s]
    """
    if q_w <= 0.0:
        return 0.0
    delta_h = (h_sat_steam(p_drum_pa) - h_feedwater(t_fw_k)) * 1000.0  # [J/kg]
    return q_w / delta_h
