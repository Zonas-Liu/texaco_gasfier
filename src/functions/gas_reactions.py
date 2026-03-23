#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 气相反应速率模块
对应Fortran的Wg6.for

包含以下气相反应速率计算:
- XK1: CO + 1/2 O2 -> CO2
- XK2: H2 + 1/2 O2 -> H2O
- XK3: CO + H2O -> CO2 + H2 (水煤气变换)
- XK4: CO2 + H2 -> CO + H2O (逆水煤气变换)
- XK5: CH4 + H2O -> CO + 3H2 (蒸汽重整)
- XK6: CH4 + 2 O2 -> CO2 + 2H2O

以及挥发分释放子程序 FLUCHT
"""
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.common_data import common


def xk1(i):
    """
    CO + 1/2 O2 -> CO2 反应速率
    
    参数:
        i: 格子索引 (1-based)
    
    返回:
        xk1: 反应速率 [kmol/s]
    
    公式:
        XK10 = 3.09E8 * exp(-9.976E7/(RAG*T(I))) * (PWK/(RAG*T(I)))**2
             * AT(I)*DELZ(I)
        XK1 = XK10 * Y(1) * Y(3) * KTRL_XK1
    
    其中:
        Y(1) = O2 摩尔分数
        Y(3) = CO 摩尔分数
    
    Reference: CEN KEFA AND ZHAO LI
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物是否存在
    if common.Y[1] < 1.0e-10 or common.Y[3] < 1.0e-10:
        return 0.0
    
    # 计算反应速率
    # 防溢出保护：确保指数参数在有效范围内
    exp_arg = -9.976e7 / (common.RAG * common.T[i])
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    xk10 = (3.09e8 * np.exp(exp_arg)
            * (common.PWK / (common.RAG * common.T[i])) ** 2
            * common.AT[i] * common.DELZ[i])
    
    xk1_result = xk10 * common.Y[1] * common.Y[3] * common.KTRL_XK1
    
    return xk1_result


def xk2(i):
    """
    H2 + 1/2 O2 -> H2O 反应速率
    
    参数:
        i: 格子索引 (1-based)
    
    返回:
        xk2: 反应速率 [kmol/s]
    
    公式:
        XK20 = 8.83E8 * exp(-9.976E7/(RAG*T(I)))
               * AT(I)*DELZ(I) * (PWK/(RAG*T(I)))**2
        XK2 = XK20 * Y(1) * Y(6) * KTRL_XK2
    
    其中:
        Y(1) = O2 摩尔分数
        Y(6) = H2 摩尔分数
    
    Reference: ZHAO LI AND CEN KEFA
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物是否存在
    if common.Y[1] < 1.0e-10 or common.Y[6] < 1.0e-10:
        return 0.0
    
    # 计算反应速率
    # 防溢出保护
    exp_arg = -9.976e7 / (common.RAG * common.T[i])
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    xk20 = (8.83e8 * np.exp(exp_arg)
            * common.AT[i] * common.DELZ[i]
            * (common.PWK / (common.RAG * common.T[i])) ** 2)
    
    xk2_result = xk20 * common.Y[1] * common.Y[6] * common.KTRL_XK2
    
    return xk2_result


def xk3(i):
    """
    CO + H2O -> CO2 + H2 水煤气变换反应速率
    
    参数:
        i: 格子索引 (1-based)
    
    返回:
        xk3: 反应速率 [kmol/s]
    
    公式:
        XK30 = 2.978E12 * exp(-3.69E8/(RAG*T(I)))
               * AT(I)*DELZ(I) * (PWK/(RAG*T(I)))**2
        XK3 = XK30 * Y(3) * Y(8) * KTRL_XK3
    
    其中:
        Y(3) = CO 摩尔分数
        Y(8) = H2O 摩尔分数
    
    Reference: CEN KEFA AND ZHAO LI
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物是否存在
    if common.Y[3] < 0.0 or common.Y[8] < 0.0:
        return 0.0
    
    # 计算反应速率
    # 防溢出保护
    exp_arg = -3.69e8 / (common.RAG * common.T[i])
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    xk30 = (2.978e12 * np.exp(exp_arg)
            * common.AT[i] * common.DELZ[i]
            * (common.PWK / (common.RAG * common.T[i])) ** 2)
    
    xk3_result = xk30 * common.Y[3] * common.Y[8] * common.KTRL_XK3
    
    return xk3_result


def xk4(i):
    """
    CO2 + H2 -> CO + H2O 逆水煤气变换反应速率
    
    参数:
        i: 格子索引 (1-based)
    
    返回:
        xk4: 反应速率 [kmol/s]
    
    公式:
        XK40 = 0.215 * 6.245E14 * exp(-3.983E8/(RAG*T(I)))
               * AT(I)*DELZ(I) * (PWK/(RAG*T(I)))**2
        XK4 = XK40 * Y(4) * Y(6) * KTRL_XK4
    
    其中:
        Y(4) = CO2 摩尔分数
        Y(6) = H2 摩尔分数
    
    Reference: CEN KEFA (6.245E14), ZHAO LI (7.145E14)
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 计算反应速率
    # 防溢出保护
    exp_arg = -3.983e8 / (common.RAG * common.T[i])
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    xk40 = (0.215 * 6.245e14 * np.exp(exp_arg)
            * common.AT[i] * common.DELZ[i]
            * (common.PWK / (common.RAG * common.T[i])) ** 2)
    
    xk4_result = xk40 * common.Y[4] * common.Y[6] * common.KTRL_XK4
    
    return xk4_result


def xk5(i):
    """
    CH4 + H2O -> CO + 3H2 蒸汽重整反应速率
    
    参数:
        i: 格子索引 (1-based)
    
    返回:
        xk5: 反应速率 [kmol/s]
    
    公式:
        XK50 = 312.0 * exp(-3.0E4/(1.987*T(I)))
               * AT(I)*DELZ(I) * (PWK/(RAG*T(I)))
        XK5 = XK50 * Y(2) * KTRL_XK5
    
    其中:
        Y(2) = CH4 摩尔分数
    
    Reference: WEN
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物是否存在
    if common.Y[2] < 1.0e-10:
        return 0.0 * common.KTRL_XK5
    
    # 计算反应速率
    # 防溢出保护
    exp_arg = -3.0e4 / (1.987 * common.T[i])
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    xk50 = (312.0 * np.exp(exp_arg)
            * common.AT[i] * common.DELZ[i]
            * (common.PWK / (common.RAG * common.T[i])))
    
    xk5_result = xk50 * common.Y[2] * common.KTRL_XK5
    
    return xk5_result


def xk6(i):
    """
    CH4 + 2 O2 -> CO2 + 2H2O 反应速率
    
    参数:
        i: 格子索引 (1-based)
    
    返回:
        xk6: 反应速率 [kmol/s]
    
    公式:
        XK60 = 3.552E14 * exp(-9.304E8/(RAG*T(I)))
               * (PWK/(RAG*T(I)))**2 * AT(I)*DELZ(I)
        XK6 = XK60 * Y(1) * Y(2)
    
    其中:
        Y(1) = O2 摩尔分数
        Y(2) = CH4 摩尔分数
    
    Reference: CEN KEFA P320
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物是否存在
    if common.Y[1] < 0.0001 or common.Y[2] < 0.0001:
        return 0.0
    
    # 计算反应速率
    # 防溢出保护
    exp_arg = -9.304e8 / (common.RAG * common.T[i])
    if exp_arg < -700:
        exp_arg = -700
    elif exp_arg > 700:
        exp_arg = 700
    xk60 = (3.552e14 * np.exp(exp_arg)
            * (common.PWK / (common.RAG * common.T[i])) ** 2
            * common.AT[i] * common.DELZ[i])
    
    xk6_result = xk60 * common.Y[1] * common.Y[2]
    
    return xk6_result


def flucht():
    """
    挥发分释放计算子程序
    
    计算煤热解过程中挥发分各组分的释放速率和相关参数。
    包括CH4, CO, CO2, H2, H2O, TAR, H2S, N2等的释放量计算。
    
    主要功能:
    1. 初始化挥发分释放系数(XOCH4, XOH2, XOCO等)
    2. 根据煤的工业分析和元素分析计算各挥发分组分
    3. 处理H和O元素的平衡
    4. 计算各格子中的挥发分释放速率
    """
    # 初始化挥发分释放系数
    # XOCH4: 1摩尔CH4完全燃烧所需O2摩尔数
    common.XOCH4 = 2.0
    # XOH2: 1摩尔H2完全燃烧所需O2摩尔数
    common.XOH2 = 0.5
    # XOCO: 1摩尔CO完全燃烧所需O2摩尔数
    common.XOCO = 0.5
    # XHOCH: 1摩尔CH4完全燃烧生成H2O的摩尔数
    common.XHOCH = 2.0
    # XHOH2: 1摩尔H2完全燃烧生成H2O的摩尔数
    common.XHOH2 = 1.0
    # XCOCH: 1摩尔CH4完全燃烧生成CO2的摩尔数
    common.XCOCH = 1.0
    # XOTAR: 1摩尔TAR完全燃烧所需O2摩尔数
    common.XOTAR = 1.16525
    # XCTAR_CO: 1摩尔TAR/CO完全燃烧生成CO2的摩尔数
    common.XCTAR_CO = 1.0
    # XHTAR: 1摩尔TAR完全燃烧生成H2O的摩尔数
    common.XHTAR = 0.3445
    
    # 如果是检查模式,将所有系数设为0
    if common.KCHECK == 1:
        common.XOCO = 0.0
        common.XHOCH = 0.0
        common.XHOH2 = 0.0
        common.XCOCH = 0.0
        common.XOTAR = 0.0
        common.XCTAR_CO = 0.0
        common.XHTAR = 0.0
        common.XOCH4 = 0.0
        common.XOH2 = 0.0
    
    # 初始化各格子挥发分释放速率为0
    for i in range(common.NZEL1, common.NZEL2 + 1):
        common.RCO2[i] = 0.0    # CO2释放速率 [kmol/s]
        common.RCO[i] = 0.0     # CO释放速率 [kmol/s]
        common.RVH2[i] = 0.0    # H2释放速率 [kmol/s]
        common.RVH2O[i] = 0.0   # H2O释放速率 [kmol/s]
        common.RVCH4[i] = 0.0   # CH4释放速率 [kmol/s]
        common.RVTAR[i] = 0.0   # TAR释放速率 [kmol/s]
        common.RH2[i] = 0.0     # H2释放(另一种) [kmol/s]
        common.RO2[i] = 0.0     # O2释放 [kmol/s]
        common.REN2[i] = 0.0    # N2释放 [kmol/s]
        common.RH2S[i] = 0.0    # H2S释放 [kmol/s]
    
    # 限制挥发分含量上限
    if common.XVM > 0.5166:
        common.XVM = 0.5166
    
    # 计算各元素在1kg煤中的含量 [kg/kg coal]
    fak = 1.0
    prc = fak * common.ELC     # C元素含量
    prn = fak * common.ELN     # N元素含量
    prs = fak * common.ELS     # S元素含量
    prh = fak * common.ELH     # H元素含量
    pro = fak * common.ELO     # O元素含量
    
    # 计算总释放量(假设所有元素都以特定形式释放)
    rh2s_total = prs * common.BSMS / 32.0    # 总H2S释放量 [kmol/s]
    ren2_total = prn * common.BSMS / 28.0    # 总N2释放量 [kmol/s]
    rh2_total = prh * common.BSMS / 2.0      # 总H2释放量 [kmol/s]
    ro2_total = pro * common.BSMS / 32.0     # 总O2释放量 [kmol/s]
    
    # 如果没有挥发分,跳转到902
    if common.XVM == 0.0:
        _flucht_902(rh2s_total, ren2_total, rh2_total, ro2_total, prc, prn, prs, prh, pro)
        return
    
    # 根据挥发分含量计算各组分释放量(基于关联式)
    # RVCH41: CH4释放量 [kmol/s]
    rvch41 = ((0.201 - 0.469 * common.XVM + 0.261 * common.XVM ** 2)
              * common.XVM * common.BSWAF / 16.0)
    
    # RVTAR1: TAR释放量 [kmol/s]
    rvtar1 = ((-0.325 + 7.279 * common.XVM - 12.88 * common.XVM ** 2)
              * common.XVM * common.BSWAF / 12.913)
    
    # RVH21: H2释放量 [kmol/s]
    rvh21 = ((0.157 - 0.868 * common.XVM + 1.388 * common.XVM ** 2)
             * common.XVM * common.BSWAF / 2.0)
    
    # RCO21: CO2释放量 [kmol/s]
    rco21 = ((0.13 - 0.9 * common.XVM + 1.906 * common.XVM ** 2)
             * common.XVM * common.BSWAF / 44.0)
    
    # RCO1: CO释放量 [kmol/s]
    rco1 = ((0.428 - 2.653 * common.XVM + 4.845 * common.XVM ** 2)
            * common.XVM * common.BSWAF / 28.0)
    
    # RVH2O1: H2O释放量 [kmol/s]
    rvh2o1 = ((0.409 - 2.389 * common.XVM + 4.5 * common.XVM ** 2)
              * common.XVM * common.BSWAF / 18.0)
    
    # 计算剩余H和O元素
    # RH2_RE: 剩余H元素(转换为H2) [kmol/s]
    rh2_re = rh2_total - 2.0 * rvch41 - rvh21 - rvh2o1 - 0.3445 * rvtar1 - rh2s_total
    
    # RO2_RE: 剩余O元素(转换为O2) [kmol/s]
    ro2_re = ro2_total - rco21 - 0.5 * (rco1 + rvh2o1) - 0.007 * rvtar1
    
    # 计算挥发分释放所需O和H总量
    fak1 = rco21 + 0.5 * rco1 + 0.5 * rvh2o1 + 0.007 * rvtar1  # 所需O2
    fak2 = rvh21 + rvh2o1 + 2.0 * rvch41 + 0.3445 * rvtar1      # 所需H2
    fak3 = rvh21 + 2.0 * rvch41                                  # H2和CH4所需
    fak4 = rco21 + 0.5 * rco1                                    # CO2和CO所需
    
    # 根据H和O元素平衡条件进行分支处理
    if rh2_re >= 0.0:
        # H元素有剩余
        if ro2_re >= 0.0:
            # O元素也有剩余,跳转到901
            rvch4k, rvh2k, rvh2ok, rcok, rco2k, rvtark = _flucht_901(
                rvch41, rvh21, rvh2o1, rco1, rco21, rvtar1
            )
        else:
            # O元素不足,H元素剩余
            rvch4k = rvch41
            rvh2k = rvh21
            rvh2ok = ro2_total * rvh2o1 / fak1
            rcok = ro2_total * rco1 / fak1
            rco2k = ro2_total * rco21 / fak1
            rvtark = ro2_total * rvtar1 / fak1
    else:
        # H元素不足
        if ro2_re >= 0.0:
            # O元素有剩余
            rcok = rco1
            rco2k = rco21
            rvh2ok = (rh2_total - rh2s_total) * rvh2o1 / fak2
            rvh2k = (rh2_total - rh2s_total) * rvh21 / fak2
            rvch4k = (rh2_total - rh2s_total) * rvch41 / fak2
            rvtark = (rh2_total - rh2s_total) * rvtar1 / fak2
        else:
            # H和O元素都不足
            vh2ok1 = (rh2_total - rh2s_total) * rvh2o1 / fak2
            vh2ok2 = ro2_total * rvh2o1 / fak1
            vtark1 = (rh2_total - rh2s_total) * rvtar1 / fak2
            vtark2 = ro2_total * rvtar1 / fak1
            
            rvch4k, rvh2k, rvh2ok, rcok, rco2k, rvtark = _flucht_balance_h_o(
                vh2ok1, vh2ok2, vtark1, vtark2, rvh2o1, rvtar1, rco1, rco21,
                rvch41, rvh21, rh2_total, rh2s_total, ro2_total, fak1, fak2, fak3, fak4
            )
    
    # 更新变量
    rvch41 = rvch4k
    rvh21 = rvh2k
    rvh2o1 = rvh2ok
    rco1 = rcok
    rvtar1 = rvtark
    rco21 = rco2k
    
    # 计算各格子中的释放速率
    _flucht_distribute(
        rvch41, rvh21, rvh2o1, rco1, rco21, rvtar1,
        rh2s_total, ren2_total, rh2_total, ro2_total,
        prc, prh, pro, prn, prs
    )


def _flucht_balance_h_o(vh2ok1, vh2ok2, vtark1, vtark2, rvh2o1, rvtar1, rco1, rco21,
                        rvch41, rvh21, rh2_total, rh2s_total, ro2_total, fak1, fak2, fak3, fak4):
    """
    H和O元素都不足时的平衡计算
    """
    if vh2ok1 >= vh2ok2 and vtark1 >= vtark2:
        rvh2ok = vh2ok2
        rvtark = vtark2
        rcok = ro2_total * rco1 / fak1
        rco2k = ro2_total * rco21 / fak1
        rh2_re = rh2_total - rh2s_total - rvh2ok - rvh21 - 2.0 * rvch41 - 0.3445 * rvtark
        
        if rh2_re >= 0.0:
            rvh2k = rvh21
            rvch4k = rvch41
        else:
            rvh2k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvh21 / fak3
            rvch4k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvch41 / fak3
    
    elif vh2ok1 >= vh2ok2 and vtark1 < vtark2:
        rvh2ok = vh2ok2
        rvtark = vtark1
        rh2_re = rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark - 2.0 * rvch41 - rvh21
        ro2_re = ro2_total - 0.5 * rvh2ok - 0.007 * rvtark - 0.5 * rco1 - rco21
        
        if rh2_re >= 0.0:
            if ro2_re >= 0.0:
                rvh2k = rvh21
                rvch4k = rvch41
                rcok = rco1
                rco2k = rco21
            else:
                rvh2k = rvh21
                rvch4k = rvch41
                rcok = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco1 / fak4
                rco2k = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco21 / fak4
        else:
            if ro2_re >= 0.0:
                rcok = rco1
                rco2k = rco21
                rvch4k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvch41 / fak3
                rvh2k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvh21 / fak3
            else:
                rcok = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco1 / fak4
                rco2k = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco21 / fak4
                rvch4k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvch41 / fak3
                rvh2k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvh21 / fak3
    
    elif vh2ok1 < vh2ok2 and vtark1 >= vtark2:
        rvh2ok = vh2ok1
        rvtark = vtark1
        # 继续处理
        rh2_re = rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark - 2.0 * rvch41 - rvh21
        ro2_re = ro2_total - 0.5 * rvh2ok - 0.007 * rvtark - 0.5 * rco1 - rco21
        
        if rh2_re >= 0.0:
            if ro2_re >= 0.0:
                rvh2k = rvh21
                rvch4k = rvch41
                rcok = rco1
                rco2k = rco21
            else:
                rvh2k = rvh21
                rvch4k = rvch41
                rcok = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco1 / fak4
                rco2k = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco21 / fak4
        else:
            if ro2_re >= 0.0:
                rcok = rco1
                rco2k = rco21
                rvch4k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvch41 / fak3
                rvh2k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvh21 / fak3
            else:
                rcok = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco1 / fak4
                rco2k = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco21 / fak4
                rvch4k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvch41 / fak3
                rvh2k = (rh2_total - rh2s_total - rvh2ok - 0.3445 * rvtark) * rvh21 / fak3
    
    else:
        rvh2ok = vh2ok1
        rvtark = vtark2
        rvh2k = (rh2_total - rh2s_total) * rvh21 / fak2
        rvch4k = (rh2_total - rh2s_total) * rvch41 / fak2
        ro2_re = ro2_total - 0.5 * rvh2ok - 0.007 * rvtark - 0.5 * rco1 - rco21
        
        if ro2_re >= 0.0:
            rcok = rco1
            rco2k = rco21
        else:
            rcok = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco1 / fak4
            rco2k = (ro2_total - 0.5 * rvh2ok - 0.007 * rvtark) * rco21 / fak4
    
    return rvch4k, rvh2k, rvh2ok, rcok, rco2k, rvtark


def _flucht_901(rvch41, rvh21, rvh2o1, rco1, rco21, rvtar1):
    """
    H和O元素都有剩余时的处理
    """
    rvch4k = rvch41
    rvh2k = rvh21
    rvh2ok = rvh2o1
    rcok = rco1
    rco2k = rco21
    rvtark = rvtar1
    return rvch4k, rvh2k, rvh2ok, rcok, rco2k, rvtark


def _flucht_902(rh2s_total, ren2_total, rh2_total, ro2_total, prc, prh, pro, prn, prs):
    """
    无挥发分时的处理 - 只计算元素释放
    """
    # 计算各格子中的释放速率
    for i in range(common.NZRA, common.NZFR + 1):
        common.RH2[i] = (prh * common.BSMS / 2.0) * common.DELZ[i] / common.HNZFR
        common.RO2[i] = (pro * common.BSMS / 32.0) * common.DELZ[i] / common.HNZFR
        common.REN2[i] = (prn * common.BSMS / 28.0) * common.DELZ[i] / common.HNZFR
        common.RH2S[i] = (prs * common.BSMS / 32.0) * common.DELZ[i] / common.HNZFR
    
    # 计算固定碳分布
    sum_wfc = 0.0
    for i in range(common.NZRA, common.NZFED + 1):
        common.WFC[i] = (prc * common.BSMS) / (common.NZFED - common.NZRA + 1)
        sum_wfc += common.WFC[i]
    
    # 挥发分总转化率和碳含量
    common.XCVM0 = 0.0
    common.XC0 = sum_wfc / (sum_wfc + common.BSMS * common.ELAS)


def _flucht_distribute(rvch41, rvh21, rvh2o1, rco1, rco21, rvtar1,
                       rh2s_total, ren2_total, rh2_total, ro2_total,
                       prc, prh, pro, prn, prs):
    """
    将挥发分释放分配到各格子
    """
    # 计算元素释放速率
    for i in range(common.NZRA, common.NZFR + 1):
        common.RH2[i] = (prh * common.BSMS / 2.0 - (2.0 * rvch41 + rvh21 + rvh2o1 + rh2s_total
                                                  + 0.3445 * rvtar1)) * common.DELZ[i] / common.HNZFR
        common.RO2[i] = (pro * common.BSMS / 32.0 - (0.5 * (rco1 + rvh2o1) + 0.007
                                                   * rvtar1 + rco21)) * common.DELZ[i] / common.HNZFR
        common.REN2[i] = prn * common.BSMS / 28.0 * common.DELZ[i] / common.HNZFR
        common.RH2S[i] = prs * common.BSMS / 32.0 * common.DELZ[i] / common.HNZFR
    
    # 计算固定碳质量流量分布
    sum_wfc = 0.0
    for i in range(common.NZRA, common.NZFED + 1):
        common.WFC[i] = (prc * common.BSMS - 12.0 * (rco1 + rco21 + rvch41) - 12.0 * rvtar1) / (common.NZFED - common.NZRA + 1)
        sum_wfc += common.WFC[i]
    
    # 计算挥发分释放速率分布
    for i in range(common.NZRA, common.NZFR + 1):
        common.RVCH4[i] = rvch41 * common.DELZ[i] / common.HNZFR
        common.RVH2[i] = rvh21 * common.DELZ[i] / common.HNZFR
        common.RVH2O[i] = rvh2o1 * common.DELZ[i] / common.HNZFR
        common.RCO[i] = rco1 * common.DELZ[i] / common.HNZFR
        common.RCO2[i] = rco21 * common.DELZ[i] / common.HNZFR
        common.RVTAR[i] = rvtar1 * common.DELZ[i] / common.HNZFR
    
    # 计算总挥发分转化率
    vm0 = 0.0
    for i in range(common.NZRA, common.NZRE + 1):
        vm0 += (common.RVCH4[i] * 16.0 + common.RVH2[i] * 2.0 + common.RVH2O[i] * 18.0
                + common.RCO[i] * 28.0 + common.RCO2[i] * 44.0 + common.RVTAR[i] * 12.913
                + common.RH2[i] * 2.0 + common.RO2[i] * 32.0 + common.REN2[i] * 28.0
                + common.RH2S[i] * 34.0)
    
    # 挥发分转化率和碳含量
    common.XCVM0 = vm0 / common.BSWAF
    common.XC0 = sum_wfc / (sum_wfc + common.BSMS * common.ELAS)
