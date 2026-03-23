#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 质量流量计算
对应Fortran中的XMASS子程序
"""
import numpy as np
import sys
sys.path.append(r'E:\Texco\src')
from common.common_data import common


def xmass():
    """
    计算每个小格的质量流量
    XMASS - Calculate mass flow for each cell
    
    计算内容:
    - 气体密度 ROG(I) = 353.5/T(I)
    - 颗粒密度 ROS(I) based on carbon conversion
    - 气体粘度 XMUG(I)
    - 沉降速度 UT
    - 颗粒速度 US(I)
    - 停留时间 TRZ(I)
    - 固体质量 XMS(I) 和 空隙率 EPS(I)
    """
    # 计算灰分在干燥无灰基中的比例
    # FASH = ELAS / (ELC + ELH + ELO + ELN + ELS)
    fash = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 初始固体密度 (挥发分释放前)
    # ROSVM = ROS0 (简化处理, 实际应为 ROS0*(1+FASH-XCVM0)/(1+FASH))
    rosvm = common.ROS0
    
    # 平均停留时间计算
    sum_trz = 0.0
    
    # 循环计算每个格子 (NZRA to NZRE, Fortran 1-based index)
    # In Python: range(nzra, nzre+1) to include nzre
    for i in range(common.NZRA, common.NZRE + 1):
        # 气体密度 [kg/m^3]
        # ROG(I) = 353.5 / T(I)
        # Note: 353.5 = P0*M_air/(R*T0) for standard conditions
        common.ROG[i] = 353.5 / common.T[i]
        
        # 计算FOC (考虑碳转化率对密度的影响)
        # FOC = 1.0 - FASH * X(I) / (1.0 - X(I))
        # 防除零保护
        x_safe = min(common.X[i], 0.999999)
        foc = 1.0 - fash * x_safe / (1.0 - x_safe)
        
        # 限制FOC最大值不超过1.0
        if foc > 1.0:
            foc = 1.0
        
        # 颗粒密度 [kg/m^3]
        # ROS(I) = ROS0 * (1 + FASH - FOC) / (1 + FASH)
        common.ROS[i] = common.ROS0 * (1.0 + fash - foc) / (1.0 + fash)
        
        # 气体动力粘度 [Pa·s]
        # XMUG(I) = ROG(I) * (12.2 + 0.0261*(T(I)-273.15)**1.2616) * 1.0E-6
        temp_c = common.T[i] - 273.15  # Convert K to Celsius
        # 防负值保护: 确保温度在有效范围内
        if temp_c < 0.0:
            temp_c = 0.0
        common.XMUG[i] = common.ROG[i] * (12.2 + 0.0261 * (temp_c ** 1.2616)) * 1.0e-6
        
        # 阻力系数 B [1/s]
        # B = 18.0 * XMUG(I) / ROS(I) / DP / DP
        b = 18.0 * common.XMUG[i] / common.ROS[i] / common.DP / common.DP
        # 防除零保护
        b = max(b, 1e-20)
        
        # 颗粒沉降速度 [m/s]
        # UT = (ROS(I) - ROG(I)) * G / B / ROS(I)
        ut = (common.ROS[i] - common.ROG[i]) * common.G / b / common.ROS[i]
        
        # 初始颗粒速度 USI [m/s]
        # 对于第一个格子 (NZRA), 使用入口条件
        # 对于其他格子, 使用前一个格子的值
        if i == common.NZRA:
            # USI = (WFC(I) + WFA(I)) / ROSVM / AT(I)
            usi = (common.WFC[i] + common.WFA[i]) / rosvm / common.AT[i]
        else:
            # USI = ((WFC(I) + WFA(I)) / ROSVM + WE(I-1) / ROS(I-1)) / AT(I)
            usi = ((common.WFC[i] + common.WFA[i]) / rosvm + 
                   common.WE[i-1] / common.ROS[i-1]) / common.AT[i]
        
        # 迭代计算停留时间 TRZ1
        # 使用迭代方法求解非线性方程
        trz1 = 0.05  # 初始猜测值 [s]
        max_iter = 1000  # 最大迭代次数保护
        iter_count = 0
        
        while iter_count < max_iter:
            iter_count += 1
            
            # 颗粒速度 US(I) [m/s]
            # US(I) = USI * EXP(-B*TRZ1) + (U0(I) + UT) * (1.0 - EXP(-B*TRZ1))
            # 防下溢保护
            exp_arg = -b * trz1
            if exp_arg < -700:
                exp_term = 0.0
            else:
                exp_term = np.exp(exp_arg)
            
            # 计算US，防下溢
            us_calc = usi * exp_term + (common.U0[i] + ut) * (1.0 - exp_term)
            # 如果计算结果无效，使用一个最小正值
            if us_calc < 1e-30:
                us_calc = 1e-30
            common.US[i] = us_calc
            
            # 计算新的停留时间 [s]
            # TRZ2 = DELZ(I) / US(I)
            trz2 = common.DELZ[i] / common.US[i]
            
            # 检查收敛
            # IF(DABS((TRZ1-TRZ2)/TRZ1).GT.1.0E-5) THEN
            if abs((trz1 - trz2) / trz1) > 1.0e-5:
                trz1 = trz2
                continue  # 继续迭代
            else:
                trz1 = trz2
                break  # 收敛, 退出循环
        
        if iter_count >= max_iter:
            print(f"[WARNING] xmass: TRZ iteration did not converge for cell {i}, using last value")
            common.TRZ[i] = trz1
        
        # 存储收敛后的停留时间
        common.TRZ[i] = trz1
        sum_trz += common.TRZ[i]
    
    # 计算每个格子的固体质量和空隙率
    sum_xms = 0.0
    
    for i in range(common.NZRA, common.NZRE + 1):
        # 格子内固体质量 [kg]
        # XMS(I) = WE(I) * TRZ(I)
        common.XMS[i] = common.WE[i] * common.TRZ[i]
        
        # 空隙率 (void fraction)
        # EPS(I) = 1.0 - XMS(I) / ROS(I) / (AT(I) * DELZ(I))
        volume = common.AT[i] * common.DELZ[i]  # 格子体积 [m^3]
        solid_volume = common.XMS[i] / common.ROS[i]  # 固体体积 [m^3]
        common.EPS[i] = 1.0 - solid_volume / volume
        
        sum_xms += common.XMS[i]
    
    return sum_trz, sum_xms
