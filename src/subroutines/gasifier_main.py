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

# 导入其他子程序 (将在需要时导入)
# from subroutines.xmass import xmass
# from subroutines.entfed import entfed
# from subroutines.entkol import entkol
# from subroutines.reaction_rates import xk1, xk2, xk3, xk4, xk5, xk6
# from subroutines.char_reactions import a1, a2, a3, a4, a5
# from subroutines.auxiliary import phi, ri


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
    for ii in range(common.NZRA, common.NZRE + 1):
        common.U0[ii] = common.FEM[ii] * common.RAG * common.T[ii] / (common.PWK * common.AT[ii])
    
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
    
    # DEBUG OUTPUT disabled for production run
    
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
        
        pass
        
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
            pass
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
        # Debug output removed
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
        pass  # Debug output removed
        common.DMAT[nvws, i] -= particle_out_term
        common.DMAT[nvws, i] += (
            common.RVTAR[0] * common.XMTAR * common.KCHECK *
            (common.X[i] * common.HENTH[9, i] +
             (1.0 - common.X[i]) * common.HENTH[10, i])
        )
        
        # 热损失计算
        if wdkr_func is not None:
            if common.T[i] > common.TW:
                common.QKW[i] = wdkr_func(common.T[i], common.TW) * common.AR[i] * common.DELZ[i] * (common.T[i] - common.TW)
            else:
                common.QKW[i] = 0.0
            common.DMAT[nvws, i] -= common.QKW[i]
        
        # 热损失校正
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
    xms_orig = np.zeros(31)
    trz_orig = np.zeros(31)
    us_orig = np.zeros(31)
    u0_orig = np.zeros(31)
    for ii in range(common.NZRA, common.NZRE + 1):
        xms_orig[ii] = common.XMS[ii]
        trz_orig[ii] = common.TRZ[ii]
        us_orig[ii] = common.US[ii]
        u0_orig[ii] = common.U0[ii]
    
    # 主循环: 遍历每个网格单元
    for i in range(common.NZRA, common.NZRE + 1):  # NZRA到NZRE (inclusive)
        
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
                pass
                for ii in range(common.NZRA, common.NZRE + 1):
                    common.XMS[ii] = xms_orig[ii]
                    common.TRZ[ii] = trz_orig[ii]
                    common.US[ii] = us_orig[ii]
                    common.U0[ii] = u0_orig[ii]
            
            # 计算DMAT - 对应Fortran标签53
            # 每次扰动后都需要重新计算DMAT
            
            pass
            
            rri = _calculate_dmat_for_cell(
                i,
                xmass_func, entfed_func, entkol_func,
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
                        common.FEMF[k_state, i] -= 0.0001
                    elif k_state == common.NSGP:
                        common.WE[i] -= 0.0001
                    elif k_state == common.NSGP1:
                        common.X[i] -= 0.0001
                    elif k_state == common.NVWS:
                        common.T[i] -= 0.0001
                else:
                    # 恢复上游单元格的扰动
                    if i > common.NZRA:
                        if kk <= common.NVE:
                            common.FEMF[kk, i - 1] -= 0.0001
                        elif kk == common.NSGP:
                            common.WE[i - 1] -= 0.0001
                        elif kk == common.NSGP1:
                            common.X[i - 1] -= 0.0001
                        elif kk == common.NVWS:
                            common.T[i - 1] -= 0.0001
                
                # 计算BMAT或AMAT元素 - 对应Fortran标签70
                pass
                pass
                if kk <= 0:
                    # 计算BMAT (对角块)
                    k_col = k_state
                    for j in range(1, common.NVWS + 1):
                        common.BMAT[j, k_col, i] = (common.DMAT[j, i] - dalt[j]) / 0.0001
                else:
                    # 计算AMAT (下对角块)
                    kk_col = kk
                    for j in range(1, common.NVWS + 1):
                        common.AMAT[j, kk_col, i - 1] = (common.DMAT[j, i] - dalt[j]) / 0.0001
                
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
            
            # 第一部分扰动: 当前单元格变量 (k_state <= NVWS)
            if k_state <= common.NVE:
                common.FEMF[k_state, i] += 0.0001
                continue  # GOTO 53，重新计算DMAT
            elif k_state == common.NSGP:
                common.WE[i] += 0.0001
                continue  # GOTO 53
            elif k_state == common.NSGP1:
                common.X[i] += 0.0001
                continue  # GOTO 53
            elif k_state == common.NVWS:
                common.T[i] += 0.0001
                continue  # GOTO 53
            
            # 第二部分扰动: 上游单元格变量 (k_state > NVWS)
            # 对应Fortran标签801
            kk = k_state - common.NVWS
            
            if kk <= common.NVE:
                if i > common.NZRA:
                    common.FEMF[kk, i - 1] += 0.0001
                # 即使i==NZRA也要继续循环(不扰动)
                continue  # GOTO 53
            elif kk == common.NSGP:
                if i > common.NZRA:
                    common.WE[i - 1] += 0.0001
                continue  # GOTO 53
            elif kk == common.NSGP1:
                if i > common.NZRA:
                    common.X[i - 1] += 0.0001
                continue  # GOTO 53
            elif kk == common.NVWS:
                if i > common.NZRA:
                    common.T[i - 1] += 0.0001
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
                # 注意：AMAT对角元素不再强制设为1.0
                # 保留数值微分计算的值（包含CO2方程的5/6系数）
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
    
    # ============================================================
    # 9. 变量缩放已禁用 - 为了与Fortran 1:1对比
    # ============================================================
    # apply_variable_scaling()  # 暂时禁用缩放
    
    return sum_ri


def apply_variable_scaling():
    """
    应用行缩放以改善矩阵条件数
    仅对能量方程(第11行)进行行缩放。
    """
    WE_SCALE = 1.0e6  # 能量缩放因子
    
    for i in range(common.NZEL1, common.NZEL2 + 1):
        # 行缩放：第11行除以WE_SCALE
        common.DMAT[11, i] /= WE_SCALE
        
        for j in range(1, 12):
            common.BMAT[11, j, i] /= WE_SCALE
            common.AMAT[11, j, i] /= WE_SCALE
            common.CMAT[11, j, i] /= WE_SCALE


def restore_variable_scaling():
    """
    恢复变量缩放 - 求解后恢复解向量的第11个分量
    
    注意：求解后的值已经正确，但如果需要调整，这里乘以WE_SCALE
    因为在求解过程中，行缩放的影响需要被补偿
    """
    WE_SCALE = 1.0e6
    
    for i in range(common.NZEL1, common.NZEL2 + 1):
        common.DMAT[11, i] *= WE_SCALE
    



def restore_all_scaling():
    """
    恢复所有缩放 - 在BLKTRD回代前调用
    恢复BMAT/AMAT/CMAT的第11行和DMAT的第11行
    """
    WE_SCALE = 1.0e6
    
    for i in range(common.NZEL1, common.NZEL2 + 1):
        # 恢复DMAT第11行
        common.DMAT[11, i] *= WE_SCALE
        
        # 恢复BMAT/AMAT/CMAT的第11行
        for j in range(1, 12):
            common.BMAT[11, j, i] *= WE_SCALE
            common.AMAT[11, j, i] *= WE_SCALE
            common.CMAT[11, j, i] *= WE_SCALE
    



def gasifier_simple(
    reaction_funcs,
    enthp_func,
    wdkr_func=None
):
    """
    GASIFIER简化版本 - 用于初步测试
    
    参数:
        reaction_funcs: 包含所有反应速率函数的字典
        enthp_func: 焓值计算函数
        wdkr_func: 热传导系数函数 (可选)
    
    返回:
        sum_ri: 总反应速率
    """
    sum_ri = 0.0
    
    for i in range(common.NZRA, common.NZRE + 1):
        # 初始化
        for k in range(1, common.NVWS + 1):
            common.DMAT[k, i] = 0.0
            for l in range(1, common.NVWS + 1):
                common.AMAT[k, l, i] = 0.0
                common.BMAT[k, l, i] = 0.0
                common.CMAT[k, l, i] = 0.0
        
        # 计算总摩尔流量
        common.FEM[i] = 0.0
        for j in range(1, common.NGAS + 1):
            common.FEM[i] += common.FEMF[j, i]
        
        # 计算气体速度
        for ii in range(common.NZRA, common.NZRE + 1):
            common.U0[ii] = common.FEM[ii] * common.RAG * common.T[ii] / (common.PWK * common.AT[ii])
        
        # 计算摩尔分数
        for j in range(1, common.NGAS + 1):
            if common.FEM[i] > 0:
                common.Y[j] = common.FEMF[j, i] / common.FEM[i]
            else:
                common.Y[j] = 0.0
        
        # 计算反应速率
        if common.KTRLR == 1:
            rxk1 = reaction_funcs['xk1'](i)
            rxk2 = reaction_funcs['xk2'](i)
            rxk3 = reaction_funcs['xk3'](i)
            rxk4 = reaction_funcs['xk4'](i)
            rxk5 = reaction_funcs['xk5'](i)
            rxk6 = reaction_funcs['xk6'](i)
            
            ra1 = reaction_funcs['a1'](i)
            ra2 = reaction_funcs['a2'](i)
            ra3 = reaction_funcs['a3'](i)
            ra4 = reaction_funcs['a4'](i)
            ra5 = reaction_funcs['a5'](i)
            
            rri = reaction_funcs['ri'](i)
            common.RAC[i] = rri
        else:
            rxk1 = rxk2 = rxk3 = rxk4 = rxk5 = rxk6 = 0.0
            ra1 = ra2 = ra3 = ra4 = ra5 = 0.0
            rri = 0.0
            common.RAC[i] = rri
        
        rphi = reaction_funcs['phi'](i)
        
        # 构建DMAT (简化版本 - 仅基本质量平衡)
        for j in range(1, common.NGAS + 1):
            common.DMAT[j, i] = 0.0
            if i != common.NZRA:
                common.DMAT[j, i] += common.FEMF[j, i - 1]
            common.DMAT[j, i] -= common.FEMF[j, i]
        
        # 固体质量平衡
        nsgp = common.NSGP
        common.DMAT[nsgp, i] = common.WFC[i] + common.WFA[i]
        if i != common.NZRA:
            common.DMAT[nsgp, i] += common.WE[i - 1]
        common.DMAT[nsgp, i] -= common.WE[i] + rri
        
        # 碳转化率平衡
        nsgp1 = common.NSGP1
        common.DMAT[nsgp1, i] = common.WFC[i]
        if i != common.NZRA:
            common.DMAT[nsgp1, i] += common.WE[i - 1] * common.X[i - 1]
        common.DMAT[nsgp1, i] -= common.WE[i] * common.X[i] + rri
        
        # DMAT不取负 (与Fortran保持一致)
        # (移除取负操作，2026-03-17)
        
        sum_ri += rri
    
    return sum_ri
