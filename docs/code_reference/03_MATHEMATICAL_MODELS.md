# TEXACO Python版本 - 数学物理模型详解

本文档详细说明TEXACO气化炉模拟程序中涉及的所有数学和物理方程，包含Fortran和Python代码对照。

---

## 目录

1. [质量平衡方程](#1-质量平衡方程)
2. [能量平衡方程](#2-能量平衡方程)
3. [气相反应动力学](#3-气相反应动力学)
4. [异相反应动力学](#4-异相反应动力学)
5. [扩散与传质模型](#5-扩散与传质模型)
6. [热力学性质计算](#6-热力学性质计算)

---

## 1. 质量平衡方程

### 1.1 气体组分质量平衡

对于每个网格单元 $i$，气体组分 $j$ 的质量平衡方程为：

$$\frac{dF_j}{dz} = R_j^{in} - R_j^{out} + R_j^{reaction} + R_j^{devol}$$

其中：
- $F_j$：组分 $j$ 的摩尔流量 [kmol/s]
- $R_j^{in}$：从上游单元流入的速率 [kmol/s]
- $R_j^{out}$：流出到下游单元的速率 [kmol/s]
- $R_j^{reaction}$：化学反应生成/消耗的速率 [kmol/s]
- $R_j^{devol}$：挥发分释放的速率 [kmol/s]

#### 1.1.1 O₂ 平衡方程 (DMAT[1,i])

**物理意义**: O₂的来源包括挥发分释放、进料和上游流入；消耗包括流出和各种反应消耗。

**数学表达式**:

$$DMAT_{1,i} = RO2_i + FEEDO2_i + FEMF_{1,i-1} - FEMF_{1,i} - \frac{XK1}{2} - \frac{XK2}{2} - 2XK6 - \frac{A3}{\Phi}$$

**Python代码**:
```python
def _calculate_dmat_for_cell(i, ...):
    # O2平衡方程
    common.DMAT[1, i] = common.RO2[i] + common.FEEDO2[i]
    if i != common.NZRA:
        common.DMAT[1, i] += common.FEMF[1, i - 1]  # 上游流入
    common.DMAT[1, i] -= common.FEMF[1, i]  # 流出
    
    # 气相反应消耗
    common.DMAT[1, i] -= rxk1 / 2.0  # CO氧化消耗O2
    common.DMAT[1, i] -= rxk2 / 2.0  # H2氧化消耗O2
    common.DMAT[1, i] -= rxk6 * 2.0  # CH4氧化消耗O2
    
    # 碳反应消耗O2
    common.DMAT[1, i] -= ra3 / rphi  # C+O2反应消耗
```

**Fortran代码**:
```fortran
      DMAT(1,I)=RO2(I)+FEEDO2(I)
      IF (I.NE.NZRA) THEN 
        DMAT(1,I)=DMAT(1,I)+FEMF(1,I-1)
      ENDIF
      DMAT(1,I)=DMAT(1,I)-FEMF(1,I)
      DMAT(1,I)=DMAT(1,I)-RXK1/2.0-RXK2/2.0-RXK6*2.0-RA3/RPHI
```

---

#### 1.1.2 CH₄ 平衡方程 (DMAT[2,i])

**物理意义**: CH₄的来源包括挥发分释放和甲烷化反应；消耗包括流出和氧化反应。

**数学表达式**:

$$DMAT_{2,i} = RVCH4_i + KCHECK \cdot RVCH4_i + FEMF_{2,i-1} - FEMF_{2,i} - XK5 - XK6 + A2$$

**Python代码**:
```python
    # CH4平衡方程
    common.DMAT[2, i] = common.RVCH4[i] + common.KCHECK * common.RVCH4[i]
    if i != common.NZRA:
        common.DMAT[2, i] += common.FEMF[2, i - 1]
    common.DMAT[2, i] -= common.FEMF[2, i]
    
    # 气相反应消耗CH4
    common.DMAT[2, i] -= rxk5  # 蒸汽重整消耗
    common.DMAT[2, i] -= rxk6  # 氧化消耗
    
    # 碳反应产生CH4
    common.DMAT[2, i] += ra2   # 甲烷化反应产生
```

**Fortran代码**:
```fortran
      DMAT(2,I)=RVCH4(I)+KCHECK*RVCH4(I)
      IF (I.NE.NZRA) THEN 
        DMAT(2,I)=DMAT(2,I)+FEMF(2,I-1)
      ENDIF
      DMAT(2,I)=DMAT(2,I)-FEMF(2,I)-RXK5-RXK6+RA2
```

---

#### 1.1.3 CO 平衡方程 (DMAT[3,i])

**物理意义**: CO的来源包括挥发分释放、水煤气反应、Boudouard反应等；消耗包括流出和氧化反应。

**数学表达式**:

$$DMAT_{3,i} = RCO_i + KCHECK \cdot RCO_i + FEMF_{3,i-1} - FEMF_{3,i} - XK1 - XK3 + XK4 + XK5 + A1 + A3(2-\frac{2}{\Phi}) + 2A4 - A5$$

**Python代码**:
```python
    # CO平衡方程
    common.DMAT[3, i] = common.RCO[i] + common.KCHECK * common.RCO[i]
    if i != common.NZRA:
        common.DMAT[3, i] += common.FEMF[3, i - 1]
    common.DMAT[3, i] -= common.FEMF[3, i]
    
    # 气相反应
    common.DMAT[3, i] -= rxk1  # CO氧化消耗
    common.DMAT[3, i] -= rxk3  # 水煤气变换消耗
    common.DMAT[3, i] += rxk4  # 逆水煤气变换产生
    common.DMAT[3, i] += rxk5  # 蒸汽重整产生
    
    # 碳反应
    common.DMAT[3, i] += ra1   # C+H2O产生CO
    common.DMAT[3, i] += ra3 * (2.0 - 2.0 / rphi)  # C+O2产生CO
    common.DMAT[3, i] += ra4 * 2.0  # C+CO2产生CO
    common.DMAT[3, i] -= ra5   # 催化水煤气消耗
```

---

### 1.2 固体质量平衡

#### 1.2.1 固体总质量平衡 (DMAT[NSGP,i])

**物理意义**: 固体（碳+灰分）的质量平衡。

**数学表达式**:

$$DMAT_{NSGP,i} = WFC_i + WFA_i + KCHECK \cdot RVTAR_i \cdot XMTAR + WE_{i-1} - WE_i - RI_i$$

其中：
- $NSGP = NVE + 1 = 9$（气体组分数8 + 1）
- $WFC_i$：固定碳进料 [kg/s]
- $WFA_i$：灰分进料 [kg/s]
- $WE_i$：碳质量流量 [kg/s]
- $RI_i$：总碳消耗速率 [kg/s]

**Python代码**:
```python
    nsgp = common.NSGP  # = 9
    common.DMAT[nsgp, i] = common.WFC[i] + common.WFA[i] + \
                          common.KCHECK * common.RVTAR[i] * common.XMTAR
    if i != common.NZRA:
        common.DMAT[nsgp, i] += common.WE[i - 1]  # 上游流入
    common.DMAT[nsgp, i] -= common.WE[i] + rri   # 流出 + 反应消耗
```

**Fortran代码**:
```fortran
      DMAT(NSGP,I)=WFC(I)+WFA(I)+KCHECK*RVTAR(I)*XMTAR
      IF (I.NE.NZRA) THEN 
        DMAT(NSGP,I)=DMAT(NSGP,I)+WE(I-1)
      ENDIF      
      DMAT(NSGP,I)=DMAT(NSGP,I)-WE(I)-RRI
```

---

#### 1.2.2 碳转化率平衡 (DMAT[NSGP1,i])

**物理意义**: 碳在固体中的转化率平衡。

**数学表达式**:

$$DMAT_{NSGP1,i} = WFC_i + WE_{i-1} \cdot X_{i-1} - RVTAR_1 \cdot XMTAR \cdot X_{i-1} \cdot KCHECK - WE_i \cdot X_i - RI_i + RVTAR_1 \cdot XMTAR \cdot X_i \cdot KCHECK$$

其中：
- $NSGP1 = NSGP + 1 = 10$
- $X_i$：碳转化率 [-]

**Python代码**:
```python
    nsgp1 = common.NSGP1  # = 10
    common.DMAT[nsgp1, i] = common.WFC[i]
    if i != common.NZRA:
        common.DMAT[nsgp1, i] += common.WE[i - 1] * common.X[i - 1]
        common.DMAT[nsgp1, i] -= common.RVTAR[0] * common.XMTAR * \
                                 common.X[i - 1] * common.KCHECK
    common.DMAT[nsgp1, i] -= common.WE[i] * common.X[i] + rri
    common.DMAT[nsgp1, i] += common.RVTAR[0] * common.XMTAR * \
                             common.X[i] * common.KCHECK
```

---

## 2. 能量平衡方程

### 2.1 气体能量平衡 (DMAT[NVWS,i])

**物理意义**: 每个网格单元的能量守恒，包括气体流入/流出的焓变、固体流入/流出的焓变、反应热和热损失。

**数学表达式**:

$$\begin{aligned}
DMAT_{NVWS,i} &= \sum_{j=1}^{8} FEMF_{j,i-1} \cdot HENTH_{j,i-1} \\
&+ \sum_{j} R_j^{devol} \cdot H_j(T_{feed}) \\
&+ \sum_{j} FEED_j \cdot FEEDH_{j,i} \\
&- \sum_{j=1}^{8} FEMF_{j,i} \cdot HENTH_{j,i} \\
&+ WFC_i \cdot FEDPH_{1,i} + WFA_i \cdot FEDPH_{2,i} + FEDH2O_i \cdot HFH2O_i \\
&+ WE_{i-1} \cdot [X_{i-1} \cdot HENTH_{9,i-1} + (1-X_{i-1}) \cdot HENTH_{10,i-1}] \\
&- WE_i \cdot [X_i \cdot HENTH_{9,i} + (1-X_i) \cdot HENTH_{10,i}] \\
&- QKW_i - QLOSS \cdot BSMS \cdot HU \cdot 1000 \cdot \frac{DELZ_i}{HREAK} \\
&+ QH_{CRCT} \cdot \frac{DELZ_i}{HNZFR}
\end{aligned}$$

其中：
- $NVWS = 11$（当KTRLT=1时）
- $HENTH_{j,i}$：组分 $j$ 在单元 $i$ 的焓值 [J/kmol]
- $QKW_i$：热损失 [W]
- $QLOSS$：热损失系数
- $QH_{CRCT}$：热量校正 [J/kg]

**Python代码**:
```python
    if common.KTRLT == 1:
        nvws = common.NVWS  # = 11
        
        # 上游单元格流入的能量
        if i != common.NZRA:
            common.DMAT[nvws, i] = sum(
                common.FEMF[j, i - 1] * common.HENTH[j, i - 1] 
                for j in range(1, common.NGAS + 1)
            )
        else:
            common.DMAT[nvws, i] = 0.0
        
        # 挥发分释放带入的能量
        common.DMAT[nvws, i] += (
            common.RVCH4[i] * enthp_func(2, 'G', common.TFEED_SL, common.PFEED_SL) +
            (common.RH2[i] + common.RVH2[i]) * enthp_func(6, 'G', common.TFEED_SL, common.PFEED_SL) +
            common.RVH2O[i] * common.HFH2O[i] +
            common.RO2[i] * enthp_func(1, 'G', common.TFEED_SL, common.PFEED_SL) +
            ...
        )
        
        # 进料带入的能量
        common.DMAT[nvws, i] += (
            common.FEEDO2[i] * common.FEEDH[1, i] +
            common.FEEDN2[i] * common.FEEDH[2, i] +
            common.FEDCO2[i] * common.FEEDH[3, i]
        )
        
        # 流出带走的能量
        common.DMAT[nvws, i] -= sum(
            common.FEMF[j, i] * common.HENTH[j, i] 
            for j in range(1, common.NGAS + 1)
        )
        
        # 固体颗粒流入的能量
        common.DMAT[nvws, i] += (
            common.WFC[i] * common.FEDPH[1, i] +
            common.WFA[i] * common.FEDPH[2, i] +
            common.FEDH2O[i] * common.HFH2O[i]
        )
        
        # 上游颗粒流入的能量
        if i != common.NZRA:
            common.DMAT[nvws, i] += common.WE[i - 1] * (
                common.X[i - 1] * common.HENTH[9, i - 1] +
                (1.0 - common.X[i - 1]) * common.HENTH[10, i - 1]
            )
        
        # 当前单元格颗粒流出的能量
        common.DMAT[nvws, i] -= common.WE[i] * (
            common.X[i] * common.HENTH[9, i] +
            (1.0 - common.X[i]) * common.HENTH[10, i]
        )
        
        # 热损失
        common.DMAT[nvws, i] -= common.QKW[i]
        
        # 热损失校正
        common.DMAT[nvws, i] -= common.QLOSS * common.BSMS * common.HU * \
                                1000.0 * common.DELZ[i] / common.HREAK
        
        # 第一反应区热校正
        if i <= common.NZFR:
            common.DMAT[nvws, i] += common.QH_CRCT * common.DELZ[i] / common.HNZFR
```

---

## 3. 气相反应动力学

### 3.1 CO氧化反应 (XK1)

**反应方程式**:

$$CO + \frac{1}{2}O_2 \rightarrow CO_2$$

**反应速率方程**:

$$XK1 = XK10 \cdot Y_{O2} \cdot Y_{CO} \cdot KTRL_{XK1}$$

其中：

$$XK10 = 3.09 \times 10^8 \cdot \exp\left(-\frac{9.976 \times 10^7}{R \cdot T_i}\right) \cdot \left(\frac{P}{R \cdot T_i}\right)^2 \cdot A_i \cdot \Delta z_i$$

**参数说明**:
- $Y_{O2}$：O₂摩尔分数 [-]
- $Y_{CO}$：CO摩尔分数 [-]
- $R = 8314.3$ J/(kmol·K)：通用气体常数
- $T_i$：单元 $i$ 的温度 [K]
- $P$：系统压力 [Pa]
- $A_i$：单元 $i$ 的截面积 [m²]
- $\Delta z_i$：单元 $i$ 的高度 [m]
- $KTRL_{XK1}$：反应控制参数（通常为1）

**Python代码**:
```python
def xk1(i):
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物是否存在
    if common.Y[1] < 1.0e-10 or common.Y[3] < 1.0e-10:
        return 0.0
    
    # 计算反应速率
    exp_arg = -9.976e7 / (common.RAG * common.T[i])
    xk10 = (3.09e8 * np.exp(exp_arg)
            * (common.PWK / (common.RAG * common.T[i])) ** 2
            * common.AT[i] * common.DELZ[i])
    
    xk1_result = xk10 * common.Y[1] * common.Y[3] * common.KTRL_XK1
    return xk1_result
```

**Fortran代码**:
```fortran
      FUNCTION XK1(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      
      DO 778 J=1,NGAS
  778 Y(J)=FEMF(J,I)/FEM(I)
      
      IF(Y(1).LT.1.0E-10.OR.Y(3).LT.1.0E-10) THEN
        XK1=0.0
        RETURN
      ENDIF
      
      XK10=3.09E8*DEXP(-9.976E7/(RAG*T(I)))
     &     *(PWK/(RAG*T(I)))**2*AT(I)*DELZ(I)
      XK1=XK10*Y(1)*Y(3)*KTRL_XK1
      
      RETURN
      END
```

**参考**: CEN KEFA AND ZHAO LI

---

### 3.2 H₂氧化反应 (XK2)

**反应方程式**:

$$H_2 + \frac{1}{2}O_2 \rightarrow H_2O$$

**反应速率方程**:

$$XK2 = XK20 \cdot Y_{O2} \cdot Y_{H2} \cdot KTRL_{XK2}$$

其中：

$$XK20 = 8.83 \times 10^8 \cdot \exp\left(-\frac{9.976 \times 10^7}{R \cdot T_i}\right) \cdot A_i \cdot \Delta z_i \cdot \left(\frac{P}{R \cdot T_i}\right)^2$$

**Python代码**:
```python
def xk2(i):
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    if common.Y[1] < 1.0e-10 or common.Y[6] < 1.0e-10:
        return 0.0
    
    exp_arg = -9.976e7 / (common.RAG * common.T[i])
    xk20 = (8.83e8 * np.exp(exp_arg)
            * common.AT[i] * common.DELZ[i]
            * (common.PWK / (common.RAG * common.T[i])) ** 2)
    
    return xk20 * common.Y[1] * common.Y[6] * common.KTRL_XK2
```

**参考**: ZHAO LI AND CEN KEFA

---

### 3.3 水煤气变换反应 (XK3)

**反应方程式**:

$$CO + H_2O \rightarrow CO_2 + H_2$$

**反应速率方程**:

$$XK3 = XK30 \cdot Y_{CO} \cdot Y_{H2O} \cdot KTRL_{XK3}$$

其中：

$$XK30 = 2.978 \times 10^{12} \cdot \exp\left(-\frac{3.69 \times 10^8}{R \cdot T_i}\right) \cdot A_i \cdot \Delta z_i \cdot \left(\frac{P}{R \cdot T_i}\right)^2$$

**Python代码**:
```python
def xk3(i):
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    if common.Y[3] < 0.0 or common.Y[8] < 0.0:
        return 0.0
    
    exp_arg = -3.69e8 / (common.RAG * common.T[i])
    xk30 = (2.978e12 * np.exp(exp_arg)
            * common.AT[i] * common.DELZ[i]
            * (common.PWK / (common.RAG * common.T[i])) ** 2)
    
    return xk30 * common.Y[3] * common.Y[8] * common.KTRL_XK3
```

**参考**: CEN KEFA AND ZHAO LI

---

## 4. 异相反应动力学

### 4.1 碳-水蒸气反应 (A1)

**反应方程式**:

$$C + H_2O \rightarrow CO + H_2$$

**反应速率方程**:

$$A1 = AM \cdot \pi \cdot D_p^2 \cdot XKC_{H2O}(i) \cdot P \cdot PA1 \cdot CTRL_{A1}$$

其中：
- $AM$：颗粒数量 [-]
- $D_p$：颗粒直径 [m]
- $P$：系统压力 [Pa]
- $CTRL_{A1}$：反应控制系数（通常为0.28）
- $PA1$：有效分压 [Pa]

**颗粒数量计算**:

$$AM = \frac{XMS_i}{ROS_i} \cdot \frac{6}{\pi \cdot D_p^3}$$

**有效分压计算**:

$$PA1 = Y_{H2O} - \frac{Y_{H2} \cdot Y_{CO} \cdot P}{P_0 \cdot CS_{KEQ1}}$$

**化学平衡常数**:

$$CS_{KEQ1} = \exp\left(17.644 - \frac{30260}{1.8 \cdot T_p}\right)$$

**Python代码**:
```python
def A1(i):
    # 更新气体摩尔分数
    _update_gas_fractions(i)
    
    TP = TPAR(i)  # 颗粒温度
    
    # 化学平衡常数
    exp_arg = 17.644 - 30260.0 / (1.8 * TP)
    CS_KEQ1 = np.exp(exp_arg)
    
    # 分压项
    PA1 = common.Y[8] - common.Y[6] * common.Y[3] * \
          common.PWK / common.P0 / CS_KEQ1
    
    # 检查反应条件
    if common.Y[8] < 0.0001 or PA1 < 0.0:
        return 0.0
    
    # 颗粒数量计算
    AM = common.XMS[i] / common.ROS[i] * 6.0 / (common.PI * common.DP ** 3)
    
    # 反应速率计算
    rate = AM * common.PI * common.DP ** 2.0 * \
           XKC_H2O(i) * common.PWK * PA1 * common.CTRL_A1
    
    return rate
```

**Fortran代码**:
```fortran
      FUNCTION A1(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      
      DO 778 J=1,NGAS
  778 Y(J)=FEMF(J,I)/FEM(I)
      
      TP=TPAR(I)
      CS_KEQ1=DEXP(17.644-30260.0/(1.8*TP))
      PA1=(Y(8)-Y(6)*Y(3)*PWK/P0/CS_KEQ1)
      
      IF(Y(8).LT.0.0001.OR.PA1.LT.0.0) THEN
        A1=0.0
        RETURN
      ENDIF
      
      AM=XMS(I)/ROS(I)*6.0/(PI*DP**3)
      A1=AM*PI*DP**2.0*XKC_H2O(I)*PWK*PA1*CTRL_A1
      
      RETURN
      END
```

---

### 4.2 甲烷化反应 (A2)

**反应方程式**:

$$C + 2H_2 \rightarrow CH_4$$

**反应速率方程**:

$$A2 = AM \cdot \pi \cdot D_p^2 \cdot XKC_{H2}(i) \cdot P \cdot PA2 \cdot CTRL_{A2}$$

**有效分压计算**:

$$PA2 = Y_{H2} - \sqrt{\frac{Y_{CH4} \cdot P_0}{P \cdot CS_{KEQ2}}}$$

**化学平衡常数**:

$$CS_{KEQ2} = \frac{0.175}{34713} \cdot \exp\left(\frac{18400}{1.8 \cdot T_p}\right)$$

**Python代码**:
```python
def A2(i):
    _update_gas_fractions(i)
    
    TP = TPAR(i)
    
    # 化学平衡常数
    exp_arg = 18400.0 / (1.8 * TP)
    CS_KEQ2 = 0.175 / 34713.0 * np.exp(exp_arg)
    
    # 分压项
    PA2 = common.Y[6] - np.sqrt(common.Y[2] * common.P0 / 
                                common.PWK / CS_KEQ2)
    
    if common.Y[6] < 0.001 or PA2 < 0.0:
        return 0.0
    
    AM = common.XMS[i] / common.ROS[i] * 6.0 / (common.PI * common.DP ** 3)
    
    rate = AM * common.PI * common.DP ** 2.0 * \
           XKC_H2(i) * common.PWK * PA2 * common.CTRL_A2
    
    return rate
```

---

### 4.3 碳-氧气反应 (A3)

**反应方程式**:

$$C + O_2 \rightarrow CO + CO_2$$

**反应速率方程**:

$$A3 = AM \cdot \pi \cdot D_p^2 \cdot XKC_{O2}(i) \cdot P \cdot Y_{O2} \cdot CTRL_{A3}$$

**Python代码**:
```python
def A3(i):
    _update_gas_fractions(i)
    
    if common.Y[1] <= 0.0:
        return 0.0
    
    PA3 = common.Y[1]
    
    AM = common.XMS[i] / common.ROS[i] * 6.0 / (common.PI * common.DP ** 3)
    
    rate = AM * common.PI * common.DP ** 2.0 * \
           XKC_O2(i) * common.PWK * PA3 * common.CTRL_A3
    
    return rate
```

---

## 5. 扩散与传质模型

### 5.1 扩散系数计算模型 (Wen模型)

总反应速率系数由化学反应速率、气相扩散速率和灰层扩散速率串联组成：

$$\frac{1}{XKC} = \frac{1}{RKCH \cdot YY^2} + \frac{1}{RKDG} + \frac{1}{RKDA} \cdot \left(\frac{1}{YY} - 1\right)$$

或等价的：

$$XKC = \frac{YY^2}{\frac{1}{RKCH} + \frac{YY^2}{RKDG} + \frac{YY - YY^2}{RKDA}}$$

其中：
- $RKCH$：化学反应速率常数
- $RKDG$：气相扩散速率
- $RKDA$：灰层扩散速率
- $YY$：反应核模型参数

### 5.2 反应核模型参数

$$YY = \left(\frac{1 - FOC}{1 - XCVM0}\right)^{1/3}$$

其中：

$$FOC = 1 - FASH \cdot \frac{X}{1 - X}$$

$$FASH = \frac{ELAS}{ELC + ELH + ELO + ELN + ELS}$$

### 5.3 O₂扩散系数计算

**化学反应速率常数**:

$$RKCH = 8710 \cdot \exp\left(-\frac{17967}{T_p}\right)$$

**气相扩散系数**:

$$D0 = 4.26 \cdot \left(\frac{T}{1800}\right)^{1.75} \cdot \frac{P_0}{P}$$

$$RKDG = 0.292 \cdot \Phi(i) \cdot \frac{D0}{D_p \cdot 100 \cdot T} \cdot COEF_{A3}$$

**灰层扩散系数**:

$$RKDA = VOID^{2.5} \cdot RKDG$$

**单位转换**:

$$XKC_{O2} = XKC \cdot \frac{10}{1.01325 \times 10^5 \cdot 12}$$

**Python代码**:
```python
def XKC_O2(i):
    TP = TPAR(i)
    VOID = 0.75
    
    # 1kg原煤对应的灰分量
    FASH = common.ELAS / (common.ELC + common.ELH + 
                          common.ELO + common.ELN + common.ELS)
    
    # 计算碳转化率
    x_safe = min(common.X[i], 0.999999)
    if x_safe >= 1.0:
        FOC = 0.0
    else:
        FOC = 1.0 - FASH * x_safe / (1.0 - x_safe)
    
    # 反应核模型参数
    YY = ((1.0 - FOC) / (1.0 - common.XCVM0)) ** 0.333
    if YY >= 1.0:
        YY = 1.0
    
    # RKCH: 化学反应速率常数
    exp_arg = -17967.0 / TP
    RKCH = 8710.0 * np.exp(exp_arg)
    
    # D0: 扩散系数基础值
    t_safe = max(common.T[i], 273.15)
    D0 = 4.26 * (t_safe / 1800.0) ** 1.75 / common.PWK * common.P0
    
    # RKDG: 气相扩散系数
    RKDG = 0.292 * PHI(i) * D0 / (common.DP * 100.0) / common.T[i] * common.COEF_A3
    
    # RKDA: 灰层扩散系数
    RKDA = VOID ** 2.5 * RKDG
    
    # XKC_O2: 总反应速率系数
    XKC = YY * YY / (1.0 / RKCH + YY * YY / RKDG + 1.0 / RKDA * (YY - YY * YY))
    
    # 单位转换: g/(cm²·atm·s) -> kmol/(m²·Pa·s)
    XKC = XKC * 10.0 / 1.01325e5 / 12.0
    
    return XKC
```

---

## 6. 热力学性质计算

### 6.1 热容积分 (CMP函数)

热容多项式（Knacke/Barin格式）:

$$Cp = A + B \times 10^{-3}T + C \times \frac{10^5}{T^2} + D \times 10^{-6}T^3$$

积分公式:

$$\int_{T_0}^{T} Cp \, dT = 4.186 \cdot \left[A(T-T_0) + 0.05B\left(\frac{T^2}{100} - \frac{T_0^2}{100}\right) - C\left(\frac{10^5}{T} - \frac{10^5}{T_0}\right) + \frac{D}{3}\left(\left(\frac{T}{100}\right)^3 - \left(\frac{T_0}{100}\right)^3\right)\right]$$

**Python代码**:
```python
def CMP_SOLID(A: float, B: float, C: float, D: float, T: float, T0: float) -> float:
    """
    计算热容积分 (与Fortran CMP函数一致)
    单位: kJ/kmol
    """
    term_a = A * (T - T0)
    term_b = B * 0.05 * (T * T * 0.01 - T0 * T0 * 0.01)
    term_c = -C * (1.0e5 / T - 1.0e5 / T0)
    term_d = D / 3.0 * ((0.01 * T)**3 - (0.01 * T0)**3)
    
    result = 4.186 * (term_a + term_b + term_c + term_d)
    return result
```

### 6.2 焓值计算

**气体组分焓值**:

$$H_j(T) = \int_{298.15}^{T} Cp_j \, dT$$

**固体碳焓值**:

$$H_C(T) = HMT + CMP(A_1, B_1, C_1, D_1, T_{neu}, 298.15)$$

当 $T > 1100K$:

$$H_C(T) += CMP(A_2, B_2, C_2, D_2, T, 1100)$$

**Python代码**:
```python
def FC(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float:
    """
    计算固体碳(C)的热力学性质
    """
    A = [0.026, 5.841]
    B = [9.307, 0.104]
    C = [-0.354, -7.559]
    D = [-4.155, 0.0]
    HMT = 0.0
    TU = 298.15
    
    TEMPNEU = min(TEMP, 1100.0)
    
    if KALZG == 'ENTH':
        # 焓值 [J/kmol]
        E = HMT + CMP_SOLID(A[0], B[0], C[0], D[0], TEMPNEU, TU)
        if TEMP > 1100.0:
            E = E + CMP_SOLID(A[1], B[1], C[1], D[1], TEMP, 1100.0)
        return E * 1.0e3
```

---

*最后更新: 2026-03-20*
