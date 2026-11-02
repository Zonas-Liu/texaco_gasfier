#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - Common块Python实现
对应Fortran中的Common.00, Common.01, Common.02, Common.03
"""
import numpy as np


class CommonData:
    """
    单例类，用于存储全局共享数据，对应Fortran的Common块
    """
    _instance = None

    # 数组维度常量: 燃烧室30格 + RSC段最多30格 + 1个闲置的0号索引
    NZDIM = 61
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def reset(self):
        """原位清空计算状态，保留所有模块持有的单例引用。"""
        self.__dict__.clear()
        self._initialized = False
        self.__init__()

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.init_parameters()
        self.init_structure()
        self.init_geometry()
        self.init_coal()
        self.init_unknowns()
        self.init_flow()
        self.init_feed()
        self.init_volatile()
        self.init_enthalpy()
        self.init_matrix()
    
    def init_parameters(self):
        """Common.00 - 基本参数"""
        # 物理常数
        self.NGAS = 8              # 气体组分数
        self.G = 9.801             # 重力加速度 [m/s^2]
        self.RAG = 8314.3          # 通用气体常数 [J/(kmol·K)]
        self.PI = 3.1415926        # 圆周率
        self.P0 = 1.01325e5        # 标准大气压 [Pa]
    
    def init_structure(self):
        """Common.00 - 结构参数和控制变量"""
        # 格子结构参数
        self.NZWS = 30
        self.NZEL1 = 1   # Fortran NZEL1=1 (1-based indexing)
        self.NZEL2 = 30  # Fortran NZEL2=30 (30 cells)
        self.NZRA = 1  # Fortran NZRA=1 (1-based indexing)
        self.NZR1 = 29
        self.NZR2 = 27
        self.NZR3 = 25
        self.NZRE = 30  # Fortran NZRE=30 (1-based, cells 1-30)
        self.NZRC = 30  # 燃烧室出口格号 (晋华炉: RSC段从NZRC+1开始)
        
        self.NPRIX = 1
        self.NZFR = 0
        self.NZFED = 0
        self.N2FED = 7  # 与 Fortran N2FED=7 保持一致
        self.NZR4 = 23
        self.NZR5 = 16
        self.NZR6 = 9
        self.NZR7 = 5
        
        # 数值参数
        self.NVAR = 0
        self.NVE = 0
        self.NVWS = 0
        self.NSGP = 0
        self.NSGP1 = 0
        
        # 控制参数
        self.KCHECK = 0
        self.KTRL = 0
        self.KTRLT = 1
        self.KTRLR = 1
        
        # 反应控制参数
        self.KTRL_XK1 = 1
        self.KTRL_XK2 = 1
        self.KTRL_XK3 = 3
        self.KTRL_XK4 = 1
        self.KTRL_XK5 = 3
        
        self.CTRL_A1 = 0.28
        self.CTRL_A2 = 1.0
        self.CTRL_A3 = 1.0
        self.CTRL_A4 = 0.23
        self.CTRL_A5 = 1.0
        
        # 煤种
        self.NCOAL = 1
        
        # 收敛控制
        self.KONVER = 0
        self.ITERAT = 0
        self.ITMAX = 150
        self.SKONFE = 5.0e-4
        self.SKONWE = 5.0e-4
        self.SKONX = 5.0e-4
        self.SKONT = 5.0e-3
    
    def init_geometry(self):
        """Common.01 - 几何参数"""
        self.H = np.zeros(self.NZDIM)          # 格子高度位置 [m] (1-based in Fortran)
        self.DELZ = np.zeros(self.NZDIM)       # 格子高度 [m]
        self.AT = np.zeros(self.NZDIM)         # 格子截面积 [m^2]
        self.AR = np.zeros(self.NZDIM)         # 格子半径 [m]
        self.HREAK = 0.0               # 炉总高度 [m]
        self.DIA1 = 0.0                # 炉直径 [m]
        self.DIA2 = 0.0
        self.DIA3 = 0.0
        self.DIA4 = 0.0
        self.DIA5 = 0.0
        self.DIA6 = 0.0
        self.DIA7 = 0.0
        self.DIA8 = 0.0
        self.HNZFR = 0.0
        self.HFED = 0.0
    
    def init_coal(self):
        """Common.01 - 煤性质和操作参数"""
        # 煤性质 (默认值，实际从DAT文件读取)
        self.HU = 25900                # 热值 [J/kg]
        self.XVM = 0.28                # 挥发分含量
        self.ELC = 0.6802              # C元素含量
        self.ELH = 0.0404              # H元素含量
        self.ELO = 0.0985              # O元素含量
        self.ELN = 0.0249              # N元素含量
        self.ELS = 0.006               # S元素含量
        self.ELAS = 0.15               # 灰分含量
        self.ELH2O = 0.0               # 水分含量
        
        # 进料参数 (默认值，实际从DAT文件读取)
        self.BSLURRY = 15.98           # 水煤浆流量 [kg/s]
        self.BSMS = 0.0                # 干煤流量 [kg/s]
        self.RATIO_COAL = 0.59         # 煤浆浓度
        self.DP = 100.0e-6             # 煤颗粒直径 [m]
        self.RO_SLURRY = 1260.0        # 煤浆密度 [kg/m^3]
        self.ROS0 = 1260.0             # 煤密度 [kg/m^3]
        self.BSWAF = 0.0               # 干煤+灰分流量 [kg/s]
        
        # 氧气参数 (默认值，实际从DAT文件读取)
        self.FOX = 0.0                 # 氧气体积流量 [Nm^3/s]
        self.GFOX = 0.0                # 氧气质量流量 [kg/s]
        self.PURE_O2 = 0.996           # 氧气纯度
        self.OX_PART = 1.0             # 氧气比例
        self.RATIO_CO2 = 0.0           # CO2比例
        self.FOXY = 1.06               # 氧气过剩系数
        
        # 密度和粘度
        self.ROS = np.zeros(self.NZDIM)        # 固体密度 [kg/m^3]
        self.ROG = np.zeros(self.NZDIM)        # 气体密度 [kg/m^3]
        self.XMUG = np.zeros(self.NZDIM)       # 气体粘度 [Pa·s]
        
        # 系统压力 (默认值，实际从DAT文件读取)
        self.PWK = 67.0e5              # 工作压力 [Pa] (67.0D05 in DAT file)
        
        # 收敛参数
        self.XCVM0 = 0.0
        self.XC0 = 0.0
        
        # 分子量 [kg/kmol]
        self.XMOL = np.array([32., 16., 28., 44., 34., 2., 28., 18., 12., 60.])
        self.XMTAR = 12.913            # 焦油分子量
        
        # 系数
        self.COEF_A1 = 0.1
        self.COEF_A2 = 0.1
        self.COEF_A3 = 0.1
        self.COEF_A4 = 0.1
    
    def init_unknowns(self):
        """Common.02 - 求解变量"""
        # 未知数 (NGAS=8, NZWS=30)
        self.FEMF = np.zeros((9, self.NZDIM))     # 各组分摩尔流量 [kmol/s] (1-based)
        self.X = np.zeros(self.NZDIM)              # 碳转化率
        self.T = np.zeros(self.NZDIM)              # 温度 [K]
        self.WE = np.zeros(self.NZDIM)             # 碳质量流量 [kg/s]
        
        # 流动参数
        self.FEM = np.zeros(self.NZDIM)            # 总摩尔流量 [kmol/s]
        self.U0 = np.zeros(self.NZDIM)             # 气体速度 [m/s]
        self.US = np.zeros(self.NZDIM)             # 颗粒速度 [m/s]
        self.TRZ = np.zeros(self.NZDIM)            # 停留时间 [s]
        self.XMS = np.zeros(self.NZDIM)            # 格子内固体质量 [kg]
        self.EPS = np.zeros(self.NZDIM)            # 空隙率
    
    def init_flow(self):
        """Common.02 - 流动参数"""
        self.FEM = np.zeros(self.NZDIM)            # 总摩尔流量 [kmol/s]
        self.U0 = np.zeros(self.NZDIM)             # 气体速度 [m/s]
        self.US = np.zeros(self.NZDIM)             # 颗粒速度 [m/s]
        self.TRZ = np.zeros(self.NZDIM)            # 停留时间 [s]
        self.XMS = np.zeros(self.NZDIM)            # 格子内固体质量 [kg]
        self.EPS = np.zeros(self.NZDIM)            # 空隙率
    
    def init_feed(self):
        """Common.02 - 进料参数"""
        self.FEDH2O = np.zeros(self.NZDIM)         # H2O进料 [kmol/s]
        self.WFA = np.zeros(self.NZDIM)            # 灰分质量流量 [kg/s]
        self.WFC = np.zeros(self.NZDIM)            # 固定碳质量流量 [kg/s]
        self.FEEDO2 = np.zeros(self.NZDIM)         # O2进料 [kmol/s]
        self.FEEDN2 = np.zeros(self.NZDIM)         # N2进料 [kmol/s]
        
        self.TFEED_OX = 393.15             # 氧气进料温度 [K]
        self.PFEED_OX = 40.83e5            # 氧气进料压力 [Pa]
        self.TFEED_SL = 366.15             # 煤浆进料温度 [K]
        self.PFEED_SL = 40.83e5            # 煤浆进料压力 [Pa]
        self.TW = 3300.0                   # 壁温 [K]
        
        self.TFEED_CO2 = 393.15            # CO2进料温度 [K]
        self.PFEED_CO2 = 40.83e5           # CO2进料压力 [Pa]
        self.FEDCO2 = np.zeros(self.NZDIM)         # CO2进料 [kmol/s]
    
    def init_volatile(self):
        """Common.02 - 挥发分释放"""
        self.RVCH4 = np.zeros(self.NZDIM)          # CH4释放速率 [kmol/s]
        self.RVH2 = np.zeros(self.NZDIM)           # H2释放速率 [kmol/s]
        self.RCO = np.zeros(self.NZDIM)            # CO释放速率 [kmol/s]
        self.RCO2 = np.zeros(self.NZDIM)           # CO2释放速率 [kmol/s]
        self.RVTAR = np.zeros(self.NZDIM)          # 焦油释放速率 [kmol/s]
        self.RH2S = np.zeros(self.NZDIM)           # H2S释放速率 [kmol/s]
        self.RH2 = np.zeros(self.NZDIM)            # H2释放速率 (另一种) [kmol/s]
        self.RO2 = np.zeros(self.NZDIM)            # O2释放速率 [kmol/s]
        self.REN2 = np.zeros(self.NZDIM)           # N2释放速率 [kmol/s]
        self.RVH2O = np.zeros(self.NZDIM)          # H2O释放速率 [kmol/s]
        
        # 挥发分系数
        self.XCOCH = 0.0
        self.XOCH4 = 0.0
        self.XOH2 = 0.0
        self.XHOCH = 0.0
        self.XHOH2 = 0.0
        self.XOCO = 0.0
        self.XOTAR = 0.0
        self.XCTAR_CO = 0.0
        self.XHTAR = 0.0
    
    def init_enthalpy(self):
        """Common.02 - 焓值相关"""
        self.HENTH = np.zeros((16, self.NZDIM))    # 组分焓值
        self.DHDT = np.zeros((16, self.NZDIM))     # 焓值温度导数
        self.FEEDH = np.zeros((4, self.NZDIM))     # 进料焓值
        self.FEDPH = np.zeros((3, self.NZDIM))     # 进料压力相关
        self.HFH2O = np.zeros(self.NZDIM)          # H2O焓值
        
        self.QLOSS = 0.02                  # 热损失系数
        self.QH_CRCT = 0.0                 # 热校正
        self.QKW = np.zeros(self.NZDIM)    # 热损失 [W]

        # ---- 晋华炉3.0 参数 (jinhualu分支新增, 已按典型工况调定) ----
        self.KMODEL = 0          # 0=TEXACO(耐火砖), 1=晋华炉(水冷壁+RSC)
        self.N_RSC = 30          # 辐射废锅段网格数
        self.D_RSC = 2.6         # 辐射废锅直径 [m]
        self.H_RSC = 30.0        # 辐射废锅高度 [m]
        self.TW_WALL = 1773.0    # 燃烧室水冷壁渣层表面有效温度 [K]
        self.TW_RSC = 673.0      # 辐射废锅壁面(积灰)有效温度 [K]
        self.P_DRUM = 6.5e6      # 汽包压力 [Pa]
        self.T_FW = 423.15       # 给水温度 [K]
        self.KRELAX_WGS = 2.0    # WGS平衡松弛系数
        self.KRELAX_METH = 0.02  # 甲烷化平衡松弛系数
        self.RSC_MODE = 0        # 0=固定高度，1=给定出口温度反算高度与产汽
        self.T_RSC_OUT_C = 780.0 # 目标废锅出口温度 [°C]
        self.H_RSC_MIN = 1.0     # 高度搜索下限 [m]
        self.H_RSC_MAX = 120.0   # 高度搜索上限 [m]
        
        self.RAC = np.zeros(self.NZDIM)            # 反应速率
        self.Y = np.zeros(9)               # 组分摩尔分数
    
    def init_matrix(self):
        """Common.03 - 矩阵"""
        # 注意: Fortran是AMAT(11,11,30), Python用(12,12,31)来保持1-based索引
        # 但使用(13,13,32)来避免某些情况下的越界
        self.AMAT = np.zeros((13, 13, self.NZDIM))
        self.BMAT = np.zeros((13, 13, self.NZDIM))
        self.CMAT = np.zeros((13, 13, self.NZDIM))
        self.DMAT = np.zeros((13, self.NZDIM))


# 全局单例实例
common = CommonData()
