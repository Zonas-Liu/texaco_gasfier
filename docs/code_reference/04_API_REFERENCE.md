# TEXACO Python版本 - API函数参考手册

本文档提供TEXACO气化炉模拟程序所有函数的完整API参考。

---

## 目录

1. [主程序模块 (main.py)](#1-主程序模块-mainpy)
2. [全局数据模块 (common_data.py)](#2-全局数据模块-common_datapy)
3. [初始化模块 (initialization.py)](#3-初始化模块-initializationpy)
4. [气化炉主模块 (gasifier_main.py)](#4-气化炉主模块-gasifier_mainpy)
5. [质量流模块 (mass_flow.py)](#5-质量流模块-mass_flowpy)
6. [气相反应模块 (gas_reactions.py)](#6-气相反应模块-gas_reactionspy)
7. [反应速率模块 (reaction_rates.py)](#7-反应速率模块-reaction_ratespy)
8. [数学工具模块 (math_utils.py)](#8-数学工具模块-math_utilspy)

---

## 1. 主程序模块 (main.py)

### 1.1 main()

```python
def main()
```

**描述**: TEXACO气化炉CFD模拟主程序入口

**参数**: 无

**返回值**: 无

**功能**:
1. 打开输出文件 `GASTEST.DAT`
2. 调用 `eingab()` 进行初始化
3. 执行主迭代循环
4. 调用 `gasifier()` 进行气化炉计算
5. 调用 `newtra()` 进行牛顿迭代求解
6. 计算残差并检查收敛
7. 输出结果

**调用示例**:
```python
if __name__ == "__main__":
    main()
```

---

### 1.2 calculate_residuals()

```python
def calculate_residuals() -> tuple[float, float, float, float]
```

**描述**: 计算当前迭代的残差 (SUMFE, SUMWE, SUMX, SUMT)

**参数**: 无

**返回**: 
- `sumfe` (float): 气体组分残差
- `sumwe` (float): 固体质量流残差  
- `sumx` (float): 碳转化率残差
- `sumt` (float): 温度残差

**注意**: DMAT使用1-based索引（与Fortran兼容）

**数学公式**:
```
SUMFE = Σ|DMAT[j,i]|  (j=1 to NVE, i=NZEL1 to NZEL2)
SUMWE = Σ|DMAT[NSGP,i]|  (i=NZEL1 to NZEL2)
SUMX  = Σ|DMAT[NSGP1,i]|  (i=NZEL1 to NZEL2)
SUMT  = Σ|DMAT[NVWS,i]|  (i=NZEL1 to NZEL2)
```

---

### 1.3 print_matrices_iter0()

```python
def print_matrices_iter0()
```

**描述**: 打印第一次迭代前的矩阵（用于与Fortran对比）

**参数**: 无

**返回值**: 无

**输出文件**: `python_matrix_iter0.txt`

---

## 2. 全局数据模块 (common_data.py)

### 2.1 CommonData 类

```python
class CommonData()
```

**描述**: 单例类，用于存储全局共享数据，对应Fortran的Common块

**单例访问**:
```python
from common.common_data import common
```

#### 2.1.1 基本参数 (Common.00)

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `NGAS` | int | 8 | 气体组分数 |
| `G` | float | 9.801 | 重力加速度 [m/s²] |
| `RAG` | float | 8314.3 | 通用气体常数 [J/(kmol·K)] |
| `PI` | float | 3.1415926 | 圆周率 |
| `P0` | float | 1.01325e5 | 标准大气压 [Pa] |

#### 2.1.2 结构参数

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `NZWS` | int | 30 | 网格数 |
| `NZEL1` | int | 1 | 起始网格索引 |
| `NZEL2` | int | 30 | 结束网格索引 |
| `NZRA` | int | 1 | 反应区起始索引 |
| `NZRE` | int | 30 | 反应区结束索引 |
| `NVE` | int | 8 | 气体组分数 |
| `NSGP` | int | 9 | 固体质量流方程索引 |
| `NSGP1` | int | 10 | 碳转化率方程索引 |
| `NVWS` | int | 11 | 温度方程索引 |

#### 2.1.3 几何参数 (Common.01)

| 属性 | 类型 | 形状 | 描述 |
|------|------|------|------|
| `H` | ndarray | (31,) | 格子高度位置 [m] |
| `DELZ` | ndarray | (31,) | 格子高度 [m] |
| `AT` | ndarray | (31,) | 格子截面积 [m²] |
| `AR` | ndarray | (31,) | 格子周长 [m] |
| `HREAK` | float | - | 炉总高度 [m] |
| `DIA1-8` | float | - | 各段直径 [m] |

#### 2.1.4 求解变量 (Common.02)

| 属性 | 类型 | 形状 | 描述 | 单位 |
|------|------|------|------|------|
| `FEMF` | ndarray | (9, 31) | 各组分摩尔流量 | [kmol/s] |
| `X` | ndarray | (31,) | 碳转化率 | [-] |
| `T` | ndarray | (31,) | 温度 | [K] |
| `WE` | ndarray | (31,) | 碳质量流量 | [kg/s] |
| `FEM` | ndarray | (31,) | 总摩尔流量 | [kmol/s] |
| `U0` | ndarray | (31,) | 气体速度 | [m/s] |
| `US` | ndarray | (31,) | 颗粒速度 | [m/s] |
| `TRZ` | ndarray | (31,) | 停留时间 | [s] |
| `XMS` | ndarray | (31,) | 格子内固体质量 | [kg] |
| `EPS` | ndarray | (31,) | 空隙率 | [-] |

#### 2.1.5 矩阵 (Common.03)

| 属性 | 类型 | 形状 | 描述 |
|------|------|------|------|
| `AMAT` | ndarray | (13, 13, 32) | 下对角块矩阵 |
| `BMAT` | ndarray | (13, 13, 32) | 对角块矩阵 |
| `CMAT` | ndarray | (13, 13, 32) | 上对角块矩阵 |
| `DMAT` | ndarray | (13, 32) | 右端向量 |

---

## 3. 初始化模块 (initialization.py)

### 3.1 eingab()

```python
def eingab(data_path: str = 'data/Datain0.dat')
```

**描述**: 输入数据和初始化子程序

**参数**:
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `data_path` | str | 'data/Datain0.dat' | 输入数据文件路径 |

**返回值**: 无

**功能**:
1. 设置分子量和基本参数
2. 读取输入参数文件
3. 计算派生量
4. 调用 `geometry()` 和 `qhcrct()`
5. 初始化未知数

**调用示例**:
```python
from subroutines.initialization import eingab
eingab('data/Datain0.dat')
```

---

### 3.2 geometry()

```python
def geometry()
```

**描述**: 计算气化炉几何结构

**参数**: 无

**返回值**: 无

**功能**:
- 设置8个不同直径的炉段
- 计算每个格子的高度DELZ和位置H
- 计算每个格子的截面积AT和周长AR

---

### 3.3 qhcrct()

```python
def qhcrct()
```

**描述**: 热量校正计算

**参数**: 无

**返回值**: 无

**功能**:
- 计算挥发分释放的热量校正QH_CRCT
- 计算热解后的焓值

---

## 4. 气化炉主模块 (gasifier_main.py)

### 4.1 gasifier()

```python
def gasifier(
    xmass_func: Callable,
    entfed_func: Callable,
    entkol_func: Callable,
    xk1_func: Callable,
    xk2_func: Callable,
    xk3_func: Callable,
    xk4_func: Callable,
    xk5_func: Callable,
    xk6_func: Callable,
    a1_func: Callable,
    a2_func: Callable,
    a3_func: Callable,
    a4_func: Callable,
    a5_func: Callable,
    phi_func: Callable,
    ri_func: Callable,
    enthp_func: Callable,
    wdkr_func: Callable | None = None
) -> float
```

**描述**: GASIFIER主计算子程序，构建块三对角矩阵系统

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `xmass_func` | Callable | XMASS子程序函数 |
| `entfed_func` | Callable | ENTFED子程序函数 |
| `entkol_func` | Callable | ENTKOL子程序函数 |
| `xk1_func-xk6_func` | Callable | 气相反应速率函数 |
| `a1_func-a5_func` | Callable | 碳反应速率函数 |
| `phi_func` | Callable | PHI辅助函数 |
| `ri_func` | Callable | RI总反应速率函数 |
| `enthp_func` | Callable | ENTHP焓值计算函数 |
| `wdkr_func` | Callable \| None | WDKR热传导系数函数 |

**返回**: `sum_ri` (float): 总反应速率

**调用示例**:
```python
from subroutines.gasifier_main import gasifier
from functions.gas_reactions import xk1, xk2, xk3, xk4, xk5, xk6
from functions.reaction_rates import A1, A2, A3, A4, A5, PHI, RI, ENTHP
from subroutines.mass_flow import xmass
from subroutines.output_results import entfed, entkol

sum_ri = gasifier(
    xmass_func=xmass,
    entfed_func=entfed,
    entkol_func=entkol,
    xk1_func=xk1, xk2_func=xk2, xk3_func=xk3, xk4_func=xk4, xk5_func=xk5, xk6_func=xk6,
    a1_func=A1, a2_func=A2, a3_func=A3, a4_func=A4, a5_func=A5,
    phi_func=PHI, ri_func=RI,
    enthp_func=ENTHP
)
```

---

### 4.2 _calculate_dmat_for_cell()

```python
def _calculate_dmat_for_cell(
    i: int,
    xmass_func: Callable,
    entfed_func: Callable,
    entkol_func: Callable,
    xk1_func: Callable,
    xk2_func: Callable,
    xk3_func: Callable,
    xk4_func: Callable,
    xk5_func: Callable,
    xk6_func: Callable,
    a1_func: Callable,
    a2_func: Callable,
    a3_func: Callable,
    a4_func: Callable,
    a5_func: Callable,
    phi_func: Callable,
    ri_func: Callable,
    enthp_func: Callable,
    wdkr_func: Callable | None = None
) -> float
```

**描述**: 计算单个网格单元的DMAT（右端向量RHS）

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `i` | int | 当前网格单元索引 |
| 其他 | Callable | 各种物理计算函数 |

**返回**: `rri` (float): 总反应速率RI(I)

---

## 5. 质量流模块 (mass_flow.py)

### 5.1 xmass()

```python
def xmass()
```

**描述**: 计算每个网格单元的固体质量、停留时间、颗粒速度和空隙率

**参数**: 无

**返回值**: 无

**计算变量**:
- `ROS[i]`: 固体密度 [kg/m³]
- `ROG[i]`: 气体密度 [kg/m³]
- `XMUG[i]`: 气体粘度 [Pa·s]
- `TRZ[i]`: 停留时间 [s]（迭代计算）
- `US[i]`: 颗粒速度 [m/s]
- `XMS[i]`: 格子内固体质量 [kg]
- `EPS[i]`: 空隙率 [-]

---

## 6. 气相反应模块 (gas_reactions.py)

### 6.1 xk1() - CO氧化反应

```python
def xk1(i: int) -> float
```

**描述**: CO + 1/2 O₂ → CO₂ 反应速率

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `i` | int | 格子索引 (1-based) |

**返回**: 反应速率 [kmol/s]

**参考**: CEN KEFA AND ZHAO LI

---

### 6.2 xk2() - H₂氧化反应

```python
def xk2(i: int) -> float
```

**描述**: H₂ + 1/2 O₂ → H₂O 反应速率

**参考**: ZHAO LI AND CEN KEFA

---

### 6.3 xk3() - 水煤气变换反应

```python
def xk3(i: int) -> float
```

**描述**: CO + H₂O → CO₂ + H₂ 反应速率

**参考**: CEN KEFA AND ZHAO LI

---

### 6.4 xk4() - 逆水煤气变换反应

```python
def xk4(i: int) -> float
```

**描述**: CO₂ + H₂ → CO + H₂O 反应速率

**参考**: CEN KEFA (6.245E14), ZHAO LI (7.145E14)

---

### 6.5 xk5() - 蒸汽重整反应

```python
def xk5(i: int) -> float
```

**描述**: CH₄ + H₂O → CO + 3H₂ 反应速率

**参考**: WEN

---

### 6.6 xk6() - CH₄氧化反应

```python
def xk6(i: int) -> float
```

**描述**: CH₄ + 2O₂ → CO₂ + 2H₂O 反应速率

**参考**: CEN KEFA P320

---

### 6.7 flucht() - 挥发分释放

```python
def flucht()
```

**描述**: 挥发分释放计算子程序

**功能**:
1. 初始化挥发分释放系数
2. 根据煤的工业分析计算各挥发分组分
3. 处理H和O元素的平衡
4. 计算各格子中的挥发分释放速率

---

## 7. 反应速率模块 (reaction_rates.py)

### 7.1 A1() - 碳-水蒸气反应

```python
def A1(i: int) -> float
```

**描述**: 计算碳与水蒸气反应速率 C + H₂O → CO + H₂

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `i` | int | 格子索引 (1-based) |

**返回**: 反应速率 [kmol/s]

---

### 7.2 A2() - 甲烷化反应

```python
def A2(i: int) -> float
```

**描述**: 计算碳与氢气反应速率 C + 2H₂ → CH₄

---

### 7.3 A3() - 燃烧反应

```python
def A3(i: int) -> float
```

**描述**: 计算碳与氧气反应速率 C + O₂ → CO/CO₂

---

### 7.4 A4() - Boudouard反应

```python
def A4(i: int) -> float
```

**描述**: 计算碳与二氧化碳反应速率 C + CO₂ → 2CO

---

### 7.5 A5() - 催化水煤气变换

```python
def A5(i: int) -> float
```

**描述**: 计算催化水煤气变换反应速率 CO + H₂O ⇌ CO₂ + H₂

---

### 7.6 RI() - 总碳消耗速率

```python
def RI(i: int) -> float
```

**描述**: 计算总碳消耗速率

**公式**: RI = (A1 + A2 + A3 + A4) × 12.0 [kg/s]

---

### 7.7 PHI() - 结构参数

```python
def PHI(i: int) -> float
```

**描述**: 计算机械因子/结构参数 (Mechanical Factor)

**参考**: Wen模型

---

### 7.8 TPAR() - 颗粒温度

```python
def TPAR(i: int) -> float
```

**描述**: 计算颗粒温度

**公式**: TP = T[i] + FEMF[1,i]/FEM[i] × 66.0e3 × PWK/(RAG×T[i])

---

### 7.9 XKC系列 - 扩散系数

```python
def XKC_O2(i: int) -> float   # O₂扩散系数
def XKC_H2O(i: int) -> float  # H₂O扩散系数
def XKC_CO2(i: int) -> float  # CO₂扩散系数
def XKC_H2(i: int) -> float   # H₂扩散系数
```

**描述**: 计算各种气体与碳反应的扩散系数

**单位**: kmol/(m²·Pa·s)

---

### 7.10 ENTHP() - 焓值计算

```python
def ENTHP(J: int, IAGG: str, TEMP: float, PP: float) -> float
```

**描述**: 计算组分J在温度TEMP和压力PP下的焓值

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `J` | int | 组分编号 (1-10) |
| `IAGG` | str | 聚集态 ('G'气态, 'S'固态) |
| `TEMP` | float | 温度 [K] |
| `PP` | float | 压力 [Pa] |

**返回**: 焓值 [J/kmol]

---

## 8. 数学工具模块 (math_utils.py)

### 8.1 newtra()

```python
def newtra(omega: float = 1.0)
```

**描述**: 牛顿迭代

**参数**:
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `omega` | float | 1.0 | 松弛因子 (0 < omega <= 1) |

---

### 8.2 blktrd()

```python
def blktrd(nmat: int, nst: int) -> int
```

**描述**: 块三对角矩阵求解器

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `nmat` | int | 矩阵大小 |
| `nst` | int | 格子数 |

**返回**: 错误代码 (0=成功)

---

### 8.3 kolon1()

```python
def kolon1(omega: float = 1.0)
```

**描述**: 更新求解变量，检查收敛性

**参数**:
| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `omega` | float | 1.0 | 松弛因子 |

**功能**:
1. 更新组分流量FEMF
2. 更新碳质量流量WE
3. 更新碳转化率X
4. 更新温度T
5. 检查各变量的收敛性

---

### 8.4 gausll()

```python
def gausll(n: int, ns: int, a: ndarray) -> tuple[int, ndarray]
```

**描述**: 高斯消元法求解线性方程组

**参数**:
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `n` | int | 系数矩阵的维数 |
| `ns` | int | 右侧矩阵的列数 |
| `a` | ndarray | 增广矩阵 (n × (n+ns)) |

**返回**: `(nfehl, a)`
- `nfehl` (int): 错误代码 (0=成功)
- `a` (ndarray): 求解后的矩阵

---

### 8.5 矩阵运算函数

```python
def matadd(nf: int, ng: int, matin1: ndarray, nan1x: int,
           matin2: ndarray, nan2x: int, ndi1: int, ndi2: int) -> ndarray

def matsub(nf: int, ng: int, matin1: ndarray, nan1x: int,
           matin2: ndarray, nan2x: int, ndi1: int, ndi2: int) -> ndarray

def matmult(nf: int, ng: int, matin1: ndarray, nan1x: int,
            matin2: ndarray, nan2x: int, ndi1: int, ndi2: int) -> ndarray

def matdiv(nf: int, ng: int, matin1: ndarray, nan1x: int,
           matin2: ndarray, nan2x: int, ndi1: int, ndi2: int) -> tuple[int, ndarray]
```

**描述**: 矩阵加、减、乘、除运算

---

## 附录：常量参考表

### 气体组分分子量

| 编号 | 组分 | 分子量 [kg/kmol] |
|------|------|------------------|
| 1 | O₂ | 32.0 |
| 2 | CH₄ | 16.0 |
| 3 | CO | 28.0 |
| 4 | CO₂ | 44.0 |
| 5 | H₂S | 34.0 |
| 6 | H₂ | 2.0 |
| 7 | N₂ | 28.0 |
| 8 | H₂O | 18.0 |
| 9 | C (固体) | 12.0 |
| 10 | ASH (固体) | 60.0 |

### 收敛阈值

| 变量 | 阈值 | 描述 |
|------|------|------|
| `SKONFE` | 1.0e-4 | 气体组分收敛阈值 |
| `SKONWE` | 1.0e-4 | 固体质量流收敛阈值 |
| `SKONX` | 1.0e-4 | 碳转化率收敛阈值 |
| `SKONT` | 1.0e-4 | 温度收敛阈值 |

---

*最后更新: 2026-03-20*
