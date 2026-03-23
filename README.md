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
- [数学模型](#数学模型)
- [验证结果](#验证结果)
- [API参考](#api参考)
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

### 程序架构

```
┌─────────────────────────────────────────────────────────────┐
│                        主程序层                              │
│                    src/main.py                               │
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
# 或 source venv/bin/activate  # Linux/Mac

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
│   │   ├── __init__.py
│   │   └── common_data.py   # Common数据类（对应Fortran Common块）
│   ├── functions/           # 核心功能函数
│   │   ├── __init__.py
│   │   ├── gas_reactions.py # 气体反应计算（XK1-XK6）
│   │   ├── reaction_rates.py# 反应速率计算（A1-A5）
│   │   ├── math_utils.py    # 数学工具（BLKTRD求解器）
│   │   └── fh2o_fortran.py  # 物性计算
│   └── subroutines/         # 主要子程序
│       ├── __init__.py
│       ├── initialization.py# 初始化（EINGAB）
│       ├── gasifier_main.py # 气化炉主计算（GASIFIER）
│       ├── mass_flow.py     # 质量流计算（XMASS）
│       └── output_results.py# 结果输出（KOLERG）
├── data/                     # 输入数据文件
│   ├── Datain0.dat          # 计算参数
│   └── START.DAT            # 初始条件
├── docs/                     # 文档
│   ├── ISSUE_REGISTRY.md    # 问题登记册
│   ├── PROJECT_STRUCTURE.md # 项目结构说明
│   ├── TODO.md              # 待办事项
│   ├── USAGE_EXAMPLES.md    # 使用示例
│   └── code_reference/      # 详细代码文档
│       ├── 01_MODULE_OVERVIEW.md    # 模块划分与架构
│       ├── 02_CALL_HIERARCHY.md     # 函数调用关系
│       ├── 03_MATHEMATICAL_MODELS.md# 数学物理模型
│       └── 04_API_REFERENCE.md      # API参考手册
├── README.md                 # 本文件
├── ARCHIVE_NOTES.md          # 版本归档说明
└── requirements.txt          # 依赖列表
```

---

## 架构概述

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

#### 矩阵方程编号

| 编号 | 变量 | 描述 | 单位 |
|------|------|------|------|
| 1-8 | FEMF | 气体组分摩尔流量 | [kmol/s] |
| 9 | WE | 固体质量流量 | [kg/s] |
| 10 | X | 碳转化率 | [-] |
| 11 | T | 温度 | [K] |

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

### 3. 核心数学方程

**质量平衡方程**（以O₂为例）：
```
DMAT[1,i] = RO2[i] + FEEDO2[i] + FEMF[1,i-1] - FEMF[1,i]
            - XK1/2 - XK2/2 - 2·XK6 - A3/Φ
```

**扩散系数计算**（Wen模型）：
```
XKC = YY² / (1/RKCH + YY²/RKDG + (YY-YY²)/RKDA)
```

详见 [docs/code_reference/03_MATHEMATICAL_MODELS.md](docs/code_reference/03_MATHEMATICAL_MODELS.md)

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
| 推荐范围 | 0.8 - 1.0 | 稳定收敛 |

**收敛阈值**:
| 残差类型 | 阈值 | 说明 |
|----------|------|------|
| SUMFE | 1.0×10⁻⁴ | 气体组分残差 |
| SUMWE | 1.0×10⁻⁴ | 固体质量流残差 |
| SUMX | 1.0×10⁻⁴ | 碳转化率残差 |
| SUMT | 1.0×10⁻⁴ | 温度残差 |

---

## API参考

### 主要函数API

#### `main()`
主程序入口，执行完整的气化炉模拟流程。

#### `gasifier(...)`
```python
def gasifier(
    xmass_func, entfed_func, entkol_func,
    xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func,
    a1_func, a2_func, a3_func, a4_func, a5_func,
    phi_func, ri_func, enthp_func, wdkr_func=None
) -> float
```
构建块三对角矩阵系统，计算质量平衡和能量平衡。

#### `newtra(omega=1.0)`
执行牛顿迭代，求解线性方程组并更新变量。

#### `blktrd(nmat, nst)`
块三对角矩阵求解器，使用高斯消元法求解330×330矩阵系统。

#### `xk1(i) -> float`
计算CO氧化反应速率（CO + ½O₂ → CO₂）。

#### `A1(i) -> float`
计算碳-水蒸气反应速率（C + H₂O → CO + H₂）。

#### `XKC_H2O(i) -> float`
计算水蒸气扩散系数（kmol/(m²·Pa·s)）。

完整API文档见 [docs/code_reference/04_API_REFERENCE.md](docs/code_reference/04_API_REFERENCE.md)

---

## 开发文档

### 详细文档索引

| 文档 | 内容 | 适用读者 |
|------|------|----------|
| [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 项目结构规范、命名约定 | 开发者 |
| [USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) | 使用示例、故障排除 | 用户 |
| [ISSUE_REGISTRY.md](docs/ISSUE_REGISTRY.md) | 问题登记册（29个ISSUE） | 开发者 |
| [TODO.md](docs/TODO.md) | 待办事项、开发计划 | 维护者 |
| [ARCHIVE_NOTES.md](ARCHIVE_NOTES.md) | 版本历史记录 | 维护者 |

### 代码参考文档

| 文档 | 内容 |
|------|------|
| [01_MODULE_OVERVIEW.md](docs/code_reference/01_MODULE_OVERVIEW.md) | 模块划分、架构图、变量索引、执行流程 |
| [02_CALL_HIERARCHY.md](docs/code_reference/02_CALL_HIERARCHY.md) | 函数调用关系、Python/Fortran代码对照 |
| [03_MATHEMATICAL_MODELS.md](docs/code_reference/03_MATHEMATICAL_MODELS.md) | 数学物理方程详解、反应动力学 |
| [04_API_REFERENCE.md](docs/code_reference/04_API_REFERENCE.md) | 完整API文档、函数参数、常量表 |

---

## 函数调用关系总图

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

## 已知问题

### 收敛性
- ✅ **已修复** - Python与Fortran均在60-70次迭代内收敛
- 关键修复：松弛因子omega=1.0，矩阵索引修正(NSGP=9, NSGP1=10, NVWS=11)
- Case 1/Case 2测试通过，与Fortran结果等效

### 性能
- 330×330矩阵求解计算量较大
- 可考虑Numba加速或并行优化

详见 [docs/ISSUE_REGISTRY.md](docs/ISSUE_REGISTRY.md)

---

## 许可证

本项目采用 MIT 许可证。

---

## 致谢

- 原始Fortran程序作者
- 气化炉CFD领域的先驱研究者

---

*最后更新: 2026-03-23*
