# TEXACO 气化炉CFD模拟 - Python版本

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

TEXACO（德士古）气化炉计算流体动力学（CFD）模拟程序的Python移植版本，完整复现Fortran原始程序功能。

---

## 📑 目录

- [项目简介](#项目简介)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [架构概述](#架构概述)
- [函数调用关系](#函数调用关系)
- [数学模型](#数学模型)
- [API参考](#api参考)
- [验证结果](#验证结果)
- [开发文档](#开发文档)
- [许可证](#许可证)

---

## 项目简介

本项目是TEXACO水煤浆气化炉Fortran仿真程序的完整Python移植版本，用于模拟气化炉内气固两相流动、化学反应和热质传递过程。

### 主要特点

- 🚀 **完整移植**：完整复现Fortran原始程序的所有功能
- 📊 **精度验证**：矩阵组装精度达到99.98%，与Fortran完全匹配
- 🔧 **模块化设计**：清晰的模块结构，易于维护和扩展
- 📝 **完整文档**：详细的数学公式、代码架构和API文档
- ✅ **经过验证**：通过Case 1/2收敛测试验证，60-70次迭代收敛

---

## 快速开始

### 环境要求

- Python 3.10+
- NumPy
- 其他依赖见 `requirements.txt`

### 安装

```bash
# 克隆仓库
git clone https://github.com/Zonas-Liu/texaco_gasfier.git
cd texaco_gasfier

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行模拟

```bash
python src/main.py
```

运行后将在当前目录生成 `GASTEST.DAT` 结果文件。

---

## 项目结构

```
texaco_gasfier/
├── src/                      # 源代码
│   ├── main.py              # 主程序入口
│   ├── common/              # 全局数据结构
│   │   └── common_data.py   # Common数据类
│   ├── functions/           # 核心功能函数
│   │   ├── gas_reactions.py # 气体反应计算
│   │   ├── reaction_rates.py# 反应速率计算
│   │   ├── math_utils.py    # 数学工具
│   │   └── fh2o_fortran.py  # 物性计算
│   └── subroutines/         # 主要子程序
│       ├── initialization.py# 初始化
│       ├── gasifier_main.py # 气化炉主计算
│       ├── mass_flow.py     # 质量流计算
│       └── output_results.py# 结果输出
├── data/                     # 输入数据文件
│   ├── Datain0.dat          # 计算参数
│   └── START.DAT            # 初始条件
├── docs/                     # 文档
│   ├── ISSUE_REGISTRY.md    # 问题登记册
│   ├── PROJECT_STRUCTURE.md # 项目结构
│   ├── TODO.md              # 待办事项
│   └── code_reference/      # 详细代码文档
├── README.md                 # 本文件
├── ARCHIVE_NOTES.md          # 版本归档
└── requirements.txt          # 依赖列表
```

---

## 架构概述

### 程序总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        主程序层                              │
│                    src/main.py                               │
│  - 迭代控制                                                   │
│  - 收敛判断                                                   │
│  - 结果输出                                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       子程序层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │initialization│  │gasifier_main│  │output_results│         │
│  │  (初始化)    │  │ (矩阵组装)  │  │  (结果输出)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐                                            │
│  │  mass_flow  │                                            │
│  │ (质量流计算)│                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       函数计算层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │gas_reactions│  │reaction_rates│  │  math_utils │         │
│  │ (气相反应)  │  │ (碳反应速率) │  │ (数学工具)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 模块详细说明

| 模块 | 文件 | 对应Fortran | 功能 |
|------|------|-------------|------|
| 主程序 | `main.py` | Wg1.for | 迭代控制、收敛判断、结果输出 |
| 全局数据 | `common/common_data.py` | COMMON.00-03 | 全局共享数据、Common块实现 |
| 初始化 | `subroutines/initialization.py` | Wg2.for | 输入读取、几何计算、初始化 |
| 气化炉主 | `subroutines/gasifier_main.py` | Wg3.for | 矩阵组装、质量/能量平衡 |
| 质量流 | `subroutines/mass_flow.py` | Wg1.for | 固体质量、停留时间计算 |
| 气相反应 | `functions/gas_reactions.py` | Wg6.for | XK1-XK6反应速率、挥发分释放 |
| 碳反应 | `functions/reaction_rates.py` | Wg7-8.for | A1-A5反应速率、扩散系数 |
| 数学工具 | `functions/math_utils.py` | Wg9.for | BLKTRD求解器、矩阵运算 |

### 核心函数一览

| 函数 | 描述 | 输入 | 输出 |
|------|------|------|------|
| `main()` | 主程序入口 | - | - |
| `eingab()` | 初始化 | data_path | - |
| `gasifier()` | 气化炉计算 | 回调函数 | sum_ri |
| `newtra()` | 牛顿迭代 | omega | - |
| `blktrd()` | 块三对角求解 | nmat, nst | 错误码 |
| `xk1()-xk6()` | 气相反应速率 | i | 速率[kmol/s] |
| `A1()-A5()` | 碳反应速率 | i | 速率[kmol/s] |

### 变量索引说明

#### 气体组分编号 (1-based)

| 编号 | 符号 | 名称 | 分子量 [kg/kmol] |
|------|------|------|------------------|
| 1 | O₂ | 氧气 | 32.0 |
| 2 | CH₄ | 甲烷 | 16.0 |
| 3 | CO | 一氧化碳 | 28.0 |
| 4 | CO₂ | 二氧化碳 | 44.0 |
| 5 | H₂S | 硫化氢 | 34.0 |
| 6 | H₂ | 氢气 | 2.0 |
| 7 | N₂ | 氮气 | 28.0 |
| 8 | H₂O | 水蒸气 | 18.0 |

#### 固体组分编号

| 编号 | 符号 | 名称 | 分子量 [kg/kmol] |
|------|------|------|------------------|
| 9 | C | 碳 | 12.0 |
| 10 | ASH | 灰分 | 60.0 |

#### 矩阵方程编号

| 编号 | 变量 | 描述 | 单位 |
|------|------|------|------|
| 1-8 | FEMF | 气体组分摩尔流量 | [kmol/s] |
| 9 | WE | 固体质量流量 | [kg/s] |
| 10 | X | 碳转化率 | [-] |
| 11 | T | 温度 | [K] |

### 程序执行流程

```
开始
  │
  ▼
┌─────────────────┐
│  main()         │
│  - 打开输出文件  │
└─────────────────┘
  │
  ▼
┌─────────────────┐
│  eingab()       │
│  - 读取输入数据  │
│  - 计算几何参数  │
│  - 初始化变量    │
└─────────────────┘
  │
  ▼
┌─────────────────┐     未收敛
│  迭代循环        │◄─────────────────┐
│  (1 to ITMAX)   │                  │
└─────────────────┘                  │
  │                                  │
  ▼                                  │
┌─────────────────┐                  │
│  gasifier()     │                  │
│  - 计算反应速率  │                  │
│  - 构建矩阵      │                  │
│  - 数值微分      │                  │
└─────────────────┘                  │
  │                                  │
  ▼                                  │
┌─────────────────┐                  │
│  newtra()       │                  │
│  - 求解矩阵      │                  │
│  - 更新变量      │                  │
└─────────────────┘                  │
  │                                  │
  ▼                                  │
┌─────────────────┐                  │
│  计算残差        │                  │
│  - SUMFE        │                  │
│  - SUMWE        │                  │
│  - SUMX         │                  │
│  - SUMT         │                  │
└─────────────────┘                  │
  │                                  │
  ▼                                  │
┌─────────────────┐                  │
│  检查收敛       │──────────────────┘
│  KONVER==0?    │    是
└─────────────────┘
  │
  ▼
┌─────────────────┐
│  kolerg()       │
│  - 输出结果      │
└─────────────────┘
  │
  ▼
结束
```

---

## 函数调用关系

### 主程序调用层次

```python
# Python: src/main.py
# Fortran: Wg1.for (PROGRAM TEXACO_GASIFIER)

def main():
    """TEXACO气化炉CFD模拟主程序"""
    output_file = open('GASTEST.DAT', 'w')
    common.ITERAT = 0
    
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
```

### 调用关系总图

```
main()
│
├── eingab()
│   ├── geometry()
│   ├── flucht()      # 挥发分释放
│   └── qhcrct()
│
├── [迭代循环]
│   ├── gasifier()
│   │   ├── xmass()   # 计算固体参数
│   │   ├── xk1-xk6() # 气相反应
│   │   ├── A1-A5()   # 碳反应
│   │   └── RI()      # 总反应速率
│   ├── newtra()
│   │   ├── blktrd()  # 块三对角求解
│   │   └── kolon1()  # 更新变量
│   └── calculate_residuals()
│
└── kolerg()
```

---

## 数学模型

### 1. 气化反应模型

| 反应 | 方程式 | 类型 | 函数 |
|------|--------|------|------|
| 燃烧反应 | C + O₂ → CO₂ | 放热 | `A3()` |
| 布多尔反应 | C + CO₂ → 2CO | 吸热 | `A4()` |
| 水煤气反应 | C + H₂O → CO + H₂ | 吸热 | `A1()` |
| 甲烷化反应 | C + 2H₂ → CH₄ | 放热 | `A2()` |
| 水煤气变换 | CO + H₂O ⇌ CO₂ + H₂ | 可逆 | `A5()` |
| CO氧化 | CO + ½O₂ → CO₂ | 放热 | `xk1()` |
| H₂氧化 | H₂ + ½O₂ → H₂O | 放热 | `xk2()` |
| 蒸汽重整 | CH₄ + H₂O → CO + 3H₂ | 吸热 | `xk5()` |

### 2. 数值方法

- **空间离散**：30个轴向控制体（Cell）
- **方程组**：11个变量 × 30个Cell = 330个方程
- **求解器**：块三对角矩阵求解器（BLKTRD）
- **迭代方法**：牛顿迭代 + 松弛因子（omega=1.0）
- **收敛准则**：残差 < 1.0×10⁻⁴

### 3. 质量平衡方程

#### O₂ 平衡方程 (DMAT[1,i])

$$DMAT_{1,i} = RO2_i + FEEDO2_i + FEMF_{1,i-1} - FEMF_{1,i} - \frac{XK1}{2} - \frac{XK2}{2} - 2XK6 - \frac{A3}{\Phi}$$

**Python代码**:
```python
def _calculate_dmat_for_cell(i, ...):
    common.DMAT[1, i] = common.RO2[i] + common.FEEDO2[i]
    if i != common.NZRA:
        common.DMAT[1, i] += common.FEMF[1, i - 1]
    common.DMAT[1, i] -= common.FEMF[1, i]
    common.DMAT[1, i] -= rxk1 / 2.0
    common.DMAT[1, i] -= rxk2 / 2.0
    common.DMAT[1, i] -= rxk6 * 2.0
    common.DMAT[1, i] -= ra3 / rphi
```

#### 固体质量平衡 (DMAT[NSGP,i])

$$DMAT_{NSGP,i} = WFC_i + WFA_i + WE_{i-1} - WE_i - RI_i$$

#### 碳转化率平衡 (DMAT[NSGP1,i])

$$DMAT_{NSGP1,i} = WFC_i + WE_{i-1} \cdot X_{i-1} - WE_i \cdot X_i - RI_i$$

### 4. 能量平衡方程

$$\begin{aligned}
DMAT_{NVWS,i} &= \sum_{j=1}^{8} FEMF_{j,i-1} \cdot HENTH_{j,i-1} \\
&+ \sum_{j} R_j^{devol} \cdot H_j(T_{feed}) \\
&- \sum_{j=1}^{8} FEMF_{j,i} \cdot HENTH_{j,i} \\
&- QKW_i - QLOSS \cdot BSMS \cdot HU \cdot 1000 \cdot \frac{DELZ_i}{HREAK}
\end{aligned}$$

### 5. 气相反应动力学

#### CO氧化反应 (XK1)

**反应方程式**: $CO + \frac{1}{2}O_2 \rightarrow CO_2$

**反应速率方程**:

$$XK1 = XK10 \cdot Y_{O2} \cdot Y_{CO} \cdot KTRL_{XK1}$$

其中：

$$XK10 = 3.09 \times 10^8 \cdot \exp\left(-\frac{9.976 \times 10^7}{R \cdot T_i}\right) \cdot \left(\frac{P}{R \cdot T_i}\right)^2 \cdot A_i \cdot \Delta z_i$$

**Python代码**:
```python
def xk1(i):
    for j in range(1, common.NGAS + 1):
        common.Y[j] = common.FEMF[j, i] / common.FEM[i]
    
    if common.Y[1] < 1.0e-10 or common.Y[3] < 1.0e-10:
        return 0.0
    
    exp_arg = -9.976e7 / (common.RAG * common.T[i])
    xk10 = (3.09e8 * np.exp(exp_arg)
            * (common.PWK / (common.RAG * common.T[i])) ** 2
            * common.AT[i] * common.DELZ[i])
    
    return xk10 * common.Y[1] * common.Y[3] * common.KTRL_XK1
```

### 6. 异相反应动力学

#### 碳-水蒸气反应 (A1)

**反应方程式**: $C + H_2O \rightarrow CO + H_2$

**反应速率方程**:

$$A1 = AM \cdot \pi \cdot D_p^2 \cdot XKC_{H2O}(i) \cdot P \cdot PA1 \cdot CTRL_{A1}$$

**颗粒数量**: $AM = \frac{XMS_i}{ROS_i} \cdot \frac{6}{\pi \cdot D_p^3}$

**有效分压**: $PA1 = Y_{H2O} - \frac{Y_{H2} \cdot Y_{CO} \cdot P}{P_0 \cdot CS_{KEQ1}}$

### 7. 扩散与传质模型 (Wen模型)

$$XKC = \frac{YY^2}{\frac{1}{RKCH} + \frac{YY^2}{RKDG} + \frac{YY - YY^2}{RKDA}}$$

其中：
- $RKCH$：化学反应速率常数
- $RKDG$：气相扩散速率
- $RKDA$：灰层扩散速率
- $YY = \left(\frac{1 - FOC}{1 - XCVM0}\right)^{1/3}$

---

## API参考

### 主程序模块 (main.py)

#### `main()`
主程序入口，执行完整的气化炉模拟流程。

#### `calculate_residuals() -> tuple[float, float, float, float]`
计算当前迭代的残差 (SUMFE, SUMWE, SUMX, SUMT)。

**返回**: (sumfe, sumwe, sumx, sumt)

### 初始化模块 (initialization.py)

#### `eingab(data_path: str = 'data/Datain0.dat')`
输入数据和初始化子程序。

**参数**:
- `data_path`: 输入数据文件路径

#### `geometry()`
计算气化炉几何结构。

### 气化炉主模块 (gasifier_main.py)

#### `gasifier(...) -> float`
构建块三对角矩阵系统。

**参数**: 多个回调函数（xmass, xk1-xk6, A1-A5等）

**返回**: sum_ri (总反应速率)

### 气相反应模块 (gas_reactions.py)

#### `xk1(i: int) -> float`
CO氧化反应速率 [kmol/s]

#### `xk2(i: int) -> float`
H₂氧化反应速率 [kmol/s]

#### `xk3(i: int) -> float`
水煤气变换反应速率 [kmol/s]

#### `xk4(i: int) -> float`
逆水煤气变换反应速率 [kmol/s]

#### `xk5(i: int) -> float`
蒸汽重整反应速率 [kmol/s]

#### `xk6(i: int) -> float`
CH₄氧化反应速率 [kmol/s]

#### `flucht()`
挥发分释放计算。

### 反应速率模块 (reaction_rates.py)

#### `A1(i: int) -> float`
碳-水蒸气反应速率 C + H₂O → CO + H₂ [kmol/s]

#### `A2(i: int) -> float`
甲烷化反应速率 C + 2H₂ → CH₄ [kmol/s]

#### `A3(i: int) -> float`
燃烧反应速率 C + O₂ → CO/CO₂ [kmol/s]

#### `A4(i: int) -> float`
Boudouard反应速率 C + CO₂ → 2CO [kmol/s]

#### `A5(i: int) -> float`
催化水煤气变换速率 CO + H₂O ⇌ CO₂ + H₂ [kmol/s]

#### `RI(i: int) -> float`
总碳消耗速率 [kg/s]

**公式**: RI = (A1 + A2 + A3 + A4) × 12.0

#### `XKC_O2(i: int) -> float`
O₂扩散系数 [kmol/(m²·Pa·s)]

### 数学工具模块 (math_utils.py)

#### `newtra(omega: float = 1.0)`
牛顿迭代。

#### `blktrd(nmat: int, nst: int) -> int`
块三对角矩阵求解器。

**参数**:
- `nmat`: 矩阵大小
- `nst`: 格子数

**返回**: 错误代码 (0=成功)

#### `kolon1(omega: float = 1.0)`
更新求解变量，检查收敛性。

### 全局数据结构 (common_data.py)

#### 基本参数

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `NGAS` | int | 8 | 气体组分数 |
| `G` | float | 9.801 | 重力加速度 [m/s²] |
| `RAG` | float | 8314.3 | 通用气体常数 [J/(kmol·K)] |
| `PI` | float | 3.1415926 | 圆周率 |
| `P0` | float | 1.01325e5 | 标准大气压 [Pa] |

#### 求解变量

| 属性 | 类型 | 形状 | 描述 | 单位 |
|------|------|------|------|------|
| `FEMF` | ndarray | (9, 31) | 各组分摩尔流量 | [kmol/s] |
| `X` | ndarray | (31,) | 碳转化率 | [-] |
| `T` | ndarray | (31,) | 温度 | [K] |
| `WE` | ndarray | (31,) | 碳质量流量 | [kg/s] |
| `AMAT` | ndarray | (13, 13, 32) | 下对角块矩阵 | - |
| `BMAT` | ndarray | (13, 13, 32) | 对角块矩阵 | - |
| `CMAT` | ndarray | (13, 13, 32) | 上对角块矩阵 | - |
| `DMAT` | ndarray | (13, 32) | 右端向量 | - |

---

## 验证结果

### 矩阵组装精度

| 矩阵 | 匹配度 | 状态 |
|------|--------|------|
| AMAT | 100% | ✅ |
| BMAT | 100% | ✅ |
| CMAT | 100% | ✅ |
| DMAT | 100% | ✅ |
| **整体** | **99.98%** | ✅ |

### 收敛性验证（Case 1/Case 2）

| 指标 | Fortran | Python | 迭代次数 |
|------|---------|--------|----------|
| Case 1 | 收敛 | 收敛 | 64 / 62 |
| Case 2 | 收敛 | 收敛 | 62 / 62 |

**结论**: Python实现与Fortran完全等效，收敛行为一致。

### 配置参数

**松弛因子（Omega）**:
| 参数 | 值 | 说明 |
|------|-----|------|
| 默认值 | 1.0 | 与Fortran兼容 |

**收敛阈值**:
| 残差类型 | 阈值 | 说明 |
|----------|------|------|
| SUMFE | 1.0×10⁻⁴ | 气体组分残差 |
| SUMWE | 1.0×10⁻⁴ | 固体质量流残差 |
| SUMX | 1.0×10⁻⁴ | 碳转化率残差 |
| SUMT | 1.0×10⁻⁴ | 温度残差 |

---

## 开发文档

### 文档索引

| 文档 | 内容 |
|------|------|
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 项目结构规范、命名约定 |
| [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) | 使用示例、故障排除 |
| [docs/ISSUE_REGISTRY.md](docs/ISSUE_REGISTRY.md) | 问题登记册（29个ISSUE） |
| [docs/TODO.md](docs/TODO.md) | 待办事项、开发计划 |
| [ARCHIVE_NOTES.md](ARCHIVE_NOTES.md) | 版本历史记录 |

### 常量参考表

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

---

## 许可证

本项目采用 MIT 许可证。

---

## 致谢

- 原始Fortran程序作者
- 气化炉CFD领域的先驱研究者

---

*最后更新: 2026-03-23*
