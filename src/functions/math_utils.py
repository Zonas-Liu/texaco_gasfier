#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 数学工具模块
对应Fortran的Wg9.for
"""
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.common_data import common


def gausll(n, ns, a):
    """
    高斯消元法求解线性方程组 (改进版 - 增强数值稳定性)
    
    改进点:
    1. 确保所有计算使用float64
    2. 改进的阈值处理
    3. 优化的部分主元选取
    4. 更稳定的消元过程
    
    参数:
        n: 系数矩阵的维数
        ns: 右侧矩阵的列数
        a: 增广矩阵 (n x (n+ns))，会被修改
    
    返回:
        nfehl: 错误代码 (0=成功)
        a: 求解后的矩阵，左侧变为单位矩阵，右侧为解
    """
    # 确保使用float64
    a = np.array(a, dtype=np.float64, copy=True)
    nfehl = 0
    n1 = n + 1
    nt = n + ns
    
    # 标量情况
    if n == 1:
        if abs(a[0, 0]) < 1.0e-20:
            a[0, 0] = 1.0e-20
        scale = a[0, 0]
        for k in range(1, nt):
            a[0, k] = a[0, k] / scale
        return nfehl, a
    
    # 前向消元 - 改进版
    for i in range(2, n + 1):
        ip = i - 1
        i1 = ip
        
        # 选主元 - 使用当前列的绝对值最大值
        x = abs(a[i1 - 1, i1 - 1])
        for j in range(i, n + 1):
            if abs(a[j - 1, i1 - 1]) > x:
                x = abs(a[j - 1, i1 - 1])
                ip = j
        
        # 行交换
        if ip != i1:
            for j in range(i1 - 1, nt):
                x = a[i1 - 1, j]
                a[i1 - 1, j] = a[ip - 1, j]
                a[ip - 1, j] = x
        
        # 消元 - 改进的数值处理
        pivot = a[i1 - 1, i1 - 1]
        if abs(pivot) < 1.0e-20:
            pivot = 1.0e-20
            a[i1 - 1, i1 - 1] = pivot
        
        for j in range(i, n + 1):
            factor = a[j - 1, i1 - 1] / pivot
            if abs(factor) > 1.0e-20:
                # 直接更新整行
                for k in range(i1 - 1, nt):
                    a[j - 1, k] = a[j - 1, k] - factor * a[i1 - 1, k]
    
    # 回代 - 修正版
    for ip in range(1, n + 1):
        i = n1 - ip
        
        pivot = a[i - 1, i - 1]
        if abs(pivot) < 1.0e-20:
            pivot = 1.0e-20
            a[i - 1, i - 1] = pivot
        
        # 归一化当前行（包括左侧矩阵）
        for k in range(i - 1, nt):
            a[i - 1, k] = a[i - 1, k] / pivot
        
        if i == 1:
            continue
        
        i1 = i - 1
        # 消去上方行的当前列（包括左侧矩阵）
        for j in range(0, i1):
            factor = a[j, i - 1]
            if abs(factor) > 1.0e-20:
                for k in range(i - 1, nt):
                    a[j, k] = a[j, k] - a[i - 1, k] * factor
    
    return nfehl, a


def matadd(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2):
    """
    矩阵加法: MATOUT = MATIN1 + MATIN2
    
    参数:
        nf, ng: 矩阵维度
        matin1: 输入矩阵1 (nf x ndi1)
        nan1x: 实际使用列数
        matin2: 输入矩阵2 (nf x ndi2)
        nan2x: 实际使用列数
        ndi1, ndi2: 矩阵维度参数
    
    返回:
        matout: 输出矩阵 (与matin1相同形状)
    """
    matout = np.zeros(matin1.shape)
    
    ncols = matin1.shape[1] - 1 if len(matin1.shape) > 1 else 0
    
    for i in range(1, min(nan1x, ncols) + 1):
        for k in range(1, ng + 1):
            if k < matin1.shape[0] and i < matin1.shape[1] and k < matin2.shape[0] and i < matin2.shape[1]:
                matout[k, i] = matin1[k, i] + matin2[k, i]
    
    return matout


def matsub(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2):
    """
    矩阵减法: MATOUT = MATIN1 - MATIN2
    
    参数:
        nf, ng: 矩阵维度
        matin1: 输入矩阵1 (nf x ndi1)
        nan1x: 实际使用列数
        matin2: 输入矩阵2 (nf x ndi2)
        nan2x: 实际使用列数
        ndi1, ndi2: 矩阵维度参数
    
    返回:
        matout: 输出矩阵 (与matin1相同形状)
    """
    matout = np.zeros(matin1.shape)
    
    # 获取实际列数
    ncols = abs(nan1x)
    max_i = min(ncols, matin1.shape[1] - 1)
    if matin1.shape[1] == 1 and ncols >= 1:
        # 特殊情况: 输入只有1列，但我们把它当作第1列来处理
        max_i = 1
    
    for i in range(1, max_i + 1):
        for k in range(1, ng + 1):
            if k < matin1.shape[0] and i < matin1.shape[1] and k < matin2.shape[0] and i < matin2.shape[1]:
                matout[k, i] = matin1[k, i] - matin2[k, i]
    
    # 特殊情况: 如果matin1只有1列，使用??
    if matin1.shape[1] == 1 and ncols >= 1:
        for k in range(1, ng + 1):
            if k < matin1.shape[0] and k < matin2.shape[0]:
                matout[k, 0] = matin1[k, 0] - matin2[k, 0]
    
    return matout


def matmult(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2):
    """
    矩阵乘法: MATOUT = MATIN1 * MATIN2
    按照Fortran MATMULT实现
    
    参数:
        nf, ng: 矩阵维度
        matin1: 输入矩阵1 (nf+1 x ...)
        nan1x: 实际使用列数（负值表示转置）
        matin2: 输入矩阵2 (nf+1 x nf+1)
        nan2x: 实际使用列数
        ndi1, ndi2: 维度参数
    
    返回:
        matout: 输出矩阵
    """
    # 获取实际的维度
    ncols_in1 = abs(nan1x)
    nrows_out = ng
    nrows_mid = ng
    
    # 判断是否为向量情况：nan1x=1 且 matin1 实际只有1列
    is_vector = (ncols_in1 == 1 and matin1.shape[1] == 1)
    
    # 创建输出数组
    if is_vector:
        # 向量情况：输出也是列向量
        matout = np.zeros((matin1.shape[0], 1))
        col_idx = 0  # 输入数据在第0列
    else:
        # 矩阵情况：输出形状与matin1相同
        actual_cols = min(ncols_in1, matin1.shape[1] - 1)
        matout = np.zeros((matin1.shape[0], matin1.shape[1]))
        col_idx = None
    
    if is_vector:
        # 向量情况：MATOUT(K,0) = sum_L MATIN1(L,0) * MATIN2(K,L)
        for k in range(1, nrows_out + 1):
            if k < matout.shape[0] and k < matin2.shape[0]:
                sum_val = 0.0
                for l in range(1, nrows_mid + 1):
                    if l < matin1.shape[0] and l < matin2.shape[1]:
                        qel = matin1[l, col_idx]
                        if abs(qel) > 1.0e-20:
                            sum_val += qel * matin2[k, l]
                matout[k, 0] = sum_val
    else:
        # 矩阵情况：MATOUT(K,I) = sum_L MATIN1(L,I) * MATIN2(K,L)
        # 注意：当ncols_in1=1时，数据可能在第0列（向量情况）或第1列（矩阵情况）
        actual_cols = min(ncols_in1, matin1.shape[1] - 1)
        for i in range(1, actual_cols + 1):
            if i >= matin1.shape[1]:
                break
            # 确定数据列和输出列
            if ncols_in1 == 1 and i == 1:
                # 检查第0列是否有数据（非零）
                col_has_data = any(abs(matin1[l, 0]) > 1e-20 for l in range(1, min(nrows_mid + 1, matin1.shape[0])))
                if col_has_data:
                    data_col = 0  # 数据在第0列
                    out_col = 0   # 结果也放在第0列
                else:
                    data_col = i
                    out_col = i
            else:
                data_col = i
                out_col = i
            
            for k in range(1, nrows_out + 1):
                if k >= matout.shape[0]:
                    break
                sum_val = 0.0
                for l in range(1, nrows_mid + 1):
                    if l < matin1.shape[0] and i < matin1.shape[1] and k < matin2.shape[0] and l < matin2.shape[1]:
                        qel = matin1[l, data_col]
                        if abs(qel) > 1.0e-20:
                            sum_val += qel * matin2[k, l]
                matout[k, out_col] = sum_val
    
    return matout


def matdiv(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2):
    """
    矩阵除法: MATOUT = MATIN1 / MATIN2
    严格按照Fortran MATDIV实现
    
    参数:
        nf: 矩阵行数
        ng: 矩阵维数
        matin1: 被除矩阵 (nf x |nan1x|)
        nan1x: matin1的列数（负值表示需要转置）
        matin2: 除数矩阵 (nf x |nan2x|)
        nan2x: matin2的列数（负值表示需要转置）
        ndi1, ndi2: 维度参数
    
    返回:
        matdiv: 错误代码 (0=成功)
        matout: 结果矩阵
    """
    # 标量情况
    if ng < 2:
        matout = np.zeros((nf + 1, 2))
        # 处理matin1和matin2可能是向量的情况
        m1_val = matin1[1, 0] if matin1.shape[1] == 1 else matin1[1, 1]
        m2_val = matin2[1, 0] if matin2.shape[1] == 1 else matin2[1, 1]
        if abs(m2_val) > 1e-20:
            matout[1, 1] = m1_val / m2_val
        else:
            matout[1, 1] = m1_val / 1e-20
        return 0, matout
    
    # 计算实际维度（取绝对值）
    nnin1 = abs(nan1x)
    nnin2 = abs(nan2x)
    
    # 创建增广矩阵 ZMAT (nnin2 x (nnin2 + nnin1))
    zmat = np.zeros((nnin2, nnin2 + nnin1))
    
    # 填充左侧: MATIN2（或其转置）
    # Fortran: 如果NAN2X<0, ZMAT(I,K) = MATIN2(K,I)
    # 注意Fortran是列优先，Python是行优先
    if nan2x < 0:
        # 转置: ZMAT的第I行第K?= MATIN2的第K行第I?
        for i in range(nnin2):
            for k in range(ng):
                zmat[i, k] = matin2[k + 1, i + 1]
    else:
        # 直接: ZMAT的第I行第K?= MATIN2的第I行第K?
        for i in range(nnin2):
            for k in range(ng):
                zmat[i, k] = matin2[i + 1, k + 1]
    
    # 填充右侧: MATIN1（或其转置）
    # Fortran: 如果NAN1X<0, ZMAT(K, NNIN2+I) = MATIN1(I,K)
    # 注意：matin1的形状可能是 (nf+1) x 1 ?(nf+1) x (nnin1+1)
    if nan1x < 0:
        # 转置: ZMAT的第K行第(NNIN2+I)?= MATIN1的第I行第K?
        for i in range(nnin1):
            for k in range(ng):
                # matin1[i+1, k+1] 要考虑matin1的实际形?
                if i + 1 < matin1.shape[0] and k + 1 < matin1.shape[1]:
                    zmat[k, nnin2 + i] = matin1[i + 1, k + 1]
                elif k + 1 < matin1.shape[0] and matin1.shape[1] == 1:
                    # matin1只有1列，使用??
                    zmat[k, nnin2 + i] = matin1[k + 1, 0]
    else:
        # 直接: ZMAT的第K行第(NNIN2+I)?= MATIN1的第K行第I?
        for i in range(nnin1):
            for k in range(ng):
                if k + 1 < matin1.shape[0] and i + 1 < matin1.shape[1]:
                    zmat[k, nnin2 + i] = matin1[k + 1, i + 1]
                elif k + 1 < matin1.shape[0] and matin1.shape[1] == 1:
                    # matin1只有1列，使用第0列
                    zmat[k, nnin2 + i] = matin1[k + 1, 0]
    
    # 调用高斯消元
    nfehl, zmat = gausll(nnin2, nnin1, zmat)
    
    if nfehl != 0:
        return nfehl, np.zeros((nf + 1, ndi1 + 1))
    
    # 创建输出矩阵
    matout = np.zeros((nf + 1, ndi1 + 1))
    
    # 复制结果
    # Fortran: 如果NAN1X<=0, MATOUT(I,K) = ZMAT(K, NNIN2+I)
    if nan1x <= 0:
        # 转置输出
        for i in range(nnin1):
            for k in range(ng):
                matout[i + 1, k + 1] = zmat[k, nnin2 + i]
    else:
        # 直接输出: MATOUT(K,I) = ZMAT(K, NNIN2+I)
        for i in range(nnin1):
            for k in range(ng):
                matout[k + 1, i + 1] = zmat[k, nnin2 + i]
    
    return 0, matout


def matums(nf, nmat, matin1, nmat1, nx1, mx1, nmat2, nxu1):
    """
    矩阵复制: MATOUT = MATIN1
    
    参数:
        nf: 矩阵维度
        nmat: 矩阵大小
        matin1: 输入矩阵 (nf x nmat)
        nmat1, nx1, mx1, nmat2, nxu1: 未使用的参数
    
    返回:
        matout: 输出矩阵
    """
    matout = np.zeros((nf + 1, nmat + 1))
    
    for i in range(1, nmat + 1):
        for k in range(1, nmat + 1):
            matout[k, i] = matin1[k, i]
    
    return matout


def kolon1(omega=1.0):
    """
    更新求解变量，检查收敛性
    对应Fortran的KOLON1子程序
    
    参数:
        omega: 松弛因子 (0 < omega <= 1)，默认1.0（无松弛）
               较小的omega可以增加稳定性但减慢收敛速度
    """
    # 重置收敛标志 (KONVER=0表示已收敛或需要检查，KONVER=1表示未收敛)
    common.KONVER = 0
    
    # 确保omega在有效范围
    omega = max(0.1, min(1.0, omega))
    
    dtmax = 100.5
    dgmax1 = 0.051
    dgmax2 = 0.001
    dgmax3 = 0.02
    dgmax4 = 0.052
    dgmax5 = 0.008
    dgmax6 = 0.01
    dgmax7 = 0.1
    dgmax8 = 0.1
    dxmax = 0.051
    dwmax = 0.2
    
    # 检查组分流量收?
    sumfe = 0.0
    for i in range(common.NZEL1, common.NZEL2 + 1):
        for j in range(1, common.NVE + 1):
            sumfe = sumfe + abs(common.DMAT[j, i])
    
    if sumfe > common.SKONFE:
        common.KONVER = 1
    
    # 更新组分流量（带松弛因子）
    for i in range(common.NZEL1, common.NZEL2 + 1):
        # O2
        if abs(common.DMAT[1, i]) > dgmax1:
            common.FEMF[1, i] = common.FEMF[1, i] + omega * common.DMAT[1, i] * dgmax1 / abs(common.DMAT[1, i])
        else:
            common.FEMF[1, i] = common.FEMF[1, i] + omega * common.DMAT[1, i]
        
        # CH4
        if abs(common.DMAT[2, i]) > dgmax2:
            common.FEMF[2, i] = common.FEMF[2, i] + omega * common.DMAT[2, i] * dgmax2 / abs(common.DMAT[2, i])
        else:
            common.FEMF[2, i] = common.FEMF[2, i] + omega * common.DMAT[2, i]
        
        # CO
        if abs(common.DMAT[3, i]) > dgmax3:
            common.FEMF[3, i] = common.FEMF[3, i] + omega * common.DMAT[3, i] * dgmax3 / abs(common.DMAT[3, i])
        else:
            common.FEMF[3, i] = common.FEMF[3, i] + omega * common.DMAT[3, i]
        
        # CO2
        if abs(common.DMAT[4, i]) > dgmax4:
            common.FEMF[4, i] = common.FEMF[4, i] + omega * common.DMAT[4, i] * dgmax4 / abs(common.DMAT[4, i])
        else:
            common.FEMF[4, i] = common.FEMF[4, i] + omega * common.DMAT[4, i]
        
        # H2S
        if abs(common.DMAT[5, i]) > dgmax5:
            common.FEMF[5, i] = common.FEMF[5, i] + omega * common.DMAT[5, i] * dgmax5 / abs(common.DMAT[5, i])
        else:
            common.FEMF[5, i] = common.FEMF[5, i] + omega * common.DMAT[5, i]
        
        # H2
        if abs(common.DMAT[6, i]) > dgmax6:
            common.FEMF[6, i] = common.FEMF[6, i] + omega * common.DMAT[6, i] * dgmax6 / abs(common.DMAT[6, i])
        else:
            common.FEMF[6, i] = common.FEMF[6, i] + omega * common.DMAT[6, i]
        
        # N2
        if abs(common.DMAT[7, i]) > dgmax7:
            common.FEMF[7, i] = common.FEMF[7, i] + omega * common.DMAT[7, i] * dgmax7 / abs(common.DMAT[7, i])
        else:
            common.FEMF[7, i] = common.FEMF[7, i] + omega * common.DMAT[7, i]
        
        # H2O
        if abs(common.DMAT[8, i]) > dgmax8:
            common.FEMF[8, i] = common.FEMF[8, i] + omega * common.DMAT[8, i] * dgmax8 / abs(common.DMAT[8, i])
        else:
            common.FEMF[8, i] = common.FEMF[8, i] + omega * common.DMAT[8, i]
        
        # 确保非负
        for j in range(1, 9):
            if common.FEMF[j, i] < 0.0:
                common.FEMF[j, i] = 0.0
    
    # 检查碳质量流量收敛
    sumwe = 0.0
    ng1 = common.NVE + 1
    for i in range(common.NZEL1, common.NZEL2 + 1):
        sumwe = sumwe + abs(common.DMAT[common.NSGP, i])
    
    if sumwe > common.SKONWE:
        common.KONVER = 1
    
    # 更新碳质量流量（带松弛因子）
    for i in range(common.NZEL1, common.NZEL2 + 1):
        if abs(common.DMAT[common.NSGP, i]) > dwmax:
            common.WE[i] = common.WE[i] + omega * common.DMAT[common.NSGP, i] * dwmax / abs(common.DMAT[common.NSGP, i])
        else:
            common.WE[i] = common.WE[i] + omega * common.DMAT[common.NSGP, i]
        
        if common.WE[i] <= 0.0:
            common.WE[i] = 1.0e-20
    
    # 检查碳转化率收?
    sumx = 0.0
    ng1 = common.NSGP + 1
    for i in range(common.NZEL1, common.NZEL2 + 1):
        sumx = sumx + abs(common.DMAT[common.NSGP1, i])
    
    if sumx > common.SKONX:
        common.KONVER = 1
    
    # 更新碳转化率（带松弛因子）
    for i in range(common.NZEL1, common.NZEL2 + 1):
        if abs(common.DMAT[common.NSGP1, i]) > dxmax:
            common.X[i] = common.X[i] + omega * common.DMAT[common.NSGP1, i] * dxmax / abs(common.DMAT[common.NSGP1, i])
        else:
            common.X[i] = common.X[i] + omega * common.DMAT[common.NSGP1, i]
        
        if common.X[i] <= 0.0:
            common.X[i] = 1.0e-20
        if common.X[i] > 1.0:
            common.X[i] = 1.0
    
    # 检查温度收敛
    sumt = 0.0
    if common.KTRLT == 1:
        # FIXED: 使用NVWS而不是ng2作为温度方程索引
        # ng2 = NVE + 2 = 10 对应NSGP1 (碳转化率)
        # NVWS = 11 才是能量方程 (温度)
        nvws_idx = common.NVWS
        for i in range(common.NZEL1, common.NZEL2 + 1):
            sumt = sumt + abs(common.DMAT[nvws_idx, i])
        
        if sumt > common.SKONT:
            common.KONVER = 1
        
        # 更新温度（带松弛因子）
        for i in range(common.NZEL1, common.NZEL2 + 1):
            if abs(common.DMAT[nvws_idx, i]) > dtmax:
                common.T[i] = common.T[i] + omega * common.DMAT[nvws_idx, i] * dtmax / abs(common.DMAT[nvws_idx, i])
            else:
                common.T[i] = common.T[i] + omega * common.DMAT[nvws_idx, i]
            
            if common.T[i] > 3000.0:
                common.T[i] = 3000.0
    
    # 输出收敛信息
    if common.ITERAT == 1:
        print("\n  KONVER       SUMFE         SUMWE         SUMX          SUMT      ITERAT")
    
    print(f"  KONVER={common.KONVER} {sumfe:.4e} {sumwe:.4e} {sumx:.4e} {sumt:.4e}   {common.ITERAT}")
    
    # 保存求和值到common以便外部检查
    common.SUMFE = sumfe
    common.SUMWE = sumwe
    common.SUMX = sumx
    common.SUMT = sumt


def newtra(omega=1.0):
    """
    牛顿迭代
    对应Fortran的NEWTRA子程序
    
    参数:
        omega: 松弛因子 (0 < omega <= 1)，默认1.0（无松弛）
    
    注意：变量缩放在gasifier中应用，在blktrd中处理
    """
    if common.KTRLT == 1:
        neqn = common.NVWS
    else:
        neqn = common.NVWS - 1
    
    # 执行块三对角求解
    blktrd(neqn, common.NZEL2)
    
    # 应用松弛因子更新变量
    kolon1(omega=omega)


def blktrd(nmat, nst):
    """
    块三对角矩阵求解?
    对应Fortran的BLKTRD子程?
    
    参数:
        nmat: 矩阵大小
        nst: 格子?
    """
    nf = nmat
    is_err = 0
    
    zwmat = np.zeros((nmat + 1, nmat + 1))
    zwvek = np.zeros(nmat + 1)
    
    # BLKTRD块三对角求解
    
    # 前向消元
    for i in range(2, nst + 1):
        # AMAT(i-1) = AMAT(i-1) / BMAT(i-1)
        nfehl, matout = matdiv(
            nf, nmat,
            common.AMAT[:, :, i - 1], -nmat,
            common.BMAT[:, :, i - 1], -nmat,
            nmat, nmat
        )
        # matout为(nmat+1, nmat+1)形状，但AMAT需要(nmat+1, nmat+1)
        # 取有效部分
        common.AMAT[1:nmat+1, 1:nmat+1, i-1] = matout[1:nmat+1, 1:nmat+1]
        is_err = is_err + nfehl
        
        # ZWMAT = CMAT(i-1) * AMAT(i-1)
        zwmat = matmult(
            nf, nmat,
            common.CMAT[:, :, i - 1], nmat,
            common.AMAT[:, :, i - 1], nmat,
            nmat, nmat
        )
        
        # BMAT(i) = BMAT(i) - ZWMAT
        common.BMAT[:, :, i] = matsub(
            nf, nmat,
            common.BMAT[:, :, i], nmat,
            zwmat, nmat,
            nmat, nmat
        )
        
        # ZWVEK = DMAT(i-1) * AMAT(i-1)
        zwvek = matmult(
            nf, nmat,
            common.DMAT[:, i - 1:i], 1,
            common.AMAT[:, :, i - 1], nmat,
            1, nmat
        )
        
        # DMAT(i) = DMAT(i) - ZWVEK
        common.DMAT[:, i:i + 1] = matsub(
            nf, nmat,
            common.DMAT[:, i:i + 1], 1,
            zwvek.reshape(-1, 1), 1,
            1, 1
        )
    
    # 回代
    for k in range(1, nst + 1):
        i = nst + 1 - k
        
        if i != nst:
            # ZWVEK = DMAT(i+1) * CMAT(i)
            zwvek = matmult(
                nf, nmat,
                common.DMAT[:, i + 1:i + 2], 1,
                common.CMAT[:, :, i], nmat,
                1, nmat
            )
            
            # DMAT(i) = DMAT(i) - ZWVEK
            common.DMAT[:, i:i + 1] = matsub(
                nf, nmat,
                common.DMAT[:, i:i + 1], 1,
                zwvek.reshape(-1, 1), 1,
                1, 1
            )
        
        # DMAT(i) = DMAT(i) / BMAT(i)
        nfehl, matout = matdiv(
            nf, nmat,
            common.DMAT[:, i:i + 1], 1,
            common.BMAT[:, :, i], nmat,
            1, nmat
        )
        # matout为(nmat+1, 2)形状，数据在第1列（第二列）
        common.DMAT[1:nmat+1, i] = matout[1:nmat+1, 1]
        is_err = is_err + nfehl
    
    if is_err != 0:
        print(f"BLKTRD error! is_err={is_err}")
        sys.exit(1)
    
    return 0
