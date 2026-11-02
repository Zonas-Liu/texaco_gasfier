#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - GASIFIER子程序Python实现
对应Fortran文件: Wg3.for

功能: 主计算子程序，构建块三对角矩阵系统的系数矩阵(AMAT, BMAT, CMAT)和右端向量(DMAT)
"""

import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.common_data import common

def _calculate_dmat_for_cell(
    i,
    xmass_func,
    entfed_func,
    entkol_func,
    xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func,
    a1_func, a2_func, a3_func, a4_func, a5_func,
    phi_func, ri_func,
    enthp_func,
    wdkr_func=None
):
    """
    计算单个网格单元的DMAT（右端向量RHS）
    
    对应Fortran中标签53开始的DMAT计算部分
    提取为辅助函数以便在数值微分中重复调用
    
    参数:
        i: 当前网格单元索引
        其他参数: 各种物理计算函数
    
    返回:
        rri: 总反应速率RI(I)（用于保存RAC[i]）
    """
    # ============================================================
    # 2. 计算总摩尔流量FEM(I)和气体速度U0(I)
    # ============================================================
    common.FEM[i] = 0.0
    for j in range(1, common.NGAS + 1):
        common.FEM[i] += common.FEMF[j, i]
    
    # 计算气体速度U0 (对所有单元格)
    active = slice(common.NZRA, common.NZRE + 1)
    common.U0[active] = common.FEM[active] * common.RAG * common.T[active] / (common.PWK * common.AT[active])
    
    # 计算组分摩尔分数Y(J)
    for j in range(1, common.NGAS + 1):
        if common.FEM[i] > 0:
            common.Y[j] = common.FEMF[j, i] / common.FEM[i]
        else:
            common.Y[j] = 0.0
    
    # ============================================================
    # 3. 调用其他子程序
    # ============================================================
    xmass_func()
    entfed_func()
    entkol_func()
    
    # ============================================================
    # 4. 计算反应速率
    # ============================================================
    if common.KTRLR == 1:
        # 气相反应速率 XK1-XK6
        rxk1 = xk1_func(i)
        rxk2 = xk2_func(i)
        rxk3 = xk3_func(i)
        rxk4 = xk4_func(i)
        rxk5 = xk5_func(i)
        rxk6 = xk6_func(i)
        
        # 碳反应速率 A1-A5
        ra1 = a1_func(i)
        ra2 = a2_func(i)
        ra3 = a3_func(i)
        ra4 = a4_func(i)
        ra5 = a5_func(i)
        
        # 总反应速率
        rri = ri_func(i)
    else:
        rxk1 = 0.0
        rxk2 = 0.0
        rxk3 = 0.0
        rxk4 = 0.0
        rxk5 = 0.0
        rxk6 = 0.0
        
        ra1 = 0.0
        ra2 = 0.0
        ra3 = 0.0
        ra4 = 0.0
        ra5 = 0.0
        rri = 0.0
    
    # 计算PHI参数
    rphi = phi_func(i)
    
    # ============================================================
    # 5. 构建DMAT (右端向量RHS)
    # ============================================================
    
    # ---------------------------------------------------------
    # DMAT(1,I): O2平衡方程
    # ---------------------------------------------------------
    # O2来源: 挥发分释放 + 进料 + 上游单元格流入
    # O2消耗: 流出 + 各种反应消耗
    common.DMAT[1, i] = common.RO2[i] + common.FEEDO2[i]
    if i != common.NZRA:
        common.DMAT[1, i] += common.FEMF[1, i - 1]
    common.DMAT[1, i] -= common.FEMF[1, i]
    
    # 挥发分燃烧消耗的O2 (部分项被注释掉)
    common.DMAT[1, i] -= (
        0.0 * common.XOCH4 * common.RVCH4[i] +
        0.0 * common.XOH2 * (common.RH2[i] + common.RVH2[i]) +
        0.0 * common.XOCO * common.RCO[i] +
        common.XOTAR * common.RVTAR[i]
    )
    
    # 气相反应消耗的O2
    common.DMAT[1, i] -= rxk1 / 2.0
    common.DMAT[1, i] -= rxk2 / 2.0
    common.DMAT[1, i] -= rxk6 * 2.0
    
    # 碳反应消耗的O2 (C + O2 -> CO + CO2)
    common.DMAT[1, i] -= ra3 / rphi
    
    # ---------------------------------------------------------
    # DMAT(2,I): CH4平衡方程
    # ---------------------------------------------------------
    common.DMAT[2, i] = common.RVCH4[i] + common.KCHECK * common.RVCH4[i]
    if i != common.NZRA:
        common.DMAT[2, i] += common.FEMF[2, i - 1]
    common.DMAT[2, i] -= common.FEMF[2, i]
    
    # 气相反应消耗的CH4
    common.DMAT[2, i] -= rxk5
    common.DMAT[2, i] -= rxk6
    
    # 碳反应产生的CH4 (C + 2H2 -> CH4)
    common.DMAT[2, i] += ra2
    
    # ---------------------------------------------------------
    # DMAT(3,I): CO平衡方程
    # ---------------------------------------------------------
    common.DMAT[3, i] = common.RCO[i] + common.KCHECK * common.RCO[i]
    if i != common.NZRA:
        common.DMAT[3, i] += common.FEMF[3, i - 1]
    common.DMAT[3, i] -= common.FEMF[3, i]
    
    # 气相反应对CO的影响
    common.DMAT[3, i] -= rxk1
    common.DMAT[3, i] -= rxk3
    common.DMAT[3, i] += rxk4
    common.DMAT[3, i] += rxk5
    
    # 碳反应对CO的影响
    common.DMAT[3, i] += ra1
    common.DMAT[3, i] += ra3 * (2.0 - 2.0 / rphi)
    common.DMAT[3, i] += ra4 * 2.0
    common.DMAT[3, i] -= ra5
    
    # ---------------------------------------------------------
    # DMAT(4,I): CO2平衡方程
    # ---------------------------------------------------------
    common.DMAT[4, i] = common.RCO2[i] + common.FEDCO2[i]
    if i != common.NZRA:
        common.DMAT[4, i] += common.FEMF[4, i - 1]
    common.DMAT[4, i] -= common.FEMF[4, i]
    
    # 挥发分释放产生的CO2
    common.DMAT[4, i] += (
        0.0 * common.XCOCH * common.RVCH4[i] +
        common.XCTAR_CO * (0.0 * common.RCO[i] + common.RVTAR[i])
    )
    
    # 气相反应对CO2的影响
    common.DMAT[4, i] += rxk1
    common.DMAT[4, i] += rxk3
    common.DMAT[4, i] -= rxk4
    common.DMAT[4, i] += rxk6
    
    # 碳反应对CO2的影响
    common.DMAT[4, i] += ra3 * (2.0 / rphi - 1.0)
    common.DMAT[4, i] -= ra4
    common.DMAT[4, i] += ra5
    
    # 校正因子 (20080324)
    common.DMAT[4, i] /= 1.2
    
    # ---------------------------------------------------------
    # DMAT(5,I): H2S平衡方程
    # ---------------------------------------------------------
    common.DMAT[5, i] = common.RH2S[i]
    if i != common.NZRA:
        common.DMAT[5, i] += common.FEMF[5, i - 1]
    common.DMAT[5, i] -= common.FEMF[5, i]
    
    # ---------------------------------------------------------
    # DMAT(6,I): H2平衡方程
    # ---------------------------------------------------------
    common.DMAT[6, i] = common.RVH2[i] + common.RH2[i]
    common.DMAT[6, i] += common.KCHECK * (common.RVH2[i] + common.RH2[i])
    if i != common.NZRA:
        common.DMAT[6, i] += common.FEMF[6, i - 1]
    common.DMAT[6, i] -= common.FEMF[6, i]
    
    # 气相反应对H2的影响
    common.DMAT[6, i] -= rxk2
    common.DMAT[6, i] += rxk3
    common.DMAT[6, i] -= rxk4
    common.DMAT[6, i] += rxk5 * 3.0
    
    # 碳反应对H2的影响
    common.DMAT[6, i] += ra1
    common.DMAT[6, i] -= ra2 * 2.0
    common.DMAT[6, i] += ra5
    
    # 校正因子 (20080324)
    common.DMAT[6, i] *= 1.02
    
    # ---------------------------------------------------------
    # DMAT(7,I): N2平衡方程
    # ---------------------------------------------------------
    common.DMAT[7, i] = common.REN2[i] + common.FEEDN2[i]
    if i != common.NZRA:
        common.DMAT[7, i] += common.FEMF[7, i - 1]
    common.DMAT[7, i] -= common.FEMF[7, i]
    
    # ---------------------------------------------------------
    # DMAT(8,I): H2O平衡方程
    # ---------------------------------------------------------
    common.DMAT[8, i] = common.RVH2O[i] + common.FEDH2O[i]
    if i != common.NZRA:
        common.DMAT[8, i] += common.FEMF[8, i - 1]
    common.DMAT[8, i] -= common.FEMF[8, i]
    
    # 挥发分释放产生的H2O
    common.DMAT[8, i] += (
        0.0 * common.XHOCH * common.RVCH4[i] +
        0.0 * common.XHOH2 * (common.RH2[i] + common.RVH2[i]) +
        common.XHTAR * common.RVTAR[i]
    )
    
    # 气相反应对H2O的影响
    common.DMAT[8, i] += rxk2
    common.DMAT[8, i] -= rxk3
    common.DMAT[8, i] += rxk4
    common.DMAT[8, i] -= rxk5
    common.DMAT[8, i] += rxk6 * 2.0
    
    # 碳反应对H2O的影响
    common.DMAT[8, i] -= ra1
    common.DMAT[8, i] -= ra5
    
    # ---------------------------------------------------------
    # 晋华炉3.0: 辐射废锅段平衡反应松弛源项 (jinhualu分支新增)
    # 仅作用于 RSC 段 (i > NZRC)，考虑两个平衡反应:
    #   WGS:     CO + H2O <-> CO2 + H2
    #   甲烷化:  CO + 3H2 <-> CH4 + H2O
    # 采用部分平衡松弛: R = KRELAX * 驱动力 * FEM[i] [kmol/s]
    # 源项连续可微，雅可比由数值微分自动获得
    # 反应热经 HENTH(含生成焓) 自动计入能量平衡
    # ---------------------------------------------------------
    if common.KMODEL == 1 and i > common.NZRC and common.FEM[i] > 0.0:
        y_o2, y_ch4, y_co, y_co2 = common.Y[1], common.Y[2], common.Y[3], common.Y[4]
        y_h2, y_h2o = common.Y[6], common.Y[8]
        t_i = max(common.T[i], 500.0)
        
        # WGS平衡常数: K = [CO2][H2]/([CO][H2O])
        k_wgs = np.exp(4577.8 / t_i - 4.33)
        drive_wgs = y_co * y_h2o - y_co2 * y_h2 / max(k_wgs, 1.0e-30)
        r_wgs = common.KRELAX_WGS * drive_wgs * common.FEM[i]
        
        # 甲烷化平衡常数 [1/bar^2], 298K标准态范特霍夫近似
        # K = [CH4][H2O]/([CO][H2]^3) * (P0/P)^2
        k_meth = np.exp(24766.0 / t_i - 25.82)
        p_ratio2 = (common.PWK / common.P0) ** 2
        denom = max(k_meth * p_ratio2, 1.0e-30)
        drive_meth = y_co * y_h2 ** 3 - y_ch4 * y_h2o / denom
        r_meth = common.KRELAX_METH * drive_meth * common.FEM[i]
        
        # 施加到DMAT组分平衡行 (r>0 表示正向进行)
        common.DMAT[2, i] += r_meth          # CH4 生成
        common.DMAT[3, i] -= r_wgs + r_meth  # CO 消耗
        common.DMAT[4, i] += r_wgs           # CO2 生成
        common.DMAT[6, i] += r_wgs - 3.0 * r_meth  # H2
        common.DMAT[8, i] -= r_wgs - r_meth  # H2O
    
    # ---------------------------------------------------------
    # DMAT(NSGP,I): 固体质量平衡 (碳 + 灰分)
    # ---------------------------------------------------------
    nsgp = common.NSGP
    common.DMAT[nsgp, i] = common.WFC[i] + common.WFA[i] + common.KCHECK * common.RVTAR[i] * common.XMTAR
    if i != common.NZRA:
        common.DMAT[nsgp, i] += common.WE[i - 1]
    common.DMAT[nsgp, i] -= common.WE[i] + rri
    
    # ---------------------------------------------------------
    # DMAT(NSGP1,I): 碳转化率平衡 X(I) (单位: kg/s)
    # ---------------------------------------------------------
    nsgp1 = common.NSGP1
    common.DMAT[nsgp1, i] = common.WFC[i]
    if i != common.NZRA:
        common.DMAT[nsgp1, i] += common.WE[i - 1] * common.X[i - 1]
        common.DMAT[nsgp1, i] -= common.RVTAR[0] * common.XMTAR * common.X[i - 1] * common.KCHECK
    common.DMAT[nsgp1, i] -= common.WE[i] * common.X[i] + rri
    common.DMAT[nsgp1, i] += common.RVTAR[0] * common.XMTAR * common.X[i] * common.KCHECK
    
    # ---------------------------------------------------------
    # DMAT(NVWS,I): 能量平衡方程 (如果KTRLT=1)
    # ---------------------------------------------------------
    if common.KTRLT == 1:
        nvws = common.NVWS
        
        # 上游单元格流入的能量
        if i != common.NZRA:
            common.DMAT[nvws, i] = (
                common.FEMF[1, i - 1] * common.HENTH[1, i - 1] +
                common.FEMF[2, i - 1] * common.HENTH[2, i - 1] +
                common.FEMF[3, i - 1] * common.HENTH[3, i - 1] +
                common.FEMF[4, i - 1] * common.HENTH[4, i - 1] +
                common.FEMF[5, i - 1] * common.HENTH[5, i - 1] +
                common.FEMF[6, i - 1] * common.HENTH[6, i - 1] +
                common.FEMF[7, i - 1] * common.HENTH[7, i - 1] +
                common.FEMF[8, i - 1] * common.HENTH[8, i - 1]
            )
        else:
            common.DMAT[nvws, i] = 0.0
        
        # 挥发分释放带入的能量
        common.DMAT[nvws, i] += (
            common.RVCH4[i] * enthp_func(2, 'G', common.TFEED_SL, common.PFEED_SL) +
            (common.RH2[i] + common.RVH2[i]) * enthp_func(6, 'G', common.TFEED_SL, common.PFEED_SL) +
            common.RVH2O[i] * common.HFH2O[i] +
            common.RO2[i] * enthp_func(1, 'G', common.TFEED_SL, common.PFEED_SL) +
            common.REN2[i] * enthp_func(7, 'G', common.TFEED_SL, common.PFEED_SL) +
            common.RCO[i] * enthp_func(3, 'G', common.TFEED_SL, common.PFEED_SL) +
            common.RCO2[i] * enthp_func(4, 'G', common.TFEED_SL, common.PFEED_SL) +
            common.RVTAR[i] * 9.3e6 +
            common.RH2S[i] * enthp_func(5, 'G', common.TFEED_SL, common.PFEED_SL)
        )
        
        # 进料带入的能量
        common.DMAT[nvws, i] += (
            common.FEEDO2[i] * common.FEEDH[1, i] +
            common.FEEDN2[i] * common.FEEDH[2, i] +
            common.FEDCO2[i] * common.FEEDH[3, i]
        )
        
        # 流出带走的能量
        outflow_term = (
            common.FEMF[1, i] * common.HENTH[1, i] +
            common.FEMF[2, i] * common.HENTH[2, i] +
            common.FEMF[3, i] * common.HENTH[3, i] +
            common.FEMF[4, i] * common.HENTH[4, i] +
            common.FEMF[5, i] * common.HENTH[5, i] +
            common.FEMF[6, i] * common.HENTH[6, i] +
            common.FEMF[7, i] * common.HENTH[7, i] +
            common.FEMF[8, i] * common.HENTH[8, i]
        )
        common.DMAT[nvws, i] -= outflow_term
        
        # 固体颗粒流入的能量
        t1 = common.WFC[i] * common.FEDPH[1, i]
        t2 = common.WFA[i] * common.FEDPH[2, i]
        t3 = common.FEDH2O[i] * common.HFH2O[i]
        solid_in_term = t1 + t2 + t3
        common.DMAT[nvws, i] += solid_in_term
        
        # 上游颗粒流入的能量
        if i != common.NZRA:
            common.DMAT[nvws, i] += common.WE[i - 1] * (
                common.X[i - 1] * common.HENTH[9, i - 1] +
                (1.0 - common.X[i - 1]) * common.HENTH[10, i - 1]
            )
            common.DMAT[nvws, i] -= (
                common.RVTAR[0] * common.XMTAR * common.KCHECK *
                (common.X[i - 1] * common.HENTH[9, i - 1] +
                 (1.0 - common.X[i - 1]) * common.HENTH[10, i - 1])
            )
        
        # 当前单元格颗粒流出的能量
        particle_out_term = common.WE[i] * (
            common.X[i] * common.HENTH[9, i] +
            (1.0 - common.X[i]) * common.HENTH[10, i]
        )
        common.DMAT[nvws, i] -= particle_out_term
        common.DMAT[nvws, i] += (
            common.RVTAR[0] * common.XMTAR * common.KCHECK *
            (common.X[i] * common.HENTH[9, i] +
             (1.0 - common.X[i]) * common.HENTH[10, i])
        )
        
        # 热损失计算
        # 晋华炉3.0 (KMODEL=1): 燃烧室段为水冷壁(渣层表面温度TW_WALL),
        # RSC段为废锅壁面(TW_RSC); TEXACO (KMODEL=0) 为耐火砖壁温TW
        if wdkr_func is not None:
            if common.KMODEL == 1:
                tw_i = common.TW_WALL if i <= common.NZRC else common.TW_RSC
            else:
                tw_i = common.TW
            if common.T[i] > tw_i:
                common.QKW[i] = wdkr_func(common.T[i], tw_i) * common.AR[i] * common.DELZ[i] * (common.T[i] - tw_i)
            else:
                common.QKW[i] = 0.0
            common.DMAT[nvws, i] -= common.QKW[i]
        
        # 热损失校正 (仅作用于燃烧室段; RSC段热回收由QKW显式计算)
        if i <= common.NZRC:
            common.DMAT[nvws, i] -= common.QLOSS * common.BSMS * common.HU * 1000.0 * common.DELZ[i] / common.HREAK
        
        # 第一反应区热校正
        if i <= common.NZFR:
            common.DMAT[nvws, i] += common.QH_CRCT * common.DELZ[i] / common.HNZFR
        
        # 焦油热校正
        if common.KCHECK == 1:
            common.DMAT[nvws, i] -= common.RVTAR[i] * 9.3e6 * common.KCHECK
    
    return rri


def gasifier(
    xmass_func,
    entfed_func,
    entkol_func,
    xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func,
    a1_func, a2_func, a3_func, a4_func, a5_func,
    phi_func, ri_func,
    enthp_func,
    wdkr_func=None
):
    """
    GASIFIER主计算子程序
    
    参数:
        xmass_func: XMASS子程序函数
        entfed_func: ENTFED子程序函数
        entkol_func: ENTKOL子程序函数
        xk1_func-xk6_func: 气相反应速率函数XK1-XK6
        a1_func-a5_func: 碳反应速率函数A1-A5
        phi_func: PHI辅助函数
        ri_func: RI总反应速率函数
        enthp_func: ENTHP焓值计算函数
        wdkr_func: WDKR热传导系数函数 (可选)
    
    气体组分编号 (1-based in Fortran):
        1 - O2 (氧气)
        2 - CH4 (甲烷)
        3 - CO (一氧化碳)
        4 - CO2 (二氧化碳)
        5 - H2S (硫化氢)
        6 - H2 (氢气)
        7 - N2 (氮气)
        8 - H2O (水蒸气)
        9 - CARBON (碳)
        10 - ASH (灰分)
    """
    
    # 局部变量
    sum_ri = 0.0
    dalt = np.zeros(12)  # 存储DMAT的初始值 (1-based, index 0 unused)

    # ENTKOL 物性只依赖温度/压力，在一次组装内复用；不跨运行保存缓存。
    # 保留外部注入的回调约定，只有原生实现启用此优化。
    from subroutines.output_results import entkol, entfed
    from subroutines.mass_flow import xmass
    native_entkol = entkol_func is entkol
    native_xmass = xmass_func is xmass
    if entkol_func is entkol:
        enthalpy_cache = {}
        entkol(cache=enthalpy_cache)
    if entfed_func is entfed:
        entfed_func()
        entfed_func = lambda: None  # 进料条件在一次牛顿迭代内不变
    
    # ============================================================
    # 关键修复1: 先调用XMASS计算所有Cell的固体参数
    # 对应Fortran Wg3.for中的 CALL XMASS
    # ============================================================
    xmass_func()
    
    # ============================================================
    # 关键修复2: 计算所有Cell的FEM和U0
    # 对应Fortran Wg3.for中的 FEM(I)计算和U0(II)计算
    # ============================================================
    for ii in range(common.NZRA, common.NZEL2 + 1):
        common.FEM[ii] = 0.0
        for j in range(1, common.NGAS + 1):
            common.FEM[ii] += common.FEMF[j, ii]
    
    for ii in range(common.NZRA, common.NZEL2 + 1):
        common.U0[ii] = common.FEM[ii] * common.RAG * common.T[ii] / (common.PWK * common.AT[ii])
    
    # 用于保存数值微分前的原始状态，避免副作用
    # 必须在所有Cell计算之前保存全局原始值
    xms_orig = np.zeros(common.NZDIM)
    trz_orig = np.zeros(common.NZDIM)
    us_orig = np.zeros(common.NZDIM)
    u0_orig = np.zeros(common.NZDIM)
    for ii in range(common.NZRA, common.NZRE + 1):
        xms_orig[ii] = common.XMS[ii]
        trz_orig[ii] = common.TRZ[ii]
        us_orig[ii] = common.US[ii]
        u0_orig[ii] = common.U0[ii]
    
    # 主循环: 遍历每个网格单元
    for i in range(common.NZRA, common.NZRE + 1):  # NZRA到NZRE (inclusive)
        # 方程仅依赖本格及上游格；不为每次扰动重算全炉物性。
        cells = range(max(common.NZRA, i - 1), i + 1)
        local_xmass = (lambda: xmass(cells=cells)) if native_xmass else xmass_func
        local_entkol = (lambda: entkol(cells=cells, cache=enthalpy_cache)) if native_entkol else entkol_func
        
        # ============================================================
        # 1. 初始化矩阵为零
        # ============================================================
        for k in range(1, common.NVWS + 1):
            common.DMAT[k, i] = 0.0
            for l in range(1, common.NVWS + 1):
                common.AMAT[k, l, i] = 0.0
                common.BMAT[k, l, i] = 0.0
                common.CMAT[k, l, i] = 0.0
        
        k_state = 0  # 状态变量，用于数值微分
        
        # ============================================================
        # 数值微分主循环 - 对应Fortran的标签53/80逻辑
        # ============================================================
        while True:
            # 在计算DMAT之前恢复XMS等变量，避免数值微分副作用
            # 这确保每次计算使用正确的固体质量
            if k_state > 0:
                active = slice(common.NZRA, common.NZRE + 1)
                common.XMS[active] = xms_orig[active]
                common.TRZ[active] = trz_orig[active]
                common.US[active] = us_orig[active]
                common.U0[active] = u0_orig[active]
            
            # 计算DMAT - 对应Fortran标签53
            # 每次扰动后都需要重新计算DMAT
            
            pass
            
            rri = _calculate_dmat_for_cell(
                i,
                local_xmass, entfed_func, local_entkol,
                xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func,
                a1_func, a2_func, a3_func, a4_func, a5_func,
                phi_func, ri_func,
                enthp_func,
                wdkr_func
            )
            
            # 保存RAC[i] (仅在k_state=0时)
            if k_state == 0:
                common.RAC[i] = rri
            
            # 对应Fortran: IF (K.GT.0) GOTO 70
            # 如果k_state>0，说明已经扰动过，计算差分并恢复变量
            if k_state > 0:
                # 恢复扰动值
                kk = k_state - common.NVWS
                if kk <= 0:
                    # 恢复当前单元格的扰动
                    if k_state <= common.NVE:
                        common.FEMF[k_state, i] -= delta
                    elif k_state == common.NSGP:
                        common.WE[i] -= delta
                    elif k_state == common.NSGP1:
                        common.X[i] -= delta
                    elif k_state == common.NVWS:
                        common.T[i] -= delta
                else:
                    # 恢复上游单元格的扰动
                    if i > common.NZRA:
                        if kk <= common.NVE:
                            common.FEMF[kk, i - 1] -= delta
                        elif kk == common.NSGP:
                            common.WE[i - 1] -= delta
                        elif kk == common.NSGP1:
                            common.X[i - 1] -= delta
                        elif kk == common.NVWS:
                            common.T[i - 1] -= delta
                
                # 计算BMAT或AMAT元素 - 对应Fortran标签70
                pass
                pass
                if kk <= 0:
                    # 计算BMAT (对角块)
                    k_col = k_state
                    for j in range(1, common.NVWS + 1):
                        common.BMAT[j, k_col, i] = (common.DMAT[j, i] - dalt[j]) / delta
                else:
                    # 计算AMAT (下对角块)
                    kk_col = kk
                    for j in range(1, common.NVWS + 1):
                        common.AMAT[j, kk_col, i - 1] = (common.DMAT[j, i] - dalt[j]) / delta
                
                # 检查是否继续数值微分 - 对应Fortran: IF (K.LE.NSGP1) GOTO 80
                if k_state <= common.NSGP1:
                    pass  # 继续到标签80，增加k_state并扰动下一个变量
                elif k_state <= 2 * common.NVWS - 1:
                    pass  # 继续到标签801（第二个循环）
                else:
                    # 数值微分完成，恢复DMAT原始值
                    for j in range(1, common.NVWS + 1):
                        common.DMAT[j, i] = dalt[j]
                    break  # 退出数值微分循环
            
            # 对应Fortran标签80: 保存初始值并开始扰动循环
            if k_state == 0:
                # 保存初始DMAT值
                for j in range(1, common.NVWS + 1):
                    dalt[j] = common.DMAT[j, i]
            
            # 增加k_state并扰动下一个变量
            k_state += 1
            delta = 0.0001
            # 残碳接近零时，固定 1e-4 扰动远大于本身，导致反应核导数失真。
            # 晋华炉使用相对步长；TEXACO 保留原 Fortran 差分路径。
            column = (k_state - 1) % common.NVWS + 1
            cell = i if k_state <= common.NVWS else i - 1
            if common.KMODEL == 1 and column == common.NSGP1 and cell >= common.NZRA:
                delta = max(1e-12, min(0.0001, abs(common.X[cell]) * 0.01))
            
            # 第一部分扰动: 当前单元格变量 (k_state <= NVWS)
            if k_state <= common.NVE:
                common.FEMF[k_state, i] += delta
                continue  # GOTO 53，重新计算DMAT
            elif k_state == common.NSGP:
                common.WE[i] += delta
                continue  # GOTO 53
            elif k_state == common.NSGP1:
                common.X[i] += delta
                continue  # GOTO 53
            elif k_state == common.NVWS:
                common.T[i] += delta
                continue  # GOTO 53
            
            # 第二部分扰动: 上游单元格变量 (k_state > NVWS)
            # 对应Fortran标签801
            kk = k_state - common.NVWS
            
            if kk <= common.NVE:
                if i > common.NZRA:
                    common.FEMF[kk, i - 1] += delta
                # 即使i==NZRA也要继续循环(不扰动)
                continue  # GOTO 53
            elif kk == common.NSGP:
                if i > common.NZRA:
                    common.WE[i - 1] += delta
                continue  # GOTO 53
            elif kk == common.NSGP1:
                if i > common.NZRA:
                    common.X[i - 1] += delta
                continue  # GOTO 53
            elif kk == common.NVWS:
                if i > common.NZRA:
                    common.T[i - 1] += delta
                continue  # GOTO 53
            
            # 所有扰动完成，退出循环
            # 恢复DMAT原始值
            for j in range(1, common.NVWS + 1):
                common.DMAT[j, i] = dalt[j]
            break
        
        # ============================================================
        # 7. 构建AMAT矩阵 (下对角块) - 显式设置对角元素
        # ============================================================
        if common.KTRLT == 1:
            if i != common.NZRA:
                # 固体质量平衡项
                common.AMAT[common.NSGP, common.NSGP, i - 1] = 1.0
                common.AMAT[common.NSGP, common.NSGP1, i - 1] = 0.0
                common.AMAT[common.NSGP1, common.NSGP, i - 1] = common.X[i - 1]
                common.AMAT[common.NSGP1, common.NSGP1, i - 1] = common.WE[i - 1]
                
                # 能量方程AMAT项
                for k in range(1, common.NVE + 1):
                    common.AMAT[common.NVWS, k, i - 1] = common.HENTH[k, i - 1]
                
                common.AMAT[common.NVWS, common.NSGP, i - 1] = (
                    common.X[i - 1] * common.HENTH[9, i - 1] +
                    (1.0 - common.X[i - 1]) * common.HENTH[10, i - 1]
                )
                common.AMAT[common.NVWS, common.NSGP1, i - 1] = (
                    common.WE[i - 1] * (common.HENTH[9, i - 1] - common.HENTH[10, i - 1])
                )
                
                # 温度导数项
                dhdt_sum = (
                    common.FEMF[1, i - 1] * common.DHDT[1, i - 1] +
                    common.FEMF[2, i - 1] * common.DHDT[2, i - 1] +
                    common.FEMF[3, i - 1] * common.DHDT[3, i - 1] +
                    common.FEMF[4, i - 1] * common.DHDT[4, i - 1] +
                    common.FEMF[5, i - 1] * common.DHDT[5, i - 1] +
                    common.FEMF[6, i - 1] * common.DHDT[6, i - 1] +
                    common.FEMF[7, i - 1] * common.DHDT[7, i - 1] +
                    common.FEMF[8, i - 1] * common.DHDT[8, i - 1]
                )
                dhdt_sum += common.WE[i - 1] * (
                    common.X[i - 1] * common.DHDT[9, i - 1] +
                    (1.0 - common.X[i - 1]) * common.DHDT[10, i - 1]
                )
                common.AMAT[common.NVWS, common.NVWS, i - 1] = dhdt_sum
        
        # ============================================================
        # 8. DMAT取负 (与Fortran保持一致)
        # ============================================================
        # Fortran代码在GASIFIER末尾对DMAT取负
        # DO 1990 J=1,NVWS
        #    DMAT(J,I)=-DMAT(J,I)
        # 1990 CONTINUE
        for j in range(1, common.NVWS + 1):
            common.DMAT[j, i] = -common.DMAT[j, i]
        
        # 累加总反应速率
        sum_ri += rri
    
    return sum_ri
