#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 主程序 (残差输出版)
对应Fortran主程序: PROGRAM TEXACO_GASIFIER
"""

import numpy as np
from common.common_data import common
from subroutines.initialization import eingab
from subroutines.gasifier_main import gasifier
from functions.math_utils import newtra
from subroutines.output_results import kolerg

# Import reaction rate functions
from functions.gas_reactions import xk1, xk2, xk3, xk4, xk5, xk6
from functions.reaction_rates import A1, A2, A3, A4, A5, PHI, RI, ENTHP
from subroutines.mass_flow import xmass
from subroutines.output_results import entfed, entkol


def calculate_residuals():
    """
    计算当前迭代的残差 (SUMFE, SUMWE, SUMX, SUMT)
    对应Fortran NEWTRA中的残差计算
    
    注意: DMAT使用1-based索引（与Fortran兼容）
    DMAT[1:8,:] 对应气体组分方程 (O2, CH4, CO, CO2, H2S, H2, N2, H2O)
    """
    # SUMFE: 气体组分残差 (J=1 to NVE)
    sumfe = 0.0
    for i in range(common.NZEL1 - 1, common.NZEL2):
        for j in range(1, common.NVE + 1):  # FIXED: 从1开始，不是0
            sumfe += abs(common.DMAT[j, i])
    
    # SUMWE: 固体质量流残差 (Fortran NSGP = 9)
    sumwe = 0.0
    for i in range(common.NZEL1 - 1, common.NZEL2):
        sumwe += abs(common.DMAT[common.NSGP, i])
    
    # SUMX: 碳转化率残差 (Fortran NSGP1 = 10)
    sumx = 0.0
    for i in range(common.NZEL1 - 1, common.NZEL2):
        sumx += abs(common.DMAT[common.NSGP1, i])
    
    # SUMT: 温度残差 (Fortran NVWS = 11)
    sumt = 0.0
    if common.KTRLT == 1:
        for i in range(common.NZEL1 - 1, common.NZEL2):
            sumt += abs(common.DMAT[common.NVWS, i])
    
    return sumfe, sumwe, sumx, sumt


def print_matrices_iter0():
    """
    打印第一次迭代前的矩阵（用于与Fortran对比）
    输出格式与Fortran保持一致
    """
    with open('python_matrix_iter0.txt', 'w') as f:
        f.write('Python Matrix Output - First Iteration (Iter=1)\n')
        f.write('================================\n')
        
        # 只打印前5个单元 (Python 0-based: 0-4 = Fortran 1-based: 1-5)
        for ii in range(0, 5):
            f.write('\n')
            f.write('================================\n')
            f.write(f'Cell {ii+1}\n')
            f.write('================================\n')
            
            # DMAT
            f.write('DMAT:\n')
            for j in range(1, common.NVWS + 1):
                f.write(f'  DMAT({j:2d},{ii:2d}) = {common.DMAT[j, ii]:20.10e}\n')
            
            # BMAT (只打印前8行8列)
            f.write('BMAT:\n')
            for j in range(1, 9):
                row_str = f'  Row{j:2d} = '
                for k in range(1, 9):
                    row_str += f'{common.BMAT[j, k, ii]:12.4e} '
                f.write(row_str + '\n')
            
            # AMAT (只打印前8行8列)
            f.write('AMAT:\n')
            for j in range(1, 9):
                row_str = f'  Row{j:2d} = '
                for k in range(1, 9):
                    row_str += f'{common.AMAT[j, k, ii]:12.4e} '
                f.write(row_str + '\n')
            
            # CMAT (只打印前8行8列)
            f.write('CMAT:\n')
            for j in range(1, 9):
                row_str = f'  Row{j:2d} = '
                for k in range(1, 9):
                    row_str += f'{common.CMAT[j, k, ii]:12.4e} '
                f.write(row_str + '\n')


def main():
    """
    TEXACO气化炉CFD模拟主程序 (残差输出版)
    """
    # 打开输出文件 (对应Fortran: OPEN (UNIT=1,FILE='GASTEST.DAT',STATUS='UNKNOWN'))
    output_file = open('GASTEST.DAT', 'w')
    
    # 初始化迭代计数器
    common.ITERAT = 0
    
    # 调用EINGAB进行初始化 (对应Fortran: CALL EINGAB)
    eingab()
    
    # 写入残差历史表头
    output_file.write('\n')
    output_file.write('=' * 60 + '\n')
    output_file.write('迭代残差历史 (Convergence History)\n')
    output_file.write('=' * 60 + '\n')
    output_file.write(f"{'Iter':>6} {'KONVER':>8} {'SUMFE':>14} {'SUMWE':>14} {'SUMX':>14} {'SUMT':>14}\n")
    output_file.write('-' * 60 + '\n')
    
    # 主迭代循环 (对应Fortran: DO 100 I=1,ITMAX)
    converged = False
    for iteration in range(1, common.ITMAX + 1):
        # 增加迭代计数
        common.ITERAT = common.ITERAT + 1
        
        # 重置收敛标志
        common.KONVER = 0
        
        # 调用GASIFIER进行气化炉计算
        gasifier(
            xmass_func=xmass,
            entfed_func=entfed,
            entkol_func=entkol,
            xk1_func=xk1, xk2_func=xk2, xk3_func=xk3, xk4_func=xk4, xk5_func=xk5, xk6_func=xk6,
            a1_func=A1, a2_func=A2, a3_func=A3, a4_func=A4, a5_func=A5,
            phi_func=PHI, ri_func=RI,
            enthp_func=ENTHP
        )
        
        # 第一次迭代时打印矩阵（用于与Fortran对比）
        if common.ITERAT == 1:
            print_matrices_iter0()
        
        # 重置收敛标志用于牛顿迭代
        common.KONVER = 0
        
        # 调用NEWTRA进行牛顿迭代求解
        omega = 1.0  # Match Fortran (no relaxation)
        newtra(omega=omega)
        
        # 计算残差
        sumfe, sumwe, sumx, sumt = calculate_residuals()
        
        # 写入当前迭代的残差到GASTEST.DAT
        output_file.write(f"{common.ITERAT:>6} {common.KONVER:>8} {sumfe:>14.6e} {sumwe:>14.6e} {sumx:>14.6e} {sumt:>14.6e}\n")
        
        # 同时输出到屏幕
        print(f"Iter:{common.ITERAT:>4} K={common.KONVER} FE={sumfe:.3e} WE={sumwe:.3e} X={sumx:.3e} T={sumt:.3e}")
        
        # 检查收敛性
        if common.KONVER == 0:
            output_file.write('-' * 60 + '\n')
            output_file.write(f'收敛完成! (Converged at iteration {common.ITERAT})\n')
            output_file.write('=' * 60 + '\n')
            kolerg(output_file)
            converged = True
            break
        
        # 检查是否达到最大迭代次数
        if common.ITERAT == common.ITMAX:
            message = ' MAX. ITERATIONS'
            output_file.write(message + '\n')
            output_file.write('-' * 60 + '\n')
            output_file.write('达到最大迭代次数 (Reached max iterations)\n')
            output_file.write('=' * 60 + '\n')
            print(message)
            kolerg(output_file)
            break
    
    # 关闭输出文件
    output_file.close()


if __name__ == "__main__":
    main()
