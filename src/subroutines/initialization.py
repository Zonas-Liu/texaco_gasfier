#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - 初始化和几何模块
对应Fortran的Wg2.for
包含子程序:
- EINGAB: 输入数据和初始化
- GEOMETRY: 计算几何结构
- QHCRCT: 热量校正计算
"""
import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.common_data import common


def eingab(data_path='data/Datain0.dat'):
    """
    输入数据和初始化子程序
    对应Fortran的EINGAB子程序
    
    参数:
        data_path: 输入数据文件路径(相对项目根目录)
    
    功能:
        - 读取输入参数文件
        - 设置分子量和基本参数
        - 计算派生量(流量、几何等)
        - 调用GEOMETRY和QHCRCT
        - 初始化未知数
    """
    # 设置分子量 (DATA语句) [kg/kmol]
    # XMOL: O2, CH4, CO, CO2, H2S, H2, N2, H2O, C, TAR
    common.XMOL = np.array([32., 16., 28., 44., 34., 2., 28., 18., 12., 60.])
    common.XMTAR = 12.913  # 焦油分子量
    
    # 设置基本控制参数
    common.KCHECK = 0  # 与Fortran一致 (Wg2.for line 17)
    common.KTRLT = 1
    common.KTRLR = 1
    common.NZWS = 30
    # 注意: 使用0-based索引 (Fortran使用1-based)
    # 转换关系: Python_index = Fortran_index - 1
    common.NZEL1 = 1   # Fortran NZEL1=1 (1-based indexing)
    common.NZEL2 = 30  # Fortran NZEL2=30
    common.NZRE = 30   # Fortran NZRE=30
    
    # 设置结构参数 (炉子分段边界)
    common.NZR1 = 29  # Fortran 29
    common.NZR2 = 27  # Fortran 27
    common.NZR3 = 25  # Fortran 25
    common.NZR4 = 23  # Fortran 23
    common.NZR5 = 16  # Fortran 16
    common.NZR6 = 9   # Fortran 9
    common.NZR7 = 5   # Fortran 5
    
    # 进料相关参数
    common.N2FED = 6  # Fortran N2FED=7
    common.NZRA = 1   # Fortran NZRA=1 (1-based indexing)
    common.NPRIX = 1  # Fortran NPRIX=1
    nzfed0 = 1  # Fortran nzfed0=1 (number of feed cells)
    
    # 反应控制参数
    common.KTRL_XK1 = 1
    common.KTRL_XK2 = 1
    common.KTRL_XK3 = 3
    common.KTRL_XK4 = 1
    common.KTRL_XK5 = 3
    
    # 控制系数
    common.CTRL_A1 = 0.28
    common.CTRL_A2 = 1.0
    common.CTRL_A3 = 1.0
    common.CTRL_A4 = 0.23
    common.CTRL_A5 = 1.0
    
    # 系数
    common.COEF_A1 = 0.1
    common.COEF_A2 = 0.1
    common.COEF_A3 = 0.1
    common.COEF_A4 = 0.1
    
    # 密度参数
    common.RO_SLURRY = 1260.0
    common.ROS0 = 1260.0
    common.QH_CRCT = 0.0
    
    # 读取输入数据文件
    # 使用项目根目录作为基准
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_data_path = os.path.join(project_root, data_path)
    
    with open(full_data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 解析输入数据(每行格式: value1,value2,.../----comment)
    def parse_line(line):
        """解析数据行,提取数值"""
        # 移除注释部分
        if '/' in line:
            line = line.split('/')[0]
        # 分割并转换为浮点数
        values = []
        for v in line.strip().split(','):
            v = v.strip()
            if v:
                # 处理Fortran科学计数法格式(D+05 -> E+05)
                v = v.replace('D', 'E').replace('d', 'e')
                values.append(float(v))
        return values
    
    # 读取各参数
    # Line 1: KTRL
    values = parse_line(lines[0])
    common.KTRL = int(values[0])
    
    # Line 2: ITMAX, SKONFE, SKONWE, SKONX, SKONT
    values = parse_line(lines[1])
    common.ITMAX = int(values[0])
    common.SKONFE = values[1]
    common.SKONWE = values[2]
    common.SKONX = values[3]
    common.SKONT = values[4]
    
    # Line 3: BSLURRY, RATIO_COAL
    values = parse_line(lines[2])
    common.BSLURRY = values[0]
    common.RATIO_COAL = values[1]
    
    # Line 4: FOXY, PURE_O2, OX_PART, RATIO_CO2
    values = parse_line(lines[3])
    common.FOXY = values[0]
    common.PURE_O2 = values[1]
    common.OX_PART = values[2]
    common.RATIO_CO2 = values[3]
    
    # Line 5: PFEED_SL, TFEED_SL, PFEED_OX, TFEED_OX
    values = parse_line(lines[4])
    common.PFEED_SL = values[0]
    common.TFEED_SL = values[1]
    common.PFEED_OX = values[2]
    common.TFEED_OX = values[3]
    
    # Line 6: PFEED_CO2, TFEED_CO2
    values = parse_line(lines[5])
    common.PFEED_CO2 = values[0]
    common.TFEED_CO2 = values[1]
    
    # Line 7: DP
    values = parse_line(lines[6])
    common.DP = values[0]
    
    # Line 8: HU, XVM
    values = parse_line(lines[7])
    common.HU = values[0]
    common.XVM = values[1]
    
    # Line 9: ELC, ELH, ELO, ELN, ELS, ELAS, ELH2O
    values = parse_line(lines[8])
    common.ELC = values[0]
    common.ELH = values[1]
    common.ELO = values[2]
    common.ELN = values[3]
    common.ELS = values[4]
    common.ELAS = values[5]
    common.ELH2O = values[6] if len(values) > 6 else 0.0
    
    # Line 10: TU, TW, PWK
    values = parse_line(lines[9])
    common.TU = values[0]
    common.TW = values[1]
    common.PWK = values[2]
    
    # Line 11: QLOSS
    values = parse_line(lines[10])
    common.QLOSS = values[0]
    
    print('END OF INPUT DATA!!')
    
    # 计算结构参数
    common.NVE = common.NGAS        # 气体组分数 = 8
    common.NSGP = common.NVE + 1    # NSGP = 9
    common.NSGP1 = common.NSGP + 1  # NSGP1 = 10
    
    # 根据KTRLT计算变量数NVAR
    if common.KTRLT == 1:
        common.NVAR = common.NSGP1 + 1  # NVAR = 11
    else:
        common.NVAR = common.NSGP1      # NVAR = 10
    
    common.NVWS = common.NVAR
    common.NZFR = common.NPRIX - common.NZRA + 1  # NZFR = number of cells in volatile release zone (Fortran compatible)
    common.NZFED = nzfed0                     # NZFED = nzfed0 (1-based, compatible with Fortran DO I=NZRA,NZFED)
    
    # 调用几何计算
    geometry()
    
    # 计算质量流量
    # BSMS: 干煤质量流量 [kg/s]
    common.BSMS = common.BSLURRY * common.RATIO_COAL
    
    # BSWAF: 干煤+灰分(除去水和灰分后的煤)质量流量 [kg/s]
    common.BSWAF = common.BSMS * (1.0 - common.ELH2O - common.ELAS)
    
    # FOX: 氧气体积流量 [Nm3/s]
    common.FOX = (common.FOXY * common.BSWAF / 32.0 / common.PURE_O2 * 22.4)
    
    # GFOX: 氧气质量流量 [kg/s]
    common.GFOX = common.FOX * (common.PURE_O2 * 32.0 + (1.0 - common.PURE_O2) * 28.0) / 22.4
    
    # FCO2: CO2体积流量 [Nm3/s]
    fco2 = common.FOX * common.RATIO_CO2
    
    # GFCO2: CO2质量流量 [kg/s]
    gfco2 = fco2 / 22.4 * 44.0
    
    # 计算进料分配 (循环I=NZRA到NZFED,即第1个格子)
    # 注意: Fortran使用1-based索引,Python使用0-based但保持数组大小为31来兼容
    for i in range(common.NZRA, common.NZFED + 1):
        # WFA: 灰分质量流量 [kg/s]
        common.WFA[i] = common.ELAS * common.BSMS * common.DELZ[i] / common.HFED
        
        # WFC: 固定碳质量流量 [kg/s]
        common.WFC[i] = common.ELC * common.BSMS * common.DELZ[i] / common.HFED
        
        # FEEDO2: O2进料 [kmol/s]
        common.FEEDO2[i] = (common.FOX * common.PURE_O2 / 22.4 * 
                           common.DELZ[i] / common.HFED * common.OX_PART)
        
        # FEEDN2: N2进料 [kmol/s]
        common.FEEDN2[i] = (common.FOX * (1.0 - common.PURE_O2) / 22.4 * 
                           common.DELZ[i] / common.HFED)
        
        # FEDCO2: CO2进料 [kmol/s]
        common.FEDCO2[i] = common.FOX * common.RATIO_CO2 / 22.4 * common.DELZ[i] / common.HFED
        
        # FEDH2O: H2O进料 [kmol/s]
        common.FEDH2O[i] = ((common.BSLURRY * (1.0 - common.RATIO_COAL) + 
                            common.ELH2O * common.BSMS) / 18.0 * 
                           common.DELZ[i] / common.HFED)
    
    # 第二个进料点的氧气 (N2FED=7)
    h_n2fed_diff = common.H[common.N2FED] - common.H[common.N2FED + 1]
    if abs(h_n2fed_diff) > 1e-10:
        common.FEEDO2[common.N2FED] = (common.FOX * common.PURE_O2 / 22.4 * 
                                       common.DELZ[common.N2FED] / h_n2fed_diff * 
                                       (1.0 - common.OX_PART))
    
    # 调用FLUCHT (挥发分释放计算)
    from functions.gas_reactions import flucht
    flucht()
    
    # 调用热量校正
    qhcrct()
    
    # 初始化未知数
    if common.KTRL == 0:
        # 从START.DAT读取初始值
        start_path = os.path.join(project_root, 'data/START.DAT')
        _read_start_file(start_path)
    elif common.KCHECK == 1:
        # 检查模式初始化
        for i in range(common.NZRA, common.NZRE + 1):
            common.FEMF[1, i] = common.FEEDO2[0] + common.RO2[0]
            common.FEMF[2, i] = 0.0/1000.0*4.0 + common.KCHECK * common.RVCH4[0]
            common.FEMF[3, i] = 0.0/1000.0*4.0 + common.KCHECK * common.RCO[0]
            common.FEMF[4, i] = 0.0/1000.0*4.0 + common.KCHECK * common.RCO2[0]
            common.FEMF[5, i] = 0.0/1000.0*4.0 + common.KCHECK * common.RH2S[0]
            common.FEMF[6, i] = 0.0/1000.0*4.0 + common.KCHECK * (common.RH2[0] + common.RVH2[0])
            # Fortran: FEMF(7,I)=GFOX*(1.0-PURE_O2)/28.0/NZFED + KCHECK*REN2(1)
            # Note: NZFED in Fortran is 1-based count (NZRA=1 to NZFED=1 means 1 cell)
            nzed = common.NZFED - common.NZRA + 1  # Number of feed cells
            common.FEMF[7, i] = (common.GFOX * (1.0 - common.PURE_O2) / 28.0 / nzed + 
                                common.KCHECK * common.REN2[0])
            # Fortran: FEMF(8,I)=(BSLURRY*(1.0-RATIO_COAL)+ELH2O*BSMS)/18.0/NZFED + KCHECK*RVH2O(1)
            common.FEMF[8, i] = ((common.BSLURRY * (1.0 - common.RATIO_COAL) + 
                                 common.ELH2O * common.BSMS) / 18.0 / nzed + 
                                common.KCHECK * common.RVH2O[0])
            common.T[i] = 298.15
            common.X[i] = common.WFC[0] / (common.WFA[0] + common.WFC[0])
            common.WE[i] = common.WFA[0] + common.WFC[0] + common.RVTAR[0] * common.XMTAR
    else:
        # 默认初始化
        for i in range(common.NZRA, common.NZRE + 1):
            common.FEMF[1, i] = 0.555249e-02
            common.FEMF[2, i] = 0.065000 + common.KCHECK * common.RVCH4[0]
            common.FEMF[3, i] = 0.129528e+00 / 2.0 + common.KCHECK * common.RCO[0]
            common.FEMF[4, i] = 0.468267e-01 + common.KCHECK * common.RCO2[0]
            common.FEMF[5, i] = 0.104452e-02 + common.KCHECK * common.RH2S[0]
            common.FEMF[6, i] = 0.137525e-01 * 2.0 + common.KCHECK * (common.RH2[0] + common.RVH2[0])
            nzed = common.NZFED - common.NZRA + 1  # Number of feed cells
            common.FEMF[7, i] = (common.GFOX * (1.0 - common.PURE_O2) / 28.0 / nzed + 
                                common.KCHECK * common.REN2[0])
            common.FEMF[8, i] = ((common.BSLURRY * (1.0 - common.RATIO_COAL) + 
                                 common.ELH2O * common.BSMS) / 18.0 / nzed + 
                                common.KCHECK * common.RVH2O[0])
            common.T[i] = 1500.0
            common.X[i] = 0.0665412e+00
            common.WE[i] = 0.5217118
    
    # 输出信息
    print('\n4. 进料参数')
    print(f'     水煤浆浓度:           {common.RATIO_COAL*100.:15.6f} %')
    print(f'     干煤量:               {common.BSMS:15.6f} KG/S')
    print(f'     氧煤比:               {common.FOXY:15.6f} KG O2/KG BSWAF')
    print(f'     氧气体积流量:         {common.FOX:15.6f} NM3/S')
    print(f'     一次氧气比例:         {common.OX_PART:15.6f}')
    print(f'     CO2比例:              {common.RATIO_CO2:15.6f}')
    print(f'     二次进料所在小格号:   {common.N2FED:15d}')
    
    print('???????????????  END OF EINGAB  ???????????????')


def _read_start_file(filepath):
    """
    从START.DAT读取初始值
    对应Fortran中KTRL=0时的文件读取部分
    
    Fortran读取顺序:
    READ(4,*)((FEMF(II,I),II=1,4),I=NZEL1,NZEL2)  - 先遍历格子,再遍历组分1-4
    READ(4,*)((FEMF(II,I),II=5,8),I=NZEL1,NZEL2)  - 先遍历格子,再遍历组分5-8
    READ(4,*)(T(I),I=NZEL1,NZEL2)
    READ(4,*)(X(I),I=NZEL1,NZEL2)
    READ(4,*)(WE(I),I=NZEL1,NZEL2)
    """
    try:
        # Read all values from file (flattened list)
        all_values = []
        with open(filepath, 'r') as f:
            for line in f:
                # Split line by whitespace and convert to float
                values = [float(x) for x in line.strip().split()]
                all_values.extend(values)
        
        val_idx = 0
        
        # 读取FEMF(1:4, :) - Fortran顺序: 外层I(格子),内层II(组分)
        # 即: FEMF(1,1), FEMF(2,1), FEMF(3,1), FEMF(4,1), FEMF(1,2), FEMF(2,2)...
        for i in range(common.NZEL1, common.NZEL2 + 1):
            for ii in range(1, 5):
                if val_idx < len(all_values):
                    common.FEMF[ii, i] = all_values[val_idx]
                    val_idx += 1
        
        # 读取FEMF(5:8, :) 
        for i in range(common.NZEL1, common.NZEL2 + 1):
            for ii in range(5, 9):
                if val_idx < len(all_values):
                    common.FEMF[ii, i] = all_values[val_idx]
                    val_idx += 1
        
        # 读取T(温度)
        for i in range(common.NZEL1, common.NZEL2 + 1):
            if val_idx < len(all_values):
                common.T[i] = all_values[val_idx]
                val_idx += 1
        
        # 读取X(碳转化率)
        for i in range(common.NZEL1, common.NZEL2 + 1):
            if val_idx < len(all_values):
                common.X[i] = all_values[val_idx]
                val_idx += 1
        
        # 读取WE(碳质量流量)
        for i in range(common.NZEL1, common.NZEL2 + 1):
            if val_idx < len(all_values):
                common.WE[i] = all_values[val_idx]
                val_idx += 1
        
        print(f'Read {val_idx} values from START.DAT')
                
    except FileNotFoundError:
        print(f'Warning: START.DAT not found at {filepath}')
        print('Using default initialization instead.')
        common.KTRL = 1  # 切换到默认初始化
    except Exception as e:
        print(f'Error reading START.DAT: {e}')
        print('Using default initialization instead.')
        common.KTRL = 1  # 切换到默认初始化


def geometry():
    """
    计算气化炉几何结构
    对应Fortran的GEOMETRY子程序
    
    功能:
        - 设置8个不同直径的炉段
        - 计算每个格子的高度DELZ和位置H
        - 计算每个格子的截面积AT和周长AR
    
    炉子结构(从顶部到底部):
        HREAK1=0.4m,    DIA1=1.005m,   NZRE=30 到 NZR1=29
        HREAK2=0.4m,    DIA2=0.935m,   NZR1-1=28 到 NZR2=27
        HREAK3=0.1926m, DIA3=1.175m,   NZR2-1=26 到 NZR3=25
        HREAK4=0.1926m, DIA4=1.725m,   NZR3-1=24 到 NZR4=23
        HREAK5=3.4m,    DIA5=2.0m,     NZR4-1=22 到 NZR5=16
        HREAK6=3.4m,    DIA6=2.0m,     NZR5-1=15 到 NZR6=9
        HREAK7=0.1876m, DIA7=1.675m,   NZR6-1=8 到 NZR7=5
        HREAK8=0.1876m, DIA8=1.025m,   NZR7-1=4 到 NZRA=1
    """
    # 各段高度 [m]
    hreak1 = 0.4
    hreak2 = 0.4
    hreak3 = 0.1926
    hreak4 = 0.1926
    hreak5 = 3.4
    hreak6 = 3.4
    hreak7 = 0.1876
    hreak8 = 0.1876
    
    # 总高度
    common.HREAK = hreak1 + hreak2 + hreak3 + hreak4 + hreak5 + hreak6 + hreak7 + hreak8
    
    # 各段直径 [m]
    common.DIA1 = 1.005
    common.DIA2 = 0.935
    common.DIA3 = 1.175
    common.DIA4 = 1.725
    common.DIA5 = 2.0
    common.DIA6 = 2.0
    common.DIA7 = 1.675
    common.DIA8 = 1.025
    
    # 初始化数组
    for i in range(common.NZEL1, common.NZEL2 + 1):
        common.DELZ[i] = 0.0
        common.H[i] = 0.0
        common.AT[i] = 0.0
        common.AR[i] = 0.0
    
    # 第1段: NZRE=30 到 NZR1=29 (顶部最窄段)
    # 使用DIA1, HREAK1
    n_cells_1 = common.NZRE - common.NZR1 + 1  # = 2个格子
    for i in range(common.NZRE, common.NZR1 - 1, -1):
        common.DELZ[i] = hreak1 / n_cells_1
        common.H[i] = common.DELZ[i] * (common.NZRE - i + 1)
        common.AT[i] = common.DIA1 * common.DIA1 * common.PI / 4.0
        common.AR[i] = common.DIA1 * common.PI
    
    # 第2段: NZR1-1=28 到 NZR2=27
    # 使用DIA2, HREAK2
    n_cells_2 = common.NZR1 - common.NZR2  # = 2个格子
    for i in range(common.NZR1 - 1, common.NZR2 - 1, -1):
        common.DELZ[i] = hreak2 / n_cells_2
        common.H[i] = hreak1 + common.DELZ[i] * (common.NZR1 - i)
        common.AT[i] = common.DIA2 * common.DIA2 * common.PI / 4.0
        common.AR[i] = common.DIA2 * common.PI
    
    # 第3段: NZR2-1=26 到 NZR3=25
    # 使用DIA3, HREAK3
    n_cells_3 = common.NZR2 - common.NZR3  # = 2个格子
    for i in range(common.NZR2 - 1, common.NZR3 - 1, -1):
        common.DELZ[i] = hreak3 / n_cells_3
        common.H[i] = hreak1 + hreak2 + common.DELZ[i] * (common.NZR2 - i)
        common.AT[i] = common.DIA3 * common.DIA3 * common.PI / 4.0
        common.AR[i] = common.DIA3 * common.PI
    
    # 第4段: NZR3-1=24 到 NZR4=23
    # 使用DIA4, HREAK4
    n_cells_4 = common.NZR3 - common.NZR4  # = 2个格子
    for i in range(common.NZR3 - 1, common.NZR4 - 1, -1):
        common.DELZ[i] = hreak4 / n_cells_4
        common.H[i] = hreak1 + hreak2 + hreak3 + common.DELZ[i] * (common.NZR3 - i)
        common.AT[i] = common.DIA4 * common.DIA4 * common.PI / 4.0
        common.AR[i] = common.DIA4 * common.PI
    
    # 第5段: NZR4-1=22 到 NZR5=16
    # 使用DIA5, HREAK5
    n_cells_5 = common.NZR4 - common.NZR5  # = 7个格子
    for i in range(common.NZR4 - 1, common.NZR5 - 1, -1):
        common.DELZ[i] = hreak5 / n_cells_5
        common.H[i] = hreak1 + hreak2 + hreak3 + hreak4 + common.DELZ[i] * (common.NZR4 - i)
        common.AT[i] = common.DIA5 * common.DIA5 * common.PI / 4.0
        common.AR[i] = common.DIA5 * common.PI
    
    # 第6段: NZR5-1=15 到 NZR6=9
    # 使用DIA6, HREAK6
    n_cells_6 = common.NZR5 - common.NZR6  # = 7个格子
    for i in range(common.NZR5 - 1, common.NZR6 - 1, -1):
        common.DELZ[i] = hreak6 / n_cells_6
        common.H[i] = (hreak1 + hreak2 + hreak3 + hreak4 + hreak5 + 
                      common.DELZ[i] * (common.NZR5 - i))
        common.AT[i] = common.DIA6 * common.DIA6 * common.PI / 4.0
        common.AR[i] = common.DIA6 * common.PI
    
    # 第7段: NZR6-1=8 到 NZR7=5
    # 使用DIA7, HREAK7
    n_cells_7 = common.NZR6 - common.NZR7  # = 4个格子
    for i in range(common.NZR6 - 1, common.NZR7 - 1, -1):
        common.DELZ[i] = hreak7 / n_cells_7
        common.H[i] = (hreak1 + hreak2 + hreak3 + hreak4 + hreak5 + hreak6 + 
                      common.DELZ[i] * (common.NZR6 - i))
        common.AT[i] = common.DIA7 * common.DIA7 * common.PI / 4.0
        common.AR[i] = common.DIA7 * common.PI
    
    # 第8段: NZR7-1=4 到 NZRA=1 (底部段)
    # 使用DIA8, HREAK8
    n_cells_8 = common.NZR7 - common.NZRA  # = 4个格子
    # 手动处理以包含index 4（Fortran Cell 4）到index 1（Fortran Cell 1）
    for i in [4, 3, 2, 1]:
        common.DELZ[i] = hreak8 / n_cells_8
        common.H[i] = (hreak1 + hreak2 + hreak3 + hreak4 + hreak5 + hreak6 + hreak7 + 
                      common.DELZ[i] * (common.NZR7 - i))
        common.AT[i] = common.DIA8 * common.DIA8 * common.PI / 4.0
        common.AR[i] = common.DIA8 * common.PI
    
    # 计算HNZFR和HFED
    common.HNZFR = 0.0
    for i in range(common.NZRA, common.NZFR + 1):
        common.HNZFR += common.DELZ[i]
    
    common.HFED = 0.0
    for i in range(common.NZRA, common.NZFED + 1):
        common.HFED += common.DELZ[i]


def qhcrct():
    """
    热量校正计算
    对应Fortran的QHCRCT子程序
    
    功能:
        - 计算挥发分释放的热量校正QH_CRCT
        - 计算热解后的焓值
        - 用于能量平衡计算
    
    注意:
        该函数依赖于ENTHP函数(在Wg7.for中定义)
        由于依赖关系,ENTHP的调用暂时注释,需要时取消注释
    """
    # 累加各格子中的挥发分释放量
    rco21 = 0.0   # CO2总释放量
    rco1 = 0.0    # CO总释放量
    rvch41 = 0.0  # CH4总释放量
    rvtar1 = 0.0  # 焦油总释放量
    rh2s1 = 0.0   # H2S总释放量
    rh2o1 = 0.0   # H2O总释放量
    
    for i in range(common.NZRA, common.NZRE + 1):
        rco21 += common.RCO2[i]
        rco1 += common.RCO[i]
        rvch41 += common.RVCH4[i]
        rvtar1 += common.RVTAR[i]
        rh2s1 += common.RH2S[i]
        rh2o1 += common.RVH2O[i]
    
    # 计算有效热值HUU [kJ/kg]
    # 使用标准生成焓计算
    huu = (((common.ELC / 12.0) * common.BSMS * (-393.6933) +
            (common.ELH / 2.0 - common.ELS / 32.0) * common.BSMS * (-286.5) -
            rco21 * common.BSMS * (-393.6933) -
            rco1 * common.BSMS * (-110.59412) -
            rvch41 * common.BSMS * (-74.84568) -
            rvtar1 * common.BSMS * (-9.3)) / common.BSMS * 1000.0 -
            rh2s1 * (-20.18))
    
    # 热量校正 [J/kg]
    common.QH_CRCT = (huu + common.HU) * 1000.0
    
    # 计算热解后的焓值 (需要ENTHP函数)
    # 由于ENTHP在Wg7.for中,暂时使用近似值
    # 当Wg7.for翻译完成后,可以取消以下注释:
    
    # from functions.thermodynamics import enthp
    # hf_h2o1 = enthp(8, 'L', 298.15, common.PWK) / 1.0e6
    
    # 使用H2O在298.15K的近似焓值 [MJ/kmol]
    hf_h2o1 = -0.28583  # H2O(l)的标准生成焓近似值 [MJ/kmol]
    
    # 热解后混合物的焓 [MJ/kmol]
    h_in = (rvch41 * (-74.84568) + 
            rco1 * (-110.59412) + 
            rco21 * (-393.6933) + 
            rh2o1 * hf_h2o1 + 
            rh2s1 * (-20.18) + 
            rvtar1 * (-9.3))
    
    # 计算产物焓值
    co2_out = common.ELC * common.BSMS / 12.0
    h2o_out = common.ELH * common.BSMS / 2.0 - rh2s1
    
    h_prdct = co2_out * (-393.6933) + h2o_out * hf_h2o1 + rh2s1 * (-20.18)
    
    # 焓差 [MJ/kg]
    delth = (h_prdct - h_in) / common.BSMS
    
    # 反应热 [MJ/kg]
    h_ract = common.HU / 1000.0
    
    # 这些值可以用于后续的能量平衡检查
    # 存储在common中供其他函数使用
    common.DELTH = delth
    common.H_RACT = h_ract
    common.H_IN = h_in


# 为向后兼容提供别名
eingabe = eingab


if __name__ == '__main__':
    # 测试代码
    print("Testing initialization module...")
    
    # 测试GEOMETRY
    print("\n1. Testing GEOMETRY...")
    geometry()
    print(f"   HREAK = {common.HREAK:.4f} m")
    print(f"   DIA1 = {common.DIA1:.4f} m, DIA8 = {common.DIA8:.4f} m")
    print(f"   DELZ[0] = {common.DELZ[0]:.6f} m, DELZ[29] = {common.DELZ[29]:.6f} m")
    print(f"   AT[0] = {common.AT[0]:.6f} m^2, AT[29] = {common.AT[29]:.6f} m^2")
    print(f"   HFED = {common.HFED:.4f} m, HNZFR = {common.HNZFR:.4f} m")
    
    # 测试EINGAB
    print("\n2. Testing EINGAB...")
    eingab()
    print(f"   BSMS = {common.BSMS:.4f} kg/s")
    print(f"   FOX = {common.FOX:.6f} Nm3/s")
    print(f"   GFOX = {common.GFOX:.4f} kg/s")
    print(f"   FEMF[1,0] = {common.FEMF[1,0]:.6e}")
    print(f"   T[0] = {common.T[0]:.2f} K")
    
    # 测试QHCRCT
    print("\n3. Testing QHCRCT...")
    qhcrct()
    print(f"   QH_CRCT = {common.QH_CRCT:.4f} J/kg")
    
    print("\nAll tests completed!")
