# TEXACO Python版本 - 函数调用关系与代码架构

本文档详细展示TEXACO气化炉模拟程序的函数调用关系，包括Python代码和对应的Fortran代码块。

---

## 1. 主程序调用层次

### 1.1 顶层调用关系

```python
# Python: src/main.py
# Fortran: Wg1.for (PROGRAM TEXACO_GASIFIER)

# ============================================
# 主程序入口
# ============================================

# Python版本
def main():
    """TEXACO气化炉CFD模拟主程序"""
    output_file = open('GASTEST.DAT', 'w')  # 打开输出文件
    common.ITERAT = 0                        # 初始化迭代计数器
    
    eingab()                                 # 调用初始化
    
    # 主迭代循环
    for iteration in range(1, common.ITMAX + 1):
        common.ITERAT = common.ITERAT + 1
        common.KONVER = 0
        
        gasifier(...)                        # 气化炉计算
        newtra(omega=1.0)                    # 牛顿迭代求解
        
        sumfe, sumwe, sumx, sumt = calculate_residuals()  # 计算残差
        
        if common.KONVER == 0:               # 检查收敛
            kolerg(output_file)              # 输出结果
            break

# Fortran版本 (Wg1.for)
"""
      PROGRAM  TEXACO_GASIFIER
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'
      
      OPEN (UNIT=1,FILE='GASTEST.DAT',STATUS='UNKNOWN')
      ITERAT=0
      
      CALL EINGAB                              ! 初始化
      
      DO 100 I=1,ITMAX                         ! 主迭代循环
      ITERAT=ITERAT+1
      KONVER=0
      
      CALL GASIFIER                            ! 气化炉计算
      KONVER=0
      CALL NEWTRA                              ! 牛顿迭代
      
      ! 计算残差
      SUMFE=0.0D0
      DO 10 II=NZEL1,NZEL2
      DO 11 J=1,NVE
   11 SUMFE=SUMFE+DABS(DMAT(J,II))
   10 CONTINUE
      ...
      
      IF (KONVER.EQ.0)  THEN
        CALL KOLERG                            ! 输出结果
        GOTO 110
      ENDIF
      
 100  CONTINUE
 110  CONTINUE
      CLOSE(UNIT=1)
      END
"""
```

---

## 2. 初始化模块调用链

### 2.1 eingab() 函数调用关系

```python
# Python: src/subroutines/initialization.py
# Fortran: Wg2.for (SUBROUTINE EINGAB)

def eingab(data_path='data/Datain0.dat'):
    """
    输入数据和初始化子程序
    """
    # 1. 设置基本参数
    common.XMOL = np.array([32., 16., 28., 44., 34., 2., 28., 18., 12., 60.])
    common.KCHECK = 0
    common.KTRLT = 1
    common.KTRLR = 1
    
    # 2. 读取输入数据文件
    with open(full_data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 解析各参数...
    common.ITMAX = int(values[0])      # 最大迭代次数
    common.SKONFE = values[1]           # 收敛阈值
    common.SKONWE = values[2]
    common.SKONX = values[3]
    common.SKONT = values[4]
    
    # 3. 调用几何计算
    geometry()                          # ↓ 调用GEOMETRY
    
    # 4. 计算质量流量
    common.BSMS = common.BSLURRY * common.RATIO_COAL
    common.BSWAF = common.BSMS * (1.0 - common.ELH2O - common.ELAS)
    common.FOX = (common.FOXY * common.BSWAF / 32.0 / common.PURE_O2 * 22.4)
    
    # 5. 计算进料分配...
    
    # 6. 调用挥发分释放计算
    from functions.gas_reactions import flucht
    flucht()                            # ↓ 调用FLUCHT
    
    # 7. 调用热量校正
    qhcrct()                            # ↓ 调用QHCRCT
    
    # 8. 初始化未知数
    if common.KTRL == 0:
        _read_start_file(start_path)    # ↓ 读取START.DAT
    else:
        # 默认初始化...
        pass

# Fortran版本 (Wg2.for)
"""
      SUBROUTINE EINGAB
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      
      DATA XMOL/32.,16.,28.,44.,34.,2.,28.,18.,12.,60./
      
      ! 读取输入数据...
      READ(5,*)KTRL
      READ(5,*)ITMAX,SKONFE,SKONWE,SKONX,SKONT
      ...
      
      CALL GEOMETRY                        ! 几何计算
      
      ! 计算质量流量
      BSMS=BSLURRY*RATIO_COAL
      BSWAF=BSMS*(1.0-ELH2O-ELAS)
      FOX=(FOXY*BSWAF/32.0/PURE_O2*22.4)
      
      ! 计算进料分配...
      
      CALL FLUCHT                          ! 挥发分释放
      CALL QHCRCT                          ! 热量校正
      
      ! 初始化未知数...
      IF(KTRL.EQ.0) THEN
         READ(4,*)((FEMF(II,I),II=1,4),I=NZEL1,NZEL2)
         ...
      ENDIF
      
      RETURN
      END
"""
```

### 2.2 geometry() 函数

```python
# Python: src/subroutines/initialization.py
# Fortran: Wg2.for (SUBROUTINE GEOMETRY)

def geometry():
    """
    计算气化炉几何结构
    炉子分为8段，每段有不同的直径
    """
    # 各段高度 [m]
    hreak1 = 0.4      # 第1段高度
    hreak2 = 0.4      # 第2段高度
    ...
    hreak8 = 0.1876   # 第8段高度
    
    # 总高度
    common.HREAK = hreak1 + hreak2 + ... + hreak8
    
    # 各段直径 [m]
    common.DIA1 = 1.005   # 第1段直径
    common.DIA2 = 0.935   # 第2段直径
    ...
    common.DIA8 = 1.025   # 第8段直径
    
    # 计算每个格子的高度、位置、截面积
    # 第1段: NZRE=30 到 NZR1=29
    n_cells_1 = common.NZRE - common.NZR1 + 1
    for i in range(common.NZRE, common.NZR1 - 1, -1):
        common.DELZ[i] = hreak1 / n_cells_1
        common.H[i] = common.DELZ[i] * (common.NZRE - i + 1)
        common.AT[i] = common.DIA1 * common.DIA1 * common.PI / 4.0
        common.AR[i] = common.DIA1 * common.PI
    
    # 第2-8段类似...

# Fortran版本
"""
      SUBROUTINE GEOMETRY
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      
      HREAK1=0.4
      HREAK2=0.4
      ...
      HREAK8=0.1876
      
      HREAK=HREAK1+HREAK2+...+HREAK8
      
      DIA1=1.005
      DIA2=0.935
      ...
      DIA8=1.025
      
      ! 计算每个格子参数
      DO 100 I=NZRE,NZR1,-1
        DELZ(I)=HREAK1/2.0
        H(I)=DELZ(I)*(NZRE-I+1)
        AT(I)=DIA1*DIA1*PI/4.0
        AR(I)=DIA1*PI
  100 CONTINUE
      
      ! 第2-8段类似...
      
      RETURN
      END
"""
```

---

## 3. 气化炉主计算模块调用链

### 3.1 gasifier() 函数调用关系

```python
# Python: src/subroutines/gasifier_main.py
# Fortran: Wg3.for (SUBROUTINE GASIFIER)

def gasifier(
    xmass_func, entfed_func, entkol_func,
    xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func,
    a1_func, a2_func, a3_func, a4_func, a5_func,
    phi_func, ri_func,
    enthp_func, wdkr_func=None
):
    """
    GASIFIER主计算子程序
    """
    # 1. 调用XMASS计算固体参数
    xmass_func()                        # ↓ 调用XMASS
    
    # 2. 计算所有Cell的FEM和U0
    for ii in range(common.NZRA, common.NZEL2 + 1):
        common.FEM[ii] = sum(common.FEMF[j, ii] for j in range(1, common.NGAS + 1))
    
    for ii in range(common.NZRA, common.NZEL2 + 1):
        common.U0[ii] = common.FEM[ii] * common.RAG * common.T[ii] / (common.PWK * common.AT[ii])
    
    # 3. 主循环: 遍历每个网格单元
    for i in range(common.NZRA, common.NZRE + 1):
        
        # 3.1 初始化矩阵
        for k in range(1, common.NVWS + 1):
            common.DMAT[k, i] = 0.0
            for l in range(1, common.NVWS + 1):
                common.AMAT[k, l, i] = 0.0
                common.BMAT[k, l, i] = 0.0
                common.CMAT[k, l, i] = 0.0
        
        # 3.2 数值微分主循环
        k_state = 0
        while True:
            # 计算DMAT
            rri = _calculate_dmat_for_cell(
                i,
                xmass_func, entfed_func, entkol_func,
                xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func,
                a1_func, a2_func, a3_func, a4_func, a5_func,
                phi_func, ri_func,
                enthp_func, wdkr_func
            )
            
            # 保存RAC[i]
            if k_state == 0:
                common.RAC[i] = rri
            
            # 数值微分逻辑...
            if k_state > 0:
                # 恢复扰动，计算BMAT/AMAT
                # ...
                if k_state <= common.NSGP1:
                    pass  # 继续扰动
                elif k_state <= 2 * common.NVWS - 1:
                    pass  # 继续扰动
                else:
                    # 数值微分完成
                    break
            
            # 保存初始值并开始扰动
            if k_state == 0:
                for j in range(1, common.NVWS + 1):
                    dalt[j] = common.DMAT[j, i]
            
            k_state += 1
            # 扰动下一个变量...
            
        # 3.3 构建AMAT矩阵（显式设置对角元素）
        if common.KTRLT == 1:
            if i != common.NZRA:
                common.AMAT[common.NSGP, common.NSGP, i - 1] = 1.0
                common.AMAT[common.NSGP, common.NSGP1, i - 1] = 0.0
                common.AMAT[common.NSGP1, common.NSGP, i - 1] = common.X[i - 1]
                common.AMAT[common.NSGP1, common.NSGP1, i - 1] = common.WE[i - 1]
                # ...
        
        # 3.4 DMAT取负
        for j in range(1, common.NVWS + 1):
            common.DMAT[j, i] = -common.DMAT[j, i]
        
        sum_ri += rri
    
    return sum_ri

# Fortran版本 (Wg3.for)
"""
      SUBROUTINE GASIFIER
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'      
      INCLUDE 'COMMON.01'      
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'
      
      DIMENSION DALT(11)
      
      SUM_RI=0.0
      DO 1991 I=NZRA,NZRE
        
        ! 初始化矩阵
        DO 13 K=1,NVWS
          DMAT(K,I)=0.D00
          DO 13 L=1,NVWS
            AMAT(K,L,I)=0.D00
            BMAT(K,L,I)=0.D00
            CMAT(K,L,I)=0.D00
   13   CONTINUE
        
        K=0
   53   CONTINUE
        
        ! 计算FEM和U0
        FEM(I)=0.0D00
        DO 777 J=1,NGAS
  777   FEM(I)=FEM(I)+FEMF(J,I)      
        DO 82 II=NZRA,NZRE
   82   U0(II)=FEM(II)*RAG*T(II)/(PWK*AT(II))
        
        ! 计算摩尔分数
        DO 778 J=1,NGAS
  778   Y(J)=FEMF(J,I)/FEM(I)
        
        CALL XMASS
        CALL ENTFED
        CALL ENTKOL
        
        ! 计算反应速率
        IF(KTRLR.EQ.1) THEN
          RXK1=XK1(I)
          RXK2=XK2(I) 
          RXK3=XK3(I)
          RXK4=XK4(I)
          RXK5=XK5(I)
          RXK6=XK6(I)
          RA1=A1(I)
          RA2=A2(I)
          RA3=A3(I)
          RA4=A4(I)
          RA5=A5(I)
          RRI=RI(I)
          IF(K.EQ.0) RAC(I)=RRI
        ENDIF
        
        RPHI=PHI(I)
        
        ! 构建DMAT (质量平衡和能量平衡)
        DMAT(1,I)=RO2(I)+FEEDO2(I)
        IF (I.NE.NZRA) THEN 
          DMAT(1,I)=DMAT(1,I)+FEMF(1,I-1)
        ENDIF
        DMAT(1,I)=DMAT(1,I)-FEMF(1,I)
        DMAT(1,I)=DMAT(1,I)-RXK1/2.0-RXK2/2.0-RXK6*2.0-RA3/RPHI
        
        ! O2, CH4, CO, CO2, H2S, H2, N2, H2O平衡方程...
        
        ! 固体质量平衡
        DMAT(NSGP,I)=WFC(I)+WFA(I)+KCHECK*RVTAR(I)*XMTAR
        IF (I.NE.NZRA) THEN 
          DMAT(NSGP,I)=DMAT(NSGP,I)+WE(I-1)
        ENDIF      
        DMAT(NSGP,I)=DMAT(NSGP,I)-WE(I)-RRI
        
        ! 碳转化率平衡
        DMAT(NSGP1,I)=WFC(I)
        IF (I.NE.NZRA) THEN 
          DMAT(NSGP1,I)=DMAT(NSGP1,I)+WE(I-1)*X(I-1)
     &                    -RVTAR(1)*XMTAR*X(I-1)*KCHECK
        ENDIF      
        DMAT(NSGP1,I)=DMAT(NSGP1,I)-WE(I)*X(I)-RRI
     &                 +RVTAR(1)*XMTAR*X(I)*KCHECK
        
        ! 能量平衡方程
        IF(KTRLT.EQ.1) THEN
          IF (I.NE.NZRA) THEN
            DMAT(NVWS,I)=FEMF(1,I-1)*HENTH(1,I-1)
     &                  +FEMF(2,I-1)*HENTH(2,I-1)
     &                  +...
          ELSE
            DMAT(NVWS,I)=0.0
          ENDIF
          
          ! 加入各种能量项...
          
        ENDIF
        
        ! 数值微分逻辑
        IF (K.GT.0) GOTO 70
        
        DO 80 J=1,NVWS
   80   DALT(J)=DMAT(J,I)
        
        ! 扰动变量...
        
   70   CONTINUE
        ! 计算BMAT/AMAT...
        
        IF (K.LE.NSGP1) GOTO 80
        IF (K.LE.2*NVWS-1) GOTO 801
        
        DO 90 J=1,NVWS
   90   DMAT(J,I)=DALT(J)
        GOTO 1990
        
        ! 构建AMAT...
        
 1990   CONTINUE
        
        ! DMAT取负
        DO 1990 J=1,NVWS
          DMAT(J,I)=-DMAT(J,I)
 1990   CONTINUE
        
        SUM_RI=SUM_RI+RRI
 1991 CONTINUE
      
      RETURN
      END
"""
```

---

## 4. 气相反应模块调用链

### 4.1 气相反应速率计算

```python
# Python: src/functions/gas_reactions.py
# Fortran: Wg6.for

def xk1(i):
    """
    CO + 1/2 O2 -> CO2 反应速率
    """
    # 计算各组分摩尔分数
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    # 检查反应物
    if common.Y[1] < 1.0e-10 or common.Y[3] < 1.0e-10:
        return 0.0
    
    # 计算反应速率
    exp_arg = -9.976e7 / (common.RAG * common.T[i])
    xk10 = (3.09e8 * np.exp(exp_arg)
            * (common.PWK / (common.RAG * common.T[i])) ** 2
            * common.AT[i] * common.DELZ[i])
    
    xk1_result = xk10 * common.Y[1] * common.Y[3] * common.KTRL_XK1
    return xk1_result

# Fortran版本 (Wg6.for)
"""
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
"""
```

### 4.2 挥发分释放计算

```python
# Python: src/functions/gas_reactions.py
# Fortran: Wg6.for (SUBROUTINE FLUCHT)

def flucht():
    """
    挥发分释放计算子程序
    """
    # 初始化挥发分释放系数
    common.XOCH4 = 2.0       # 1摩尔CH4完全燃烧所需O2摩尔数
    common.XOH2 = 0.5        # 1摩尔H2完全燃烧所需O2摩尔数
    common.XOCO = 0.5        # 1摩尔CO完全燃烧所需O2摩尔数
    common.XOTAR = 1.16525   # 1摩尔TAR完全燃烧所需O2摩尔数
    ...
    
    # 计算各元素在1kg煤中的含量
    fak = 1.0
    prc = fak * common.ELC   # C元素含量
    prn = fak * common.ELN   # N元素含量
    prs = fak * common.ELS   # S元素含量
    prh = fak * common.ELH   # H元素含量
    pro = fak * common.ELO   # O元素含量
    
    # 计算总释放量
    rh2s_total = prs * common.BSMS / 32.0
    ren2_total = prn * common.BSMS / 28.0
    rh2_total = prh * common.BSMS / 2.0
    ro2_total = pro * common.BSMS / 32.0
    
    # 根据挥发分含量计算各组分释放量
    rvch41 = ((0.201 - 0.469 * common.XVM + 0.261 * common.XVM ** 2)
              * common.XVM * common.BSWAF / 16.0)
    rvtar1 = ((-0.325 + 7.279 * common.XVM - 12.88 * common.XVM ** 2)
              * common.XVM * common.BSWAF / 12.913)
    ...
    
    # 计算剩余H和O元素
    rh2_re = rh2_total - 2.0 * rvch41 - rvh21 - rvh2o1 - 0.3445 * rvtar1 - rh2s_total
    ro2_re = ro2_total - rco21 - 0.5 * (rco1 + rvh2o1) - 0.007 * rvtar1
    
    # 根据H和O元素平衡进行分支处理
    if rh2_re >= 0.0:
        if ro2_re >= 0.0:
            # H和O都有剩余
            pass
        else:
            # O不足，H剩余
            pass
    else:
        if ro2_re >= 0.0:
            # H不足，O剩余
            pass
        else:
            # H和O都不足
            pass
    
    # 将挥发分释放分配到各格子
    for i in range(common.NZRA, common.NZFR + 1):
        common.RVCH4[i] = rvch41 * common.DELZ[i] / common.HNZFR
        common.RVH2[i] = rvh21 * common.DELZ[i] / common.HNZFR
        ...

# Fortran版本
"""
      SUBROUTINE FLUCHT
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      
      XOCH4=2.0
      XOH2=0.5
      XOCO=0.5
      XOTAR=1.16525
      ...
      
      FAK=1.0
      PRC=FAK*ELC
      PRN=FAK*ELN
      PRS=FAK*ELS
      PRH=FAK*ELH
      PRO=FAK*ELO
      
      RH2S_TOTAL=PRS*BSMS/32.0
      REN2_TOTAL=PRN*BSMS/28.0
      RH2_TOTAL=PRH*BSMS/2.0
      RO2_TOTAL=PRO*BSMS/32.0
      
      RVCH41=((0.201-0.469*XVM+0.261*XVM**2)*XVM*BSWAF/16.0)
      RVTAR1=((-0.325+7.279*XVM-12.88*XVM**2)*XVM*BSWAF/12.913)
      ...
      
      ! 元素平衡和分支处理...
      
      DO I=NZRA,NZFR
        RVCH4(I)=RVCH41*DELZ(I)/HNZFR
        RVH2(I)=RVH21*DELZ(I)/HNZFR
        ...
      ENDDO
      
      RETURN
      END
"""
```

---

## 5. 碳反应速率模块调用链

### 5.1 碳反应速率计算 (A1-A5)

```python
# Python: src/functions/reaction_rates.py
# Fortran: Wg7.for

def A1(i):
    """
    计算碳与水蒸气反应速率
    反应: C + H2O -> CO + H2
    """
    # 更新气体摩尔分数
    _update_gas_fractions(i)
    
    TP = TPAR(i)
    
    # 化学平衡常数
    exp_arg = 17.644 - 30260.0 / (1.8 * TP)
    CS_KEQ1 = np.exp(exp_arg)
    
    # 分压项
    PA1 = common.Y[8] - common.Y[6] * common.Y[3] * common.PWK / common.P0 / CS_KEQ1
    
    # 检查反应条件
    if common.Y[8] < 0.0001 or PA1 < 0.0:
        return 0.0
    
    # 颗粒数量计算
    AM = common.XMS[i] / common.ROS[i] * 6.0 / (common.PI * common.DP ** 3)
    
    # 反应速率计算
    rate = AM * common.PI * common.DP ** 2.0 * XKC_H2O(i) * common.PWK * PA1 * common.CTRL_A1
    return rate

def XKC_H2O(i):
    """
    计算碳与水蒸气反应的速率系数
    """
    TP = TPAR(i)
    VOID = 0.75
    
    # 1kg原煤对应的灰分量
    FASH = common.ELAS / (common.ELC + common.ELH + common.ELO + common.ELN + common.ELS)
    
    # 计算碳转化率
    x_safe = min(common.X[i], 0.999999)
    if x_safe >= 1.0:
        FOC = 0.0
    else:
        FOC = 1.0 - FASH * x_safe / (1.0 - x_safe)
    
    # 反应核模型参数
    YY = ((1.0 - FOC) / (1.0 - common.XCVM0)) ** 0.333
    
    # RKCH: 化学反应速率常数
    exp_arg = -21060.0 / TP
    RKCH = 247.0 * np.exp(exp_arg)
    
    # RKDG: 气相扩散系数
    t_safe = max(common.T[i], 273.15)
    RKDG = 10.0 * 1.0e-4 * (t_safe / 2000.0) ** 0.75 * common.P0 / (common.DP * 100.0 * common.PWK) * common.COEF_A1
    
    # RKDA: 灰层扩散系数
    RKDA = VOID ** 2.5 * RKDG
    
    # XKC_H2O: 总反应速率系数
    XKC = YY * YY / (1.0 / RKCH + YY * YY / RKDG + 1.0 / RKDA * (YY - YY * YY))
    
    # 单位转换
    XKC = XKC * 10.0 / 1.01325e5 / 12.0
    return XKC

# Fortran版本 (Wg7.for)
"""
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
      
      FUNCTION XKC_H2O(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02' 
      
      TP=TPAR(I)
      VOID=0.75
      
      FASH=ELAS/(ELC+ELH+ELO+ELN+ELS)
      
      IF(X(I).GE.1.0) THEN
        FOC=0.0
      ELSE
        FOC=1.0-FASH*X(I)/(1.0-X(I))
      ENDIF
      
      YY=((1.0-FOC)/(1.0-XCVM0))**0.333
      
      RKCH=247.0*DEXP(-21060.0/TP)
      
      RKDG=10.0*1.0D-4*(T(I)/2000.0)**0.75*P0/(DP*100.0*PWK)*COEF_A1
      
      RKDA=VOID**2.5*RKDG
      
      XKC_H2O=YY*YY/(1.0/RKCH+YY*YY/RKDG+1.0/RKDA*(YY-YY*YY))
      
      XKC_H2O=XKC_H2O*10.0/1.01325D5/12.0
      RETURN
      END
"""
```

---

## 6. 数学工具模块调用链

### 6.1 块三对角矩阵求解

```python
# Python: src/functions/math_utils.py
# Fortran: Wg9.for (SUBROUTINE BLKTRD)

def blktrd(nmat, nst):
    """
    块三对角矩阵求解器
    """
    nf = nmat
    is_err = 0
    
    zwmat = np.zeros((nmat + 1, nmat + 1))
    zwvek = np.zeros(nmat + 1)
    
    # 前向消元
    for i in range(2, nst + 1):
        # AMAT(i-1) = AMAT(i-1) / BMAT(i-1)
        nfehl, matout = matdiv(
            nf, nmat,
            common.AMAT[:, :, i - 1], -nmat,
            common.BMAT[:, :, i - 1], -nmat,
            nmat, nmat
        )
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
        common.DMAT[1:nmat+1, i] = matout[1:nmat+1, 1]
        is_err = is_err + nfehl
    
    return 0

# Fortran版本 (Wg9.for)
"""
      SUBROUTINE BLKTRD(NMAT,NST)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'
      
      DIMENSION ZWMAT(11,11),ZWVEK(11)
      
      NF=NMAT
      IS_ERR=0
      
      ! 前向消元
      DO 100 I=2,NST
        
        CALL MATDIV(NF,NMAT,AMAT(1,1,I-1),-NMAT,BMAT(1,1,I-1),
     &              -NMAT,NMAT,NMAT,MATDIV_ERR,MATOUT)
        AMAT(:,:,I-1)=MATOUT
        IS_ERR=IS_ERR+MATDIV_ERR
        
        CALL MATMULT(NF,NMAT,CMAT(1,1,I-1),NMAT,AMAT(1,1,I-1),
     &               NMAT,NMAT,NMAT,ZWMAT)
        
        CALL MATSUB(NF,NMAT,BMAT(1,1,I),NMAT,ZWMAT,NMAT,
     &              NMAT,NMAT,BMAT(1,1,I))
        
        CALL MATMULT(NF,NMAT,DMAT(1,I-1),1,AMAT(1,1,I-1),
     &               NMAT,1,NMAT,ZWVEK)
        
        CALL MATSUB(NF,NMAT,DMAT(1,I),1,ZWVEK,1,
     &              1,1,DMAT(1,I))
        
  100 CONTINUE
      
      ! 回代
      DO 200 K=1,NST
        I=NST+1-K
        
        IF(I.NE.NST) THEN
          CALL MATMULT(NF,NMAT,DMAT(1,I+1),1,CMAT(1,1,I),
     &                 NMAT,1,NMAT,ZWVEK)
          
          CALL MATSUB(NF,NMAT,DMAT(1,I),1,ZWVEK,1,
     &                1,1,DMAT(1,I))
        ENDIF
        
        CALL MATDIV(NF,NMAT,DMAT(1,I),1,BMAT(1,1,I),
     &              NMAT,1,NMAT,MATDIV_ERR,MATOUT)
        DMAT(:,I)=MATOUT(:,1)
        IS_ERR=IS_ERR+MATDIV_ERR
        
  200 CONTINUE
      
      RETURN
      END
"""
```

---

## 7. 调用关系总图

```
main()
│
├── eingab()
│   ├── geometry()
│   ├── flucht()
│   │   ├── _flucht_901()
│   ├── qhcrct()
│   └── _read_start_file()
│
├── [迭代循环]
│   │
│   ├── gasifier()
│   │   ├── xmass_func() → xmass()
│   │   │   └── 计算固体质量、停留时间、速度、空隙率
│   │   │
│   │   ├── entfed_func() → entfed()
│   │   ├── entkol_func() → entkol()
│   │   │
│   │   └── [对每个Cell i]
│   │       ├── _calculate_dmat_for_cell()
│   │       │   ├── xk1(i) → CO + 1/2O₂ → CO₂
│   │       │   ├── xk2(i) → H₂ + 1/2O₂ → H₂O
│   │       │   ├── xk3(i) → CO + H₂O → CO₂ + H₂
│   │       │   ├── xk4(i) → CO₂ + H₂ → CO + H₂O
│   │       │   ├── xk5(i) → CH₄ + H₂O → CO + 3H₂
│   │       │   ├── xk6(i) → CH₄ + 2O₂ → CO₂ + 2H₂O
│   │       │   ├── A1(i) → C + H₂O → CO + H₂
│   │       │   ├── A2(i) → C + 2H₂ → CH₄
│   │       │   ├── A3(i) → C + O₂ → CO/CO₂
│   │       │   ├── A4(i) → C + CO₂ → 2CO
│   │       │   ├── A5(i) → CO + H₂O ⇌ CO₂ + H₂
│   │       │   ├── RI(i) → 总碳消耗速率
│   │       │   ├── PHI(i) → 结构参数
│   │       │   ├── TPAR(i) → 颗粒温度
│   │       │   ├── XKC_O2(i) → O₂扩散系数
│   │       │   ├── XKC_H2O(i) → H₂O扩散系数
│   │       │   ├── XKC_CO2(i) → CO₂扩散系数
│   │       │   ├── XKC_H2(i) → H₂扩散系数
│   │       │   └── enthp_func() → ENTHP()
│   │       │
│   │       └── [数值微分构建AMAT, BMAT, CMAT]
│   │
│   ├── newtra()
│   │   ├── blktrd()
│   │   │   ├── matdiv()
│   │   │   ├── matmult()
│   │   │   └── matsub()
│   │   └── kolon1()
│   │
│   └── calculate_residuals()
│
└── kolerg()
    ├── entkol()
    └── entfed()
```

---

*最后更新: 2026-03-20*
