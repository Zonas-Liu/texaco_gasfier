#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 反应速率和热力学性质计算模块
对应Fortran文件: Wg7.for

本模块包含以下功能:
1. 碳反应速率计算: A1-A5
2. 扩散系数计算: XKC_O2, XKC_H2O, XKC_CO2, XKC_H2
3. 结构参数: PHI
4. 总反应速率: RI
5. 热力学性质: ENTHP, FH2, FSOLID, FH2S, FO2, FC, FN2, FCO2, FCO, FCH4, FH2O
6. 辅助函数: CMP, CMPS, CMPT, FPART, TPAR
"""

import numpy as np
from common.common_data import common


# ============================================================================
# 辅助函数 - 颗粒温度计算 (TPAR)
# ============================================================================

def TPAR(I: int) -> float:
    """
    计算颗粒温度 (Particle Temperature)
    
    对应Fortran: Wg8.for (FUNCTION TPAR)
    
    颗粒温度 = 气体温度 + DELT
    其中DELT是由于氧气反应引起的温升
    DELT = FEMF(1,I)/FEM(I)*66.D+03*PWK/(RAG*T(I))
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        颗粒温度 [K]
    """
    # 计算温升DELT
    if common.FEM[I] > 0:
        DELT = common.FEMF[1, I] / common.FEM[I] * 66.0e3 * common.PWK / (common.RAG * common.T[I])
    else:
        DELT = 0.0
    
    if DELT <= 0.0:
        DELT = 0.0
    
    TP = common.T[I] + DELT
    
    return TP


# ============================================================================
# 反应速率系数函数 (XKC系列)
# ============================================================================

def PHI(I: int) -> float:
    """
    机械因子/结构参数 (Mechanical Factor)
    
    根据Wen的模型计算颗粒结构参数，影响扩散系数
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        结构参数 PHI (无量纲)
    """
    TP = TPAR(I)
    TM = (TP + common.T[I]) / 2.0
    
    # 防除零和溢出保护
    if TM < 1.0:
        TM = 1.0
    
    # 根据Wen模型计算
    exp_arg = -6249.0 / TM
    if exp_arg < -700:
        exp_arg = -700
    PP = 2500.0 * np.exp(exp_arg)
    
    if common.DP < 5.0e-05:
        return (2.0 * PP + 2.0) / (PP + 2.0)
    elif common.DP <= 1.0e-03:
        return ((2.0 * PP + 2.0) - PP * (100.0 * common.DP - 0.005) / 0.095) / (PP + 2.0)
    else:
        return 1.0


def XKC_O2(I: int) -> float:
    """
    计算碳与氧气反应的速率系数
    
    单位: kmol/(m^2·Pa·s)
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        O2反应速率系数
    """
    TP = TPAR(I)
    VOID = 0.75
    
    # 1kg原煤对应的灰分量 FASH
    FASH = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 计算碳转化率 FOC
    # 防除零保护: 确保分母不会太小
    x_safe = min(common.X[I], 0.999999)
    if x_safe >= 1.0:
        FOC = 0.0
    else:
        FOC = 1.0 - FASH * x_safe / (1.0 - x_safe)
    
    # 反应核模型参数 YY
    YY = ((1.0 - FOC) / (1.0 - common.XCVM0)) ** 0.333
    if YY >= 1.0:
        YY = 1.0
    
    # RKCH: 化学反应速率常数
    # 防溢出保护
    exp_arg = -17967.0 / TP
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    RKCH = 8710.0 * np.exp(exp_arg)
    
    # D0: 扩散系数基础值
    # 防负值: 确保温度为正
    t_safe = max(common.T[I], 273.15)
    D0 = 4.26 * (t_safe / 1800.0) ** 1.75 / common.PWK * common.P0
    
    # RKDG: 气相扩散系数
    RKDG = 0.292 * PHI(I) * D0 / (common.DP * 100.0) / common.T[I] * common.COEF_A3
    
    # RKDA: 灰层扩散系数
    RKDA = VOID ** 2.5 * RKDG
    
    # XKC_O2: 总反应速率系数 (根据Wen模型)
    XKC = YY * YY / (1.0 / RKCH + YY * YY / RKDG + 1.0 / RKDA * (YY - YY * YY))
    
    # 单位转换: g/(cm^2·atm·s) -> kmol/(m^2·Pa·s)
    XKC = XKC * 10.0 / 1.01325e5 / 12.0
    
    return XKC


def XKC_H2O(I: int) -> float:
    """
    计算碳与水蒸气反应的速率系数
    
    反应: C + H2O -> CO + H2
    单位: kmol/(m^2·Pa·s)
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        H2O反应速率系数
    """
    TP = TPAR(I)
    VOID = 0.75
    
    # 1kg原煤对应的灰分量 FASH
    FASH = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 计算碳转化率 FOC
    # 防除零保护: 确保分母不会太小
    x_safe = min(common.X[I], 0.999999)
    if x_safe >= 1.0:
        FOC = 0.0
    else:
        FOC = 1.0 - FASH * x_safe / (1.0 - x_safe)
    
    # 反应核模型参数 YY
    YY = ((1.0 - FOC) / (1.0 - common.XCVM0)) ** 0.333
    
    # RKCH: 化学反应速率常数
    # 防溢出保护
    exp_arg = -21060.0 / TP
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    RKCH = 247.0 * np.exp(exp_arg)
    
    # RKDG: 气相扩散系数
    # 防负值: 确保温度为正
    t_safe = max(common.T[I], 273.15)
    RKDG = 10.0 * 1.0e-4 * (t_safe / 2000.0) ** 0.75 * common.P0 / (common.DP * 100.0 * common.PWK) * common.COEF_A1
    
    # RKDA: 灰层扩散系数
    RKDA = VOID ** 2.5 * RKDG
    
    # XKC_H2O: 总反应速率系数
    XKC = YY * YY / (1.0 / RKCH + YY * YY / RKDG + 1.0 / RKDA * (YY - YY * YY))
    
    # 单位转换
    XKC = XKC * 10.0 / 1.01325e5 / 12.0
    
    return XKC


def XKC_CO2(I: int) -> float:
    """
    计算碳与二氧化碳反应的速率系数
    
    反应: C + CO2 -> 2CO
    单位: kmol/(m^2·Pa·s)
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        CO2反应速率系数
    """
    TP = TPAR(I)
    VOID = 0.75
    
    # 1kg原煤对应的灰分量 FASH
    FASH = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 计算碳转化率 FOC
    # 防除零保护: 确保分母不会太小
    x_safe = min(common.X[I], 0.999999)
    if x_safe >= 1.0:
        FOC = 0.0
    else:
        FOC = 1.0 - FASH * x_safe / (1.0 - x_safe)
    
    # 反应核模型参数 YY
    YY = ((1.0 - FOC) / (1.0 - common.XCVM0)) ** 0.333
    
    # RKCH: 化学反应速率常数
    # 防溢出保护
    exp_arg = -21060.0 / TP
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    RKCH = 247.0 * np.exp(exp_arg)
    
    # RKDG: 气相扩散系数
    # 防负值: 确保温度为正
    t_safe = max(common.T[I], 273.15)
    RKDG = 7.450e-4 * (t_safe / 2000.0) ** 0.75 * common.P0 / (common.DP * 100.0 * common.PWK) * common.COEF_A4
    
    # RKDA: 灰层扩散系数
    RKDA = VOID ** 2.5 * RKDG
    
    # XKC_CO2: 总反应速率系数
    XKC = YY * YY / (1.0 / RKCH + YY * YY / RKDG + 1.0 / RKDA * (YY - YY * YY))
    
    # 单位转换
    XKC = XKC * 10.0 / 1.01325e5 / 12.0
    
    return XKC


def XKC_H2(I: int) -> float:
    """
    计算碳与氢气反应的速率系数
    
    反应: C + 2H2 -> CH4
    单位: kmol/(m^2·Pa·s)
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        H2反应速率系数
    """
    TP = TPAR(I)
    VOID = 0.75
    
    # 1kg原煤对应的灰分量 FASH
    FASH = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 计算碳转化率 FOC
    # 防除零保护: 确保分母不会太小
    x_safe = min(common.X[I], 0.999999)
    if x_safe >= 1.0:
        FOC = 0.0
    else:
        FOC = 1.0 - FASH * x_safe / (1.0 - x_safe)
    
    # 反应核模型参数 YY
    YY = ((1.0 - FOC) / (1.0 - common.XCVM0)) ** 0.333
    
    # RKCH: 化学反应速率常数
    RKCH = 0.12 * np.exp(-17921.0 / TP)
    
    # RKDG: 气相扩散系数
    RKDG = 1.330e-3 * (common.T[I] / 2000.0) ** 0.75 * common.P0 / (common.DP * 100.0 * common.PWK) * common.COEF_A2
    
    # RKDA: 灰层扩散系数
    RKDA = VOID ** 2.5 * RKDG
    
    # XKC_H2: 总反应速率系数
    XKC = YY * YY / (1.0 / RKCH + YY * YY / RKDG + 1.0 / RKDA * (YY - YY * YY))
    
    # 单位转换
    XKC = XKC * 10.0 / 1.01325e5 / 12.0
    
    return XKC


# ============================================================================
# 碳反应速率函数 (A1-A5)
# ============================================================================

def _update_gas_fractions(I: int) -> None:
    """
    更新气体组分摩尔分数 Y[1:9]
    
    Args:
        I: 格子索引 (1-based)
    """
    # 防除零保护
    fem_safe = max(common.FEM[I], 1e-20)
    for J in range(1, common.NGAS + 1):
        common.Y[J] = common.FEMF[J, I] / fem_safe


def A1(I: int) -> float:
    """
    计算碳与水蒸气反应速率
    
    反应: C + H2O -> CO + H2
    单位: kmol/s
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        反应速率 [kmol/s]
    """
    # 更新气体摩尔分数
    _update_gas_fractions(I)
    
    TP = TPAR(I)
    
    # 化学平衡常数
    # 防溢出保护
    exp_arg = 17.644 - 30260.0 / (1.8 * TP)
    if exp_arg > 700:
        exp_arg = 700
    if exp_arg < -700:
        exp_arg = -700
    CS_KEQ1 = np.exp(exp_arg)
    
    # 分压项
    PA1 = common.Y[8] - common.Y[6] * common.Y[3] * common.PWK / common.P0 / CS_KEQ1
    
    # 检查反应条件
    if common.Y[8] < 0.0001 or PA1 < 0.0:
        return 0.0
    
    # 颗粒数量计算
    AM = common.XMS[I] / common.ROS[I] * 6.0 / (common.PI * common.DP ** 3)
    
    # 反应速率计算
    rate = AM * common.PI * common.DP ** 2.0 * XKC_H2O(I) * common.PWK * PA1 * common.CTRL_A1
    
    return rate


def A2(I: int) -> float:
    """
    计算碳与氢气反应速率 (甲烷化反应)
    
    反应: C + 2H2 -> CH4
    单位: kmol/s
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        反应速率 [kmol/s]
    """
    # 更新气体摩尔分数
    _update_gas_fractions(I)
    
    TP = TPAR(I)
    
    # 化学平衡常数
    # 防溢出保护
    exp_arg = 18400.0 / (1.8 * TP)
    if exp_arg > 700:
        exp_arg = 700
    CS_KEQ2 = 0.175 / 34713.0 * np.exp(exp_arg)
    # 防除零保护
    if CS_KEQ2 < 1e-20:
        CS_KEQ2 = 1e-20
    
    # 分压项
    PA2 = common.Y[6] - np.sqrt(common.Y[2] * common.P0 / common.PWK / CS_KEQ2)
    
    # 检查反应条件
    if common.Y[6] < 0.001 or PA2 < 0.0:
        return 0.0
    
    # 颗粒数量计算
    AM = common.XMS[I] / common.ROS[I] * 6.0 / (common.PI * common.DP ** 3)
    
    # 反应速率计算
    rate = AM * common.PI * common.DP ** 2.0 * XKC_H2(I) * common.PWK * PA2 * common.CTRL_A2
    
    return rate


def A3(I: int) -> float:
    """
    计算碳与氧气反应速率 (燃烧反应)
    
    反应: C + O2 -> CO2 (或2CO)
    单位: kmol/s
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        反应速率 [kmol/s]
    """
    # 更新气体摩尔分数
    _update_gas_fractions(I)
    
    # 检查反应条件
    if common.Y[1] <= 0.0:
        return 0.0
    
    PA3 = common.Y[1]
    
    # 颗粒数量计算
    AM = common.XMS[I] / common.ROS[I] * 6.0 / (common.PI * common.DP ** 3)
    
    # 反应速率计算
    rate = AM * common.PI * common.DP ** 2.0 * XKC_O2(I) * common.PWK * PA3 * common.CTRL_A3
    
    return rate


def A4(I: int) -> float:
    """
    计算碳与二氧化碳反应速率 (Boudouard反应)
    
    反应: C + CO2 -> 2CO
    单位: kmol/s
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        反应速率 [kmol/s]
    """
    # 更新气体摩尔分数
    _update_gas_fractions(I)
    
    # 检查反应条件
    if common.Y[4] <= 0.0:
        return 0.0
    
    # 颗粒数量计算
    AM = common.XMS[I] / common.ROS[I] * 6.0 / (common.PI * common.DP ** 3)
    
    # 反应速率计算
    rate = AM * common.PI * common.DP ** 2.0 * XKC_CO2(I) * common.PWK * common.Y[4] * common.CTRL_A4
    
    return rate


def A5(I: int) -> float:
    """
    计算催化水煤气变换反应速率
    
    反应: CO + H2O <-> CO2 + H2 (催化)
    单位: kmol/s
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        反应速率 [kmol/s]
    """
    # 更新气体摩尔分数
    _update_gas_fractions(I)
    
    TP = TPAR(I)
    TM = (TP + common.T[I]) / 2.0
    
    FW = 0.2  # 权重因子
    
    # 化学平衡常数
    XKEQ = np.exp(-3.6893 + 7234.0 / (1.8 * TM))
    
    # 分压计算
    PCO2 = common.Y[4] * common.PWK / common.P0
    PCO = common.Y[3] * common.PWK / common.P0
    PH2 = common.Y[6] * common.PWK / common.P0
    PH2O = common.Y[8] * common.PWK / common.P0
    
    # 防零保护: 如果PH2O为0，设为极小值避免除零
    if PH2O < 1e-20:
        PH2O = 1e-20
    
    # 平衡组成
    XCO0 = common.P0 / common.PWK * PCO2 * PH2 / (XKEQ * PH2O)
    
    # 检查反应条件
    if common.Y[3] < 0.001 or common.Y[8] < 0.001:
        return 0.0
    
    if common.Y[3] - XCO0 < 0.0:
        return 0.0
    
    # 反应速率计算
    rate = FW * 2.877e5 * (common.Y[3] - XCO0) * np.exp(-27760.0 / 1.987 / TM)
    rate = rate * (common.PWK / common.P0) ** (0.5 - common.PWK / common.P0 / 250.0) * np.exp(-8.91 + 5553.0 / TM)
    rate = rate * common.XMS[I] * (1.0 - common.X[I]) * common.CTRL_A5
    
    return rate


def RI(I: int) -> float:
    """
    计算总碳消耗速率
    
    总反应速率 = A1 + A2 + A3 + A4，然后乘以碳的分子量转换为质量速率
    单位: kg/s
    
    Args:
        I: 格子索引 (1-based)
        
    Returns:
        总碳消耗速率 [kg/s]
    """
    # 更新气体摩尔分数
    _update_gas_fractions(I)
    
    # 总反应速率 (kmol/s)，乘以12.0转换为 kg/s
    total_rate = (A1(I) + A2(I) + A3(I) + A4(I)) * 12.0
    
    return total_rate


# ============================================================================
# 热力学辅助函数
# ============================================================================

def CMP(A: float, B: float, C: float, D: float, T: float, T0: float) -> float:
    """
    计算热容积分 (用于气体组分)
    
    积分公式: ∫(A + B×10^-3×T + C×10^5/T^2 + D×10^-6×T^3) dT
    单位: kJ/kmol
    
    Args:
        A, B, C, D: 热容系数 (Knacke/Barin格式)
        T: 终止温度 [K]
        T0: 起始温度 [K]
        
    Returns:
        积分值 [kJ/kmol]
    """
    result = 4.186 * (
        A * (T - T0) +
        B * 0.05 * (T * T * 0.01 - T0 * T0 * 0.01) -
        C * (1.0e5 / T - 1.0e5 / T0) +
        D / 3.0 * ((0.01 * T) ** 3 - (0.01 * T0) ** 3)
    )
    return result


def CMP_SOLID(A: float, B: float, C: float, D: float, T: float, T0: float) -> float:
    """
    计算热容积分 (与Fortran CMP函数一致)
    
    Fortran热容公式: Cp = A + B*1e-3*T + C*1e5/T^2 + D*1e-6*T^3
    积分公式: 4.186 * (A*(T-T0) + B*0.05*(T^2*0.01-T0^2*0.01) 
                      - C*(1e5/T-1e5/T0) + D/3*((0.01*T)^3-(0.01*T0)^3))
    单位: kJ/kmol (与Fortran一致)
    
    参考: Wg7.for, FUNCTION CMP (line 892-901)
    
    Args:
        A, B, C, D: 热容系数 (Fortran格式)
        T: 终止温度 [K]
        T0: 起始温度 [K]
        
    Returns:
        积分值 [kJ/kmol]
    """
    # Fortran CMP 公式:
    # CMP = 4.186 * (A*(T-T0) + B*.05*(T*T*.01-T0*T0*0.01) 
    #              - C*(1.E+05/T-1.0E+05/T0) + D/3.*((.01*T)**3-(.01*T0)**3))
    term_a = A * (T - T0)
    term_b = B * 0.05 * (T * T * 0.01 - T0 * T0 * 0.01)
    term_c = -C * (1.0e5 / T - 1.0e5 / T0)
    term_d = D / 3.0 * ((0.01 * T)**3 - (0.01 * T0)**3)
    
    result = 4.186 * (term_a + term_b + term_c + term_d)
    return result


def CMPS(A: float, B: float, C: float, D: float, T: float, T0: float) -> float:
    """
    计算热容积分 (H2S专用)
    
    热容公式: Cp = A + B×T + C×T^2 + D×T^3
    单位: kJ/kmol
    
    Args:
        A, B, C, D: 热容系数
        T: 终止温度 [K]
        T0: 起始温度 [K]
        
    Returns:
        积分值 [kJ/kmol]
    """
    result = (
        A * (T - T0) +
        B * (T ** 2 - T0 ** 2) +
        C * (T ** 3 - T0 ** 3) +
        D * (T ** 4 - T0 ** 4)
    )
    return result


def CMPT(A: float, B: float, C: float, D: float, T: float, T0: float) -> float:
    """
    计算热容除以温度的积分 (用于气体组分)
    
    积分公式: ∫(A + B×10^-3×T + C×10^5/T^2 + D×10^-6×T^3)/T dT
    单位: kJ/(kmol·K)
    
    Args:
        A, B, C, D: 热容系数 (Knacke/Barin格式)
        T: 终止温度 [K]
        T0: 起始温度 [K]
        
    Returns:
        积分值 [kJ/(kmol·K)]
    """
    result = 4.186 * (
        A * np.log(T / T0) +
        B * 0.001 * (T - T0) -
        0.5 * C * (1.0e5 / T / T - 1.0e5 / T0 / T0) +
        D * 0.5e-6 * (T * T - T0 * T0)
    )
    return result


def CMPT_SOLID(A: float, B: float, C: float, D: float, T: float, T0: float) -> float:
    """
    计算热容除以温度的积分 (用于固体组分，与Fortran CMPT一致)
    
    积分公式: ∫(A + B*T + C*T^2 + D*T^3)/T dT = A*ln(T/T0) + B*(T-T0) + C*(T^2-T0^2)/2 + D*(T^3-T0^3)/3
    单位: kJ/(kmol·K)
    
    Args:
        A, B, C, D: 热容系数 (简单多项式格式)
        T: 终止温度 [K]
        T0: 起始温度 [K]
        
    Returns:
        积分值 [kJ/(kmol·K)]
    """
    result = A * np.log(T / T0) + B * (T - T0) + C * (T**2 - T0**2) / 2.0 + D * (T**3 - T0**3) / 3.0
    return result


def FPART(A: float, B: float, C: float, D: float, E: float, F: float, G: float, T: float) -> float:
    """
    计算分压
    
    Args:
        A, B, C, D, E, F, G: 系数
        T: 温度 [K]
        
    Returns:
        分压 [Pa]
    """
    RLOGP = -A / T + B + C * np.log10(T) + (D + (E + (F + G * T) * T) * T) * T
    result = 1.3332e-03 * (10.0 ** RLOGP)
    return result


# ============================================================================
# 热力学性质函数
# ============================================================================

def FH2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算H2的热力学性质
    
    数据来源: Knacke/Barin
    H2被视为理想气体
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数 (未使用)
        IAGG: 聚集态 ('G'为气态)
        KALZG: 计算类型 ('ENTH'为焓, 'ENTR'为熵, 'IDIC'为密度, 'MOLG'为分子量, 'IVIS'为粘度)
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 6.52, 0.78, 0.12, 0.0
    S298, TU = 130.645, 298.15
    RM = 8.3143
    XMOLG = 2.0159
    SIGMA, EPSK = 2.827, 59.7
    
    # 修复: 接受'S'作为固体相态 (用于固体碳焓值计算)
    if IAGG not in ['G', '    ', '', 'S']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = CMP(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT(A, B, C, D, TEMP, TU) - RM * np.log(PP / 1.01325e5)
        return E
    
    elif KALZG == 'IDIC':
        # 密度 [kg/m^3]
        E = PP * XMOLG / RM / TEMP
        return E * 1.0e-3
    
    elif KALZG == 'MOLG':
        # 分子量 [kg/kmol]
        return XMOLG
    
    elif KALZG == 'IVIS':
        # 粘度 [kg/(m·s)]
        TSTAR = TEMP / EPSK
        OMEGAV = 1.16145 / TSTAR ** 0.14874 + 0.52487 / np.exp(0.77320 * TSTAR) + 2.16178 / np.exp(2.43787 * TSTAR)
        ETA = 26.69 * np.sqrt(XMOLG * TEMP) / (SIGMA * SIGMA * OMEGAV)
        return ETA * 1.0e-7
    
    return 0.0


def FSOLID(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算固体灰分的热力学性质
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A = [10.496, 14.08]
    B = [9.277, 2.4]
    C = [-2.313, 0.0]
    D = [0.0, 0.0]
    S298, TU = 9.91, 298.15
    HMT = -911292.2
    RM = 8.3143
    
    TEMPNEU = min(TEMP, 847.0)
    
    # 修复: 接受'S'作为固体相态 (用于固体灰分焓值计算)
    if IAGG not in ['G', '    ', '', 'S']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMP_SOLID(A[0], B[0], C[0], D[0], TEMPNEU, TU)
        if TEMP > 847.0:
            E = E + CMP_SOLID(A[1], B[1], C[1], D[1], TEMP, 847.0)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT_SOLID(A[0], B[0], C[0], D[0], TEMPNEU, TU) - RM * np.log(PP / 1.01325e5)
        if TEMP > 847.0:
            E = E + CMPT_SOLID(A[1], B[1], C[1], D[1], TEMP, 847.0)
        return E
    
    return 0.0


def FH2S(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算H2S的热力学性质
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 31.8544, 3.5503e-3, 3.1474e-6, -0.8717e-9
    TU = 298.15
    HMT = -20180.4
    
    # 修复: 接受空字符串''或'    '作为固体相态
    if IAGG not in ['G', '    ', '']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMPS(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    return 0.0


def FO2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算O2的热力学性质
    
    数据来源: Knacke/Barin
    O2被视为理想气体
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 7.16, 1.0, -0.4, 0.0
    S298, TU = 205.135, 298.15
    RM = 8.3143
    XMOLG = 31.9988
    SIGMA, EPSK = 3.467, 106.7
    
    # 修复: 接受空字符串''或'    '作为固体相态
    if IAGG not in ['G', '    ', '']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = CMP(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT(A, B, C, D, TEMP, TU) - RM * np.log(PP / 1.01325e5)
        return E
    
    elif KALZG == 'IDIC':
        # 密度 [kg/m^3]
        E = PP * XMOLG / RM / TEMP
        return E * 1.0e-3
    
    elif KALZG == 'MOLG':
        # 分子量 [kg/kmol]
        return XMOLG
    
    elif KALZG == 'IVIS':
        # 粘度 [kg/(m·s)]
        TSTAR = TEMP / EPSK
        OMEGAV = 1.16145 / TSTAR ** 0.14874 + 0.52487 / np.exp(0.77320 * TSTAR) + 2.16178 / np.exp(2.43787 * TSTAR)
        ETA = 26.69 * np.sqrt(XMOLG * TEMP) / (SIGMA * SIGMA * OMEGAV)
        return ETA * 1.0e-7
    
    return 0.0


def FC(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算固体碳(C)的热力学性质
    
    数据来源: Knacke/Barin
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A = [0.026, 5.841]
    B = [9.307, 0.104]
    C = [-0.354, -7.559]
    D = [-4.155, 0.0]
    S298, TU = 5.743, 298.15
    HMT = 0.0
    RM = 8.3143
    
    TEMPNEU = min(TEMP, 1100.0)
    
    # 修复: 接受'S'作为固体相态 (用于固体碳焓值计算)
    if IAGG not in ['G', '    ', '', 'S']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMP_SOLID(A[0], B[0], C[0], D[0], TEMPNEU, TU)
        if TEMP > 1100.0:
            E = E + CMP_SOLID(A[1], B[1], C[1], D[1], TEMP, 1100.0)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT_SOLID(A[0], B[0], C[0], D[0], TEMPNEU, TU) - RM * np.log(PP / 1.01325e5)
        if TEMP > 1100.0:
            E = E + CMPT_SOLID(A[1], B[1], C[1], D[1], TEMP, 1100.0)
        return E
    
    return 0.0


def FN2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算N2的热力学性质
    
    数据来源: Knacke/Barin
    N2被视为理想气体
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 6.66, 1.02, 0.0, 0.0
    S298, TU = 191.593, 298.15
    RM = 8.3143
    XMOLG = 28.0134
    SIGMA, EPSK = 3.798, 71.4
    
    # 修复: 接受空字符串''或'    '作为固体相态
    if IAGG not in ['G', '    ', '']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = CMP(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT(A, B, C, D, TEMP, TU) - RM * np.log(PP / 1.01325e5)
        return E
    
    elif KALZG == 'IDIC':
        # 密度 [kg/m^3]
        E = PP * XMOLG / RM / TEMP
        return E * 1.0e-3
    
    elif KALZG == 'MOLG':
        # 分子量 [kg/kmol]
        return XMOLG
    
    elif KALZG == 'IVIS':
        # 粘度 [kg/(m·s)]
        TSTAR = TEMP / EPSK
        OMEGAV = 1.16145 / TSTAR ** 0.14874 + 0.52487 / np.exp(0.77320 * TSTAR) + 2.16178 / np.exp(2.43787 * TSTAR)
        ETA = 26.69 * np.sqrt(XMOLG * TEMP) / (SIGMA * SIGMA * OMEGAV)
        return ETA * 1.0e-7
    
    return 0.0


def FCO2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算CO2的热力学性质
    
    数据来源: Knacke/Barin
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 10.55, 2.16, -2.04, 0.0
    S298, TU = 213.762, 298.15
    HMT = -393693.3
    RM = 8.3143
    
    # 修复: 接受空字符串''或'    '作为固体相态
    if IAGG not in ['G', '    ', '']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMP(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT(A, B, C, D, TEMP, TU) - RM * np.log(PP / 1.01325e5)
        return E
    
    return 0.0


def FCO(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算CO的热力学性质
    
    数据来源: Knacke/Barin
    CO被视为理想气体
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 6.79, 0.98, -0.11, 0.0
    S298, TU = 197.646, 298.15
    HMT = -110594.12
    RM = 8.3143
    XMOLG = 28.0106
    SIGMA, EPSK = 3.690, 91.7
    
    # 修复: 接受空字符串''或'    '作为固体相态
    if IAGG not in ['G', '    ', '']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMP(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT(A, B, C, D, TEMP, TU) - RM * np.log(PP / 1.01325e5)
        return E
    
    elif KALZG == 'IDIC':
        # 密度 [kg/m^3]
        E = PP * XMOLG / RM / TEMP
        return E * 1.0e-3
    
    elif KALZG == 'MOLG':
        # 分子量 [kg/kmol]
        return XMOLG
    
    elif KALZG == 'IVIS':
        # 粘度 [kg/(m·s)]
        TSTAR = TEMP / EPSK
        OMEGAV = 1.16145 / TSTAR ** 0.14874 + 0.52487 / np.exp(0.77320 * TSTAR) + 2.16178 / np.exp(2.43787 * TSTAR)
        ETA = 26.69 * np.sqrt(XMOLG * TEMP) / (SIGMA * SIGMA * OMEGAV)
        return ETA * 1.0e-7
    
    return 0.0


def FCH4(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算CH4的热力学性质
    
    数据来源: Knacke/Barin
    
    Args:
        TEMP: 温度 [K]
        PP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态
        KALZG: 计算类型
        
    Returns:
        对应的热力学性质值
    """
    A, B, C, D = 2.975, 18.329, 0.346, -4.303
    S298, TU = 186.277, 298.15
    HMT = -74845.68
    RM = 8.3143
    
    # 修复: 接受空字符串''或'    '作为固体相态
    if IAGG not in ['G', '    ', '']:
        return 0.0
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMP(A, B, C, D, TEMP, TU)
        return E * 1.0e3
    
    elif KALZG == 'ENTR':
        # 熵值 [kJ/(kmol·K)]
        E = S298 + CMPT(A, B, C, D, TEMP, TU) - RM * np.log(PP / 1.01325e5)
        return E
    
    return 0.0


def FH2O(TEMP: float, PPP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算H2O的热力学性质 (Fortran 完整移植版本)
    
    使用完整的 Fortran Wasserdampftafel (水蒸气表) 实现
    基于Wg7.for中的原始Fortran代码
    
    Args:
        TEMP: 温度 [K]
        PPP: 压力 [Pa]
        X: 干度或质量分数
        IAGG: 聚集态 ('G'-气态, 'L'-液态, 'S'-固态, 'LS'/'SL'-混合)
        KALZG: 计算类型 ('ENTH'-焓, 'ENTR'-熵, 'PART'-饱和压力, 'SCHM'-熔点)
        
    Returns:
        对应的热力学性质值 [J/kmol for ENTH, kJ/(kmol·K) for ENTR]
    """
    from .fh2o_fortran import fh2o_fortran_complete as FH2O_Complete
    
    # 转换相态标识以匹配 Fortran（需要4字符宽度）
    iagg_fortran = IAGG.ljust(4)
    
    return FH2O_Complete(TEMP, PPP, X, iagg_fortran, KALZG)


def ENTHP(KOMP: int, IAGG: str, T: float, P: float) -> float:
    """
    焓值计算分发函数
    
    气体编号: 1-O2, 2-CH4, 3-CO, 4-CO2, 5-H2S, 6-H2, 7-N2, 8-H2O
              9-C(碳), 10-ASH(灰分)
    
    Args:
        KOMP: 组分编号 (1-10)
        IAGG: 聚集态
        T: 温度 [K]
        P: 压力 [Pa]
        
    Returns:
        比焓值 [J/kmol] 或 [J/kg]
    """
    XMC, XSIO2 = 12.00, 60.0
    
    if KOMP == 1:
        return FO2(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 2:
        return FCH4(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 3:
        return FCO(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 4:
        return FCO2(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 5:
        return FH2S(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 6:
        return FH2(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 7:
        return FN2(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 8:
        return FH2O(T, P, -1.0, IAGG, 'ENTH')
    elif KOMP == 9:
        # 碳的焓值需要除以分子量转换为J/kg
        return FC(T, P, -1.0, IAGG, 'ENTH') / XMC
    elif KOMP == 10:
        # 灰分的焓值需要除以分子量转换为J/kg
        return FSOLID(T, P, -1.0, IAGG, 'ENTH') / XSIO2
    
    return 0.0


def ENTHP_DELTA(KOMP: int, IAGG: str, T: float, T_REF: float, P: float) -> float:
    """
    计算相对于参考温度的焓值差
    
    用于能量方程中的固体项，Fortran可能使用焓值差而非绝对焓值
    
    Args:
        KOMP: 组分编号 (1-10)
        IAGG: 聚集态
        T: 当前温度 [K]
        T_REF: 参考温度 [K]
        P: 压力 [Pa]
        
    Returns:
        焓值差 [J/kmol] 或 [J/kg]
    """
    return ENTHP(KOMP, IAGG, T, P) - ENTHP(KOMP, IAGG, T_REF, P)


# ============================================================================
# 传热系数函数
# ============================================================================

def WDKR(T: float, TW: float) -> float:
    """
    计算辐射换热系数
    
    Args:
        T: 气体温度 [K]
        TW: 壁面温度 [K]
        
    Returns:
        辐射换热系数 [W/(m^2·K)]
    """
    TM = (TW + T) / 2.0
    CS = 5.672e-8  # Stefan-Boltzmann常数 [W/(m^2·K^4)]
    ESURF = 0.78   # 表面发射率
    ESURP = 0.78   # 颗粒发射率
    
    ALPHAR = CS * (T ** 4 - TW ** 4) / (1.0 / ESURF + 1.0 / ESURP - 1.0) / (T - TW)
    
    return ALPHAR


def FXMUG(Y_array: np.ndarray, T: float) -> float:
    """
    计算气体混合物粘度
    
    基于各组分粘度和摩尔分数计算混合物粘度
    
    Args:
        Y_array: 各组分摩尔分数数组 (1-based, 长度9)
        T: 温度 [K]
        
    Returns:
        混合物粘度 [Pa·s]
    """
    G = 9.81
    T0 = 273.15
    
    # 分子量 [kg/kmol]
    XMOLE_WEIGHT = np.array([0.0, 31.999, 58.124, 28.010, 44.010, 34.080, 2.016, 28.013, 18.015, 16.043])
    
    # 各组分粘度系数 (需要乘以G)
    XMUG_coef = np.array([0.0, 1.98e-6, 0.697e-6, 1.69e-6, 1.43e-6, 1.194e-6, 0.852e-6, 1.70e-6, 0.84e-6, 1.06e-6])
    XMUG_power = np.array([0.0, 0.693, 0.97, 0.695, 0.820, 0.986, 0.678, 0.680, 1.200, 0.760])
    
    # 计算各组分粘度
    XMUG = np.zeros(10)
    for I in range(1, 10):
        XMUG[I] = G * XMUG_coef[I] * (T / T0) ** XMUG_power[I]
    
    # 计算相互作用系数 A(I,J)
    A = np.zeros((10, 10))
    for I in range(1, 10):
        for J in range(1, 10):
            A[I, J] = (1.0 + (XMUG[I] / XMUG[J]) ** 0.5 * 
                      (XMOLE_WEIGHT[J] / XMOLE_WEIGHT[I]) ** 0.25) ** 2.0 / np.sqrt(8.0 * (1.0 + XMOLE_WEIGHT[I] / XMOLE_WEIGHT[J]))
    
    # 计算 B(I)
    B = np.zeros(10)
    for I in range(1, 10):
        B[I] = 0.0
        for J in range(1, 10):
            B[I] = B[I] + Y_array[J] * A[I, J]
        B[I] = Y_array[I] / B[I]
    
    # 计算混合物粘度
    FXMUG_result = 0.0
    for I in range(1, 10):
        FXMUG_result = FXMUG_result + B[I] * XMUG[I]
    
    return FXMUG_result


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEXACO气化炉反应速率模块测试")
    print("=" * 60)
    
    # 设置一些测试数据
    common.T[0] = 1800.0  # 温度 [K]
    common.PWK = 40.83e5  # 压力 [Pa]
    common.XMS[0] = 1.0   # 固体质量 [kg]
    common.ROS[0] = 1000.0  # 固体密度 [kg/m^3]
    common.X[0] = 0.5     # 碳转化率
    common.DP = 100.0e-6  # 颗粒直径 [m]
    common.FEM[0] = 1.0   # 总摩尔流量 [kmol/s]
    
    # 设置气体组分流量
    common.FEMF[1, 0] = 0.1  # O2
    common.FEMF[2, 0] = 0.05  # CH4
    common.FEMF[3, 0] = 0.3  # CO
    common.FEMF[4, 0] = 0.1  # CO2
    common.FEMF[5, 0] = 0.02  # H2S
    common.FEMF[6, 0] = 0.2  # H2
    common.FEMF[7, 0] = 0.15  # N2
    common.FEMF[8, 0] = 0.08  # H2O
    
    print("\n--- 测试结构参数 PHI ---")
    phi_val = PHI(0)
    print(f"PHI(0) = {phi_val:.6f}")
    
    print("\n--- 测试反应速率系数 XKC ---")
    print(f"XKC_O2(0)  = {XKC_O2(0):.6e} kmol/(m^2·Pa·s)")
    print(f"XKC_H2O(0) = {XKC_H2O(0):.6e} kmol/(m^2·Pa·s)")
    print(f"XKC_CO2(0) = {XKC_CO2(0):.6e} kmol/(m^2·Pa·s)")
    print(f"XKC_H2(0)  = {XKC_H2(0):.6e} kmol/(m^2·Pa·s)")
    
    print("\n--- 测试碳反应速率 A1-A5 ---")
    print(f"A1(0) = {A1(0):.6e} kmol/s")
    print(f"A2(0) = {A2(0):.6e} kmol/s")
    print(f"A3(0) = {A3(0):.6e} kmol/s")
    print(f"A4(0) = {A4(0):.6e} kmol/s")
    print(f"A5(0) = {A5(0):.6e} kmol/s")
    
    print("\n--- 测试总反应速率 RI ---")
    print(f"RI(0) = {RI(0):.6e} kg/s")
    
    print("\n--- 测试热力学性质 ---")
    print(f"FO2(1000K, 40.83e5Pa, 'ENTH')  = {FO2(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    print(f"FN2(1000K, 40.83e5Pa, 'ENTH')  = {FN2(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    print(f"FCO(1000K, 40.83e5Pa, 'ENTH')  = {FCO(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    print(f"FCO2(1000K, 40.83e5Pa, 'ENTH') = {FCO2(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    print(f"FCH4(1000K, 40.83e5Pa, 'ENTH') = {FCH4(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    print(f"FH2(1000K, 40.83e5Pa, 'ENTH')  = {FH2(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    print(f"FH2O(1000K, 40.83e5Pa, 'ENTH') = {FH2O(1000.0, 40.83e5, -1.0, 'G', 'ENTH'):.2f} J/kmol")
    
    print("\n--- 测试ENTHP函数 ---")
    print(f"ENTHP(1, 'G', 1000K, 40.83e5Pa) = {ENTHP(1, 'G', 1000.0, 40.83e5):.2f} J/kmol")
    print(f"ENTHP(3, 'G', 1000K, 40.83e5Pa) = {ENTHP(3, 'G', 1000.0, 40.83e5):.2f} J/kmol")
    
    print("\n--- 测试传热系数 ---")
    print(f"WDKR(1800K, 3300K) = {WDKR(1800.0, 3300.0):.6f} W/(m^2·K)")
    
    print("\n--- 测试混合物粘度 ---")
    Y_test = np.zeros(10)
    Y_test[1:9] = common.FEMF[1:9, 0] / common.FEM[0]
    print(f"FXMUG(Y, 1000K) = {FXMUG(Y_test, 1000.0):.6e} Pa·s")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
