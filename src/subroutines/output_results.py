#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 结果输出和焓计算子程序
对应Fortran文件: Wg8.for

包含以下子程序:
- KOLERG: 主输出子程序
- ENTKOL: 计算煤入口焓
- ENTFED: 计算进料焓
- KONTR: 质量/能量平衡检查
- HCRCT: 热校正
- TPAR, TPAR1: 颗粒温度参数函数
"""

import numpy as np
import sys
import os

# 添加父目录到路径以导入common_data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.common_data import common
from functions.reaction_rates import ENTHP

# 煤种数据表 (YCOAL)
# YCOAL(J,I): J=1-8 (气体组分), I=1-9 (煤种)
# 气体组分: 1-O2, 2-CH4, 3-CO, 4-CO2, 5-H2S, 6-H2, 7-N2, 8-H2O
# 数据单位: %
YCOAL = np.array([
    # O2,   CH4,    CO,    CO2,   H2S,    H2,    N2,   H2O
    [0.0,   0.04,  39.95, 11.43, 0.88,  30.78, 0.49,  16.43],   # 煤种1
    [0.0,   0.16,  37.36, 13.30, 0.12,  29.26, 0.37,  19.43],   # 煤种2
    [0.0,   0.22,  30.88, 15.91, 0.11,  26.71, 0.50,  25.67],   # 煤种3
    [0.0,   0.25,  39.46, 12.59, 0.30,  29.33, 0.60,  17.47],   # 煤种4
    [0.0,   0.02,  36.53, 15.67, 0.27,  26.01, 0.68,  20.82],   # 煤种5
    [0.0,   0.30,  41.00, 10.20, 1.10,  29.80, 0.80,  17.10],   # 煤种6
    [0.0,   0.02,  35.20, 12.80, 1.14,  29.90, 0.63,  20.30],   # 煤种7
    [0.0,   0.09,  47.10, 13.20, 2.20,  24.30, 0.40,  12.70],   # 煤种8
    [0.0,   0.00,  61.50, 1.600, 1.30,  30.60, 4.70,  0.000],   # 煤种9
])

# TPAR1函数的多项式系数
# A和B系数用于不同粒径范围的温度计算
TPAR1_A = np.array([
    [1122.994, 21.23601, -60.2475, 107.1993, -50.48936, 0.0],
    [1123.103, 23.84986, -17.29235, 43.09767, 0.0, 0.0],
    [1122.837, 54.30377, -135.3284, 182.2734, 0.0, 0.0],
    [1123.018, -100.5066, 1418.011, -4905.727, 6849.767, -3208.673],
    [1123.091, -404.3886, 4485.182, -14948.5, 19929.87, -8832.512],
    [1123.159, -800.694, 8528.113, -28452.69, 38010.92, -16979.31],
])

TPAR1_B = np.array([
    [1126.84, 19.94464, -6.334953, 0.7821025, -3.443153e-2, 0.0],
    [1118.61, 86.17874, -38.72582, 7.698807, -0.7276266, 2.653273e-2],
    [1215.189, 23.74415, -13.94155, 2.183904, -0.1122286, 0.0],
    [1308.797, -28.80658, 1.674385, 0.0, 0.0, 0.0],
    [1419.006, -77.2164, 10.24267, -0.5100107, 0.0, 0.0],
    [1624.889, -276.4914, 98.19461, -19.29845, 1.90521, -7.359819e-2],
])


def RI(i):
    """
    计算碳反应速率 (辅助函数)
    对应Fortran中的RI函数
    
    参数:
        i: 格子索引 (0-based)
    
    返回:
        反应速率 [kg/s]
    """
    # 简化的实现，实际应由Wg7.for中的A1-A5函数计算
    return common.RAC[i]


def kolerg(output_file=None):
    """
    主输出子程序 - 将计算结果输出到文件
    
    参数:
        output_file: 输出文件对象，如果为None则输出到标准输出
    
    对应Fortran: SUBROUTINE KOLERG
    
    功能:
        - 调用KONTR进行质量/能量平衡检查
        - 输出炉内参数分布 (温度、速度、转化率等)
        - 输出气体成分分布
        - 输出合成气成分
        - 保存结果到START.DAT文件
    """
    # 设置输出目标
    if output_file is None:
        outfile = sys.stdout
    else:
        outfile = output_file
    
    # 调用KONTR进行质量/能量平衡检查
    hein, haus, dh, dm, xmein, xmaus = kontr()
    
    # 输出标题
    outfile.write("\n" + "#" * 70 + "\n")
    outfile.write("计算结果输出\n\n")
    outfile.write("    1. 炉内参数分布数据\n")
    
    # 表头
    outfile.write("\n")
    outfile.write(f"{'I':>4s} {'高度(m)':>8s} {'气速(m/s)':>10s} {'停留时间(s)':>12s} "
                  f"{'碳流量(kg/s)':>12s} {'温度(C)':>10s} {'碳转化率(%)':>12s}\n")
    
    # 初始化求和变量
    sum_rac = 0.0
    sum_wfc = 0.0
    sum_qkw = 0.0
    sum_cab = 0.0
    sum_xms = 0.0
    sum_trz = 0.0
    
    # 计算灰分比例
    fash = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 遍历所有格子输出参数
    for i in range(common.NZEL1, common.NZEL2 + 1):  # 转换为0-based索引
        sum_wfc += common.WFC[i]
        
        # 氧气摩尔分数
        yo2 = common.FEMF[1, i] / common.FEM[i] if common.FEM[i] > 0 else 0.0
        
        # 反应速率
        rate = RI(i)
        
        # 碳转化率相关
        foc = 1.0 - fash * common.X[i] / (1.0 - common.X[i]) if common.X[i] < 1.0 else 0.0
        
        # 累加各项
        sum_rac += rate
        sum_qkw += common.QKW[i]
        sum_cab += common.XMS[i] * common.X[i]
        sum_xms += common.XMS[i]
        sum_trz += common.TRZ[i]
        
        # 输出当前格子数据
        outfile.write(f"{i+1:>4d} {common.H[i]:>8.3f} {common.U0[i]:>10.3f} "
                      f"{sum_trz:>12.3f} {common.WE[i]:>12.3f} "
                      f"{common.T[i]-273.15:>10.3f} {foc*100:>12.3f}\n")
    
    # 计算总转化率
    conv_rate = 1.0 - common.WE[common.NZRE] * common.X[common.NZRE] / (common.BSMS * common.ELC)
    
    # 输出气体成分分布
    outfile.write("\n")
    outfile.write("    2. 炉内气体成分分布数据\n")
    outfile.write(f"\n{'I':>4s} {'O2(%)':>8s} {'CH4(%)':>8s} {'CO(%)':>8s} "
                  f"{'CO2(%)':>8s} {'H2S(%)':>8s} {'H2(%)':>8s} {'N2(%)':>8s} {'H2O(%)':>8s}\n")
    
    for i in range(common.NZRA, common.NZRE + 1):
        mole_fracs = []
        for j in range(1, 9):  # 1-8号组分
            mf = common.FEMF[j, i] / common.FEM[i] * 100.0 if common.FEM[i] > 0 else 0.0
            mole_fracs.append(mf)
        
        outfile.write(f"{i+1:>4d} " + " ".join([f"{mf:>8.3f}" for mf in mole_fracs]) + "\n")
    
    # 计算出口气体摩尔分数
    y = np.zeros(9)
    for j in range(1, 9):
        y[j] = common.FEMF[j, common.NZRE] / common.FEM[common.NZRE] if common.FEM[common.NZRE] > 0 else 0.0
    
    # 计算误差平方和
    err_sqrt = 0.0
    for j in range(2, 9):
        err_sqrt += (y[j] * 100.0 - YCOAL[common.NCOAL-1, j-1]) ** 2
    
    # 输出合成气成分
    outfile.write("\n")
    outfile.write("    3. 合成气出口成分数据\n")
    outfile.write(f"\n{'组分':>12s}: ")
    outfile.write("O2      CH4       CO      CO2      H2S       H2       N2\n")
    
    # 干基成分 (不含H2O)
    dry_gas = common.FEM[common.NZRE] - common.FEMF[8, common.NZRE]
    dry_fracs = []
    for j in range(1, 8):  # 1-7号组分 (不含H2O)
        df = common.FEMF[j, common.NZRE] / dry_gas * 100.0 if dry_gas > 0 else 0.0
        dry_fracs.append(df)
    
    outfile.write(f"{'干基成分(%)':>12s}: " + " ".join([f"{df:>8.4f}" for df in dry_fracs]) + "\n")
    
    # 体积流量 (Nm3/s)
    vol_flows = []
    for j in range(1, 8):
        vf = common.FEMF[j, common.NZRE] * 22.4
        vol_flows.append(vf)
    
    outfile.write(f"{'体积流量(Nm3/s)':>12s}: " + " ".join([f"{vf:>8.4f}" for vf in vol_flows]) + "\n")
    
    # 输出温度和转化率
    outfile.write(f"\n    出口温度: {common.T[common.NZRE]-273.15:>8.3f} C    "
                  f"碳转化率: {conv_rate:>8.4f}\n")
    
    # 保存结果到START.DAT文件
    start_dat_path = os.path.join(os.path.dirname(__file__), '..', '..', 'START.DAT')
    try:
        with open(start_dat_path, 'w') as f:
            # 输出FEMF(1-4)
            for i in range(common.NZEL1, common.NZEL2 + 1):
                f.write(f"{common.FEMF[1,i]:15.6e}  {common.FEMF[2,i]:15.6e}  "
                        f"{common.FEMF[3,i]:15.6e}  {common.FEMF[4,i]:15.6e}\n")
            # 输出FEMF(5-8)
            for i in range(common.NZEL1, common.NZEL2 + 1):
                f.write(f"{common.FEMF[5,i]:15.6e}  {common.FEMF[6,i]:15.6e}  "
                        f"{common.FEMF[7,i]:15.6e}  {common.FEMF[8,i]:15.6e}\n")
            # 输出温度T
            for i in range(common.NZEL1, common.NZEL2 + 1):
                f.write(f"{common.T[i]:16.6e}\n")
            # 输出碳转化率X
            for i in range(common.NZEL1, common.NZEL2 + 1):
                f.write(f"{common.X[i]:15.6e}  {0.0:15.6e}\n")
            # 输出碳流量WE
            for i in range(common.NZEL1, common.NZEL2 + 1):
                f.write(f"{common.WE[i]:15.6e}  {0.0:15.6e}\n")
    except Exception as e:
        outfile.write(f"\n警告: 无法写入START.DAT文件: {e}\n")


def entkol():
    """
    计算煤入口焓 - 初始化各格子各组分的焓值和温度导数
    
    对应Fortran: SUBROUTINE ENTKOL
    
    功能:
        - 计算各气体组分(O2, CH4, CO, CO2, H2S, H2, N2)的焓值
        - 计算H2O的焓值 (根据温度决定气相或液相)
        - 计算固体组分(C, Ash)的焓值
        - 计算焓值对温度的导数 DHDT
    
    说明:
        DHDT是焓值对温度的差分近似
        气体编号: 1-O2, 2-CH4, 3-CO, 4-CO2, 5-H2S, 6-H2, 7-N2, 8-H2O, 9-C, 10-Ash
        单位: 气体焓 [J/kmol], 固体焓 [J/kg]
    """
    dht = np.zeros(15)  # 临时数组，用于计算温度导数
    
    for i in range(common.NZEL1, common.NZEL2 + 1):
        # 计算气体组分 (1-7) 的焓值和温度导数
        for j in range(1, 8):
            dht[j] = ENTHP(j, 'G', common.T[i] + 1.0, common.PWK)
            common.HENTH[j, i] = ENTHP(j, 'G', common.T[i], common.PWK)
            common.DHDT[j, i] = dht[j] - common.HENTH[j, i]
        
        # 计算H2O (组分8) 的焓值
        j = 8
        if common.T[i] > 373.15:
            # 气态水
            dht[j] = ENTHP(j, 'G', common.T[i] + 1.0, common.PWK)
            common.HENTH[j, i] = ENTHP(j, 'G', common.T[i], common.PWK)
        else:
            # 液态水
            dht[j] = ENTHP(j, 'L', common.T[i] + 1.0, common.PWK)
            common.HENTH[j, i] = ENTHP(j, 'L', common.T[i], common.PWK)
        common.DHDT[j, i] = dht[j] - common.HENTH[j, i]
        
        # 计算固体组分 (9-C, 10-Ash) 的焓值
        for j in range(9, 11):
            dht[j] = ENTHP(j, '', common.T[i] + 1.0, common.PWK)
            common.HENTH[j, i] = ENTHP(j, '', common.T[i], common.PWK)
            common.DHDT[j, i] = dht[j] - common.HENTH[j, i]


def entfed():
    """
    计算进料焓 - 计算进料流股的焓值
    
    对应Fortran: SUBROUTINE ENTFED
    
    功能:
        - 计算氧气进料焓 (FEEDH[1])
        - 计算氮气进料焓 (FEEDH[2])
        - 计算CO2进料焓 (FEEDH[3])
        - 计算水进料焓 (HFH2O)
        - 计算碳颗粒进料焓 (FEDPH[1])
        - 计算灰分进料焓 (FEDPH[2])
    
    说明:
        FEEDH(1): 格子I中氧气的焓值
        FEEDH(2): 格子I中氮气的焓值
        FEEDH(3): 格子I中CO2的焓值
        FEDPH(1): 格子I中碳颗粒的焓值
        FEDPH(2): 格子I中灰分的焓值
    """
    for i in range(common.NZEL1, common.NZEL2 + 1):
        # 初始化
        common.FEEDH[1, i] = 0.0
        common.FEEDH[2, i] = 0.0
        common.FEEDH[3, i] = 0.0
        common.FEDPH[1, i] = 0.0
        common.FEDPH[2, i] = 0.0
        common.HFH2O[i] = 0.0
        
        # 氧气 (组分1)
        if common.FEEDO2[i] != 0.0:
            common.FEEDH[1, i] = ENTHP(1, 'G', common.TFEED_OX, common.PFEED_OX)
        
        # 氮气 (组分7)
        if common.FEEDN2[i] != 0.0:
            common.FEEDH[2, i] = ENTHP(7, 'G', common.TFEED_OX, common.PFEED_OX)
        
        # CO2进料 (注意：Fortran 使用 ENTHP(7,N2) 而不是 ENTHP(4,CO2))
        if common.FEDCO2[i] != 0.0:
            common.FEEDH[3, i] = ENTHP(7, 'G', common.TFEED_CO2, common.PFEED_CO2)
        
        # H2O - 根据温度决定相态
        iagg = 'L'  # 默认液态
        if common.FEDH2O[i] != 0.0:
            common.HFH2O[i] = ENTHP(8, iagg, common.TFEED_SL, common.PFEED_SL)
        
        # 碳颗粒 (组分9)
        if common.WFC[i] != 0.0:
            common.FEDPH[1, i] = ENTHP(9, 'S', common.TFEED_SL, common.PFEED_SL)
        
        # 灰分 (组分10)
        if common.WFA[i] != 0.0:
            common.FEDPH[2, i] = ENTHP(10, 'S', common.TFEED_SL, common.PFEED_SL)


def tpar(i):
    """
    计算焦炭颗粒温度 (简化模型)
    
    参数:
        i: 格子索引 (0-based)
    
    返回:
        颗粒温度 [K]
    
    对应Fortran: FUNCTION TPAR(I)
    
    说明:
        根据气体温度和氧气浓度计算颗粒温度升高
    """
    # 计算温度升高量
    if common.FEM[i] > 0:
        delt = (common.FEMF[1, i] / common.FEM[i] * 66.0e3 * 
                common.PWK / (common.RAG * common.T[i]))
    else:
        delt = 0.0
    
    if delt <= 0.0:
        delt = 0.0
    
    tpar_val = common.T[i] + delt
    
    return tpar_val


def tpar1(i):
    """
    计算焦炭颗粒温度 (详细模型)
    
    参数:
        i: 格子索引 (0-based)
    
    返回:
        颗粒温度 [K]
    
    对应Fortran: FUNCTION TPAR1(I)
    
    说明:
        使用多项式拟合计算颗粒温度
        考虑CO2浓度和颗粒直径的影响
    """
    # CO2摩尔分数
    co2 = common.FEMF[1, i] / common.FEM[i] if common.FEM[i] > 0 else 0.0
    
    # 如果温度低于1000K，返回气体温度
    if common.T[i] < 1000.0:
        return common.T[i]
    
    # 颗粒直径 (mm)
    dpmm = common.DP * 1.0e3
    if dpmm >= 8.0:
        dpmm = 2.0
    
    # 根据CO2浓度确定系数索引
    if co2 <= 0.05:
        k = 0
    elif co2 <= 0.1:
        k = 1
    elif co2 <= 0.125:
        k = 2
    elif co2 <= 0.15:
        k = 3
    elif co2 <= 0.175:
        k = 4
    else:
        k = 5
    
    # 根据粒径范围选择多项式计算TP0
    if dpmm <= 1.0:
        # 使用A系数
        tp0 = (TPAR1_A[k, 0] + dpmm * (TPAR1_A[k, 1] + dpmm * 
               (TPAR1_A[k, 2] + dpmm * (TPAR1_A[k, 3] + 
                dpmm * (TPAR1_A[k, 4] + dpmm * TPAR1_A[k, 5])))))
    else:
        # 使用B系数
        tp0 = (TPAR1_B[k, 0] + dpmm * (TPAR1_B[k, 1] + dpmm * 
               (TPAR1_B[k, 2] + dpmm * (TPAR1_B[k, 3] + 
                dpmm * (TPAR1_B[k, 4] + dpmm * TPAR1_B[k, 5])))))
    
    # 计算温度修正
    dattp = (tp0 - 1123.0) * (-165.5 + 0.18 * common.T[i]) / 37.0
    if dattp < 0.0:
        dattp = 0.0
    
    tpar1_val = common.T[i] + dattp
    
    return tpar1_val


def kontr():
    """
    质量/能量平衡检查 - 计算进出系统的质量和能量流
    
    对应Fortran: SUBROUTINE KONTR
    
    返回:
        hein: 输入总能量流 [W]
        haus: 输出总能量流 [W]
        dh: 能量差 [W]
        dm: 质量差 [kg/s]
        xmein: 输入总质量流 [kg/s]
        xmaus: 输出总质量流 [kg/s]
    
    功能:
        - 元素平衡检查 (C, H, O, N, S, Ash)
        - 输入能量流计算 (固体进料 + 气体进料 + 挥发分)
        - 输出能量流计算 (出口固体 + 出口气体 + 热损失)
    """
    # ===== 元素平衡检查 =====
    # 输入元素总量
    c_total = common.BSLURRY * common.RATIO_COAL * common.ELC
    h_total = common.BSLURRY * (common.RATIO_COAL * (common.ELH + common.ELH2O * 2.0 / 18.0)
                                 + (1.0 - common.RATIO_COAL) * 2.0 / 18.0)
    o_total = common.BSLURRY * (common.RATIO_COAL * (common.ELO + common.ELH2O * 16.0 / 18.0)
                                 + (1.0 - common.RATIO_COAL) * 16.0 / 18.0) + common.GFOX * common.PURE_O2
    xn_total = common.BSLURRY * common.RATIO_COAL * common.ELN + common.GFOX * (1.0 - common.PURE_O2)
    s_total = common.BSLURRY * common.RATIO_COAL * common.ELS
    ash_total = common.BSLURRY * common.RATIO_COAL * common.ELAS
    
    # 输出元素总量
    nzre_idx = common.NZRE  # 转换为0-based索引
    
    # C: CH4 + CO + CO2 + 未反应碳
    sum_c = ((common.FEMF[2, nzre_idx] + common.FEMF[3, nzre_idx] + common.FEMF[4, nzre_idx]) * 12.0
             + common.WE[nzre_idx] * common.X[nzre_idx]
             - common.RVTAR[0] * common.XMTAR * common.X[nzre_idx] * common.KCHECK
             + common.RVTAR[0] * 12.0 * common.KCHECK)
    
    # H: CH4(4H) + H2S(2H) + H2(2H) + H2O(2H) + 焦油中的H
    sum_h = ((common.FEMF[2, nzre_idx] * 4.0 + common.FEMF[5, nzre_idx] * 2.0 
              + common.FEMF[6, nzre_idx] * 2.0 + common.FEMF[8, nzre_idx] * 2.0)
             + common.RVTAR[0] * 0.689 * common.KCHECK)
    
    # O: O2(2O) + CO(O) + CO2(2O) + H2O(O) + 焦油中的O
    sum_o = ((common.FEMF[1, nzre_idx] * 2.0 + common.FEMF[3, nzre_idx] 
              + common.FEMF[4, nzre_idx] * 2.0 + common.FEMF[8, nzre_idx])
             + common.RVTAR[0] * 0.014 * 16.0 * common.KCHECK)
    
    # N: N2(2N)
    sum_n = common.FEMF[7, nzre_idx] * 28.0
    
    # S: H2S(S)
    sum_s = common.FEMF[5, nzre_idx] * 32.0
    
    # Ash
    sum_ash = (common.WE[nzre_idx] * (1.0 - common.X[nzre_idx])
               - common.RVTAR[0] * common.XMTAR * (1.0 - common.X[nzre_idx]) * common.KCHECK)
    
    # 总质量流
    xmein = c_total + h_total + o_total + xn_total + s_total + ash_total
    xmaus = sum_c + sum_h + sum_o + sum_n + sum_s + sum_ash
    dm = xmein - xmaus
    
    # ===== 能量平衡检查 =====
    # 输入固体能量流
    heinf = 0.0
    for i in range(common.NZRA, common.NZRE + 1):
        heinf += common.WFC[i] * common.FEDPH[1, i] + common.WFA[i] * common.FEDPH[2, i]
    
    # 输入气体能量流 (含挥发分)
    heing = common.QH_CRCT
    for i in range(common.NZEL1, common.NZEL2 + 1):
        heing += (common.FEEDO2[i] * common.FEEDH[1, i] 
                  + common.FEEDN2[i] * common.FEEDH[2, i]
                  + common.FEDH2O[i] * common.HFH2O[i])
        
        heing += (common.RVCH4[i] * ENTHP(2, 'G', common.TFEED_SL, common.PFEED_SL)
                  + (common.RH2[i] + common.RVH2[i]) * ENTHP(6, 'G', common.TFEED_SL, common.PFEED_SL)
                  + common.RVH2O[i] * common.HFH2O[i]
                  + common.RO2[i] * ENTHP(1, 'G', common.TFEED_SL, common.PFEED_SL)
                  + common.REN2[i] * ENTHP(7, 'G', common.TFEED_SL, common.PFEED_SL)
                  + common.RCO[i] * ENTHP(3, 'G', common.TFEED_SL, common.PFEED_SL)
                  + common.RCO2[i] * ENTHP(4, 'G', common.TFEED_SL, common.PFEED_SL)
                  + common.RVTAR[i] * 9.3e6
                  + common.RH2S[i] * ENTHP(5, 'G', common.TFEED_SL, common.PFEED_SL))
    
    # 输出固体能量流
    hausf = (common.WE[nzre_idx] * (common.X[nzre_idx] * common.HENTH[9, nzre_idx]
                                      + (1.0 - common.X[nzre_idx]) * common.HENTH[10, nzre_idx])
             - common.RVTAR[0] * common.XMTAR * common.KCHECK
             * (common.X[nzre_idx] * common.HENTH[9, nzre_idx]
                + (1.0 - common.X[nzre_idx]) * common.HENTH[10, nzre_idx]))
    
    # 热损失
    hausq = common.QLOSS * common.BSMS * common.HU * 1000.0
    for i in range(common.NZRA, common.NZRE + 1):
        hausq += common.QKW[i]
    
    # 输出气体能量流
    hausg = 0.0
    for j in range(1, 9):
        hausg += common.FEMF[j, nzre_idx] * common.HENTH[j, nzre_idx]
    
    # 总能量流
    hein = heinf + heing
    haus = hausf + hausg + hausq + common.RVTAR[0] * 9.3e6 * common.KCHECK
    dh = hein - haus
    
    return hein, haus, dh, dm, xmein, xmaus


def hcrt():
    """
    热校正 - 第一格子的初始能量检查
    
    对应Fortran: SUBROUTINE HCRCT
    
    功能:
        - 检查第一格子的质量平衡
        - 计算第一格子的初始能量输入和输出
        - 确定热校正项QH_CRCT
    
    注意:
        此子程序主要用于初始条件检查和能量校正
    """
    # 第一格子 (0-based index = 0)
    i = 0
    
    # 输入质量流
    xmin_o2 = common.FEEDO2[i] * 32.0
    xmin_n2 = common.FEEDN2[i] * 28.0
    xmin_h2o = common.FEDH2O[i] * 18.0
    xmin_c = common.WFC[i]
    xmin_a = common.WFA[i]
    xmin_vt = (common.RVCH4[0] * 16.0 + common.RCO[0] * 28.0 
               + common.RCO2[0] * 44.0 + common.RVTAR[0] * common.XMTAR
               + common.RVH2O[0] * 18.0 + (common.RVH2[0] + common.RH2[0]) * 2.0
               + common.RH2S[0] * 34.0 + common.REN2[0] * 28.0 + common.RO2[0] * 32.0)
    
    xmt_in = xmin_o2 + xmin_n2 + xmin_h2o + xmin_c + xmin_a + xmin_vt
    
    # 输出质量流
    xout_gas = (common.FEMF[1, i] * 32.0 + common.FEMF[2, i] * 16.0
                + common.FEMF[3, i] * 28.0 + common.FEMF[4, i] * 44.0
                + common.FEMF[5, i] * 34.0 + common.FEMF[6, i] * 2.0
                + common.FEMF[7, i] * 28.0 + common.FEMF[8, i] * 18.0)
    xout_sd = common.WE[i]
    
    xmt_out = xout_gas + xout_sd
    xm_diff = xmt_in - xmt_out - common.RVTAR[0] * common.XMTAR
    
    # 调用ENTFED计算进料焓
    entfed()
    
    # 输入能量流
    ein_o2 = common.FEEDO2[i] * common.FEEDH[1, i]
    ein_n2 = common.FEEDN2[i] * common.FEEDH[2, i]
    ein_vt = (common.RVCH4[0] * ENTHP(2, 'G', common.TFEED_SL, common.PFEED_SL)
              + (common.RH2[0] + common.RVH2[0]) * ENTHP(6, 'G', common.TFEED_SL, common.PFEED_SL)
              + common.RVH2O[0] * common.HFH2O[0]
              + common.RO2[0] * ENTHP(1, 'G', common.TFEED_SL, common.PFEED_SL)
              + common.REN2[0] * ENTHP(7, 'G', common.TFEED_SL, common.PFEED_SL)
              + common.RCO[0] * ENTHP(3, 'G', common.TFEED_SL, common.PFEED_SL)
              + common.RCO2[0] * ENTHP(4, 'G', common.TFEED_SL, common.PFEED_SL)
              + common.RVTAR[0] * 9.3e6
              + common.RH2S[0] * ENTHP(5, 'G', common.TFEED_SL, common.PFEED_SL))
    
    ein_sd = common.WFC[i] * common.FEDPH[1, i] + common.WFA[i] * common.FEDPH[2, i]
    ein_h2o = common.FEDH2O[i] * common.HFH2O[i]
    ein_total = ein_o2 + ein_n2 + ein_vt + ein_sd + ein_h2o
    
    # 设置第一格子温度并重新计算焓
    common.T[i] = common.TFEED_SL
    entkol()
    
    # 输出能量流
    eout_gas = 0.0
    for j in range(1, 9):
        eout_gas += common.FEMF[j, i] * common.HENTH[j, i]
    
    eout_sd = common.WE[i] * (common.X[i] * common.HENTH[9, i] 
                              + (1.0 - common.X[i]) * common.HENTH[10, i])
    
    eout_total = eout_gas + eout_sd
    
    # 能量差
    e_diff = ein_total - eout_total
    e_diff1 = e_diff - common.RVTAR[0] * 9.3e6
    
    # 可以在这里设置QH_CRCT进行能量校正
    # common.QH_CRCT = -common.RVTAR[0] * 9.3e6
    
    return xm_diff, e_diff, e_diff1


# 导出所有函数
__all__ = [
    'kolerg',      # 主输出子程序
    'entkol',      # 煤入口焓计算
    'entfed',      # 进料焓计算
    'kontr',       # 质量/能量平衡检查
    'hcrt',        # 热校正
    'tpar',        # 颗粒温度(简化)
    'tpar1',       # 颗粒温度(详细)
    'ENTHP',       # 焓值计算辅助函数
    'YCOAL',       # 煤种数据表
    'RI',          # 反应速率辅助函数
]
