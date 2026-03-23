# TEXACO Python版本 - 项目结构说明

本文档详细说明项目的目录结构和文件组织规范。

---

## 目录结构

```
python_final/
├── src/                          # 源代码目录
│   ├── main.py                  # 主程序入口
│   ├── common/                  # 全局数据结构和常量
│   │   ├── __init__.py
│   │   └── common_data.py       # Common类定义
│   ├── functions/               # 核心计算函数
│   │   ├── __init__.py
│   │   ├── fh2o_fortran.py      # 物性计算
│   │   ├── gas_reactions.py     # 气体反应速率
│   │   ├── math_utils.py        # 数学工具/求解器
│   │   └── reaction_rates.py    # 反应速率计算
│   └── subroutines/             # 主要子程序
│       ├── __init__.py
│       ├── gasifier_main.py     # 气化炉主计算
│       ├── initialization.py    # 初始化程序
│       ├── mass_flow.py         # 质量流计算
│       └── output_results.py    # 结果输出
├── data/                         # 输入数据文件
│   ├── Datain0.dat              # 计算参数
│   └── START.DAT                # 初始条件
├── docs/                         # 项目文档
│   ├── ISSUE_REGISTRY.md        # 问题登记册
│   ├── PROJECT_STRUCTURE.md     # 本文件
│   └── TODO.md                  # 待办事项
├── README.md                     # 项目说明
├── ARCHIVE_NOTES.md              # 版本归档说明
└── requirements.txt              # Python依赖

```

---

## 文件命名规范

### Python源文件
- 使用小写字母和下划线（snake_case）
- 例如：`gasifier_main.py`, `reaction_rates.py`

### 文档文件
- 使用大写字母（SCREAMING_SNAKE_CASE）
- 例如：`README.md`, `ISSUE_REGISTRY.md`

### 数据文件
- 使用大写字母
- 例如：`START.DAT`, `Datain0.dat`

---

## 代码文件头规范

每个Python文件应包含以下标准文件头：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEXACO气化炉CFD模拟 - [模块名称]
对应Fortran: [Fortran文件名/子程序名]

功能说明:
    [简要描述模块功能]

作者: TEXACO Python移植项目
日期: 2026-03-20
版本: 1.0
"""

# 标准库导入
import os
import sys

# 第三方库导入
import numpy as np

# 项目内部导入
from common.common_data import common

# ... 代码主体 ...
```

---

## 模块职责

### common/common_data.py
- 定义全局数据结构（Common类）
- 存储仿真参数和状态变量
- 实现单例模式管理全局状态

### functions/
- **fh2o_fortran.py**: 水蒸气物性计算
- **gas_reactions.py**: 气体相反应速率计算
- **math_utils.py**: 数学工具（矩阵运算、求解器）
- **reaction_rates.py**: 反应速率计算（A1-A5）

### subroutines/
- **initialization.py**: 初始化所有变量（EINGAB）
- **gasifier_main.py**: 气化炉主计算循环（GASIFIER）
- **mass_flow.py**: 质量流和停留时间计算（XMASS）
- **output_results.py**: 结果输出（KOLERG）

---

## 数据文件说明

### START.DAT
初始条件文件，包含：
- 气体组分初始分布
- 固体质量流初始分布
- 温度初始分布
- 碳转化率初始分布

### Datain0.dat
计算参数文件，包含：
- 煤质参数（工业分析、元素分析）
- 操作条件（温度、压力、流量）
- 几何参数
- 收敛控制参数

---

## 输出文件

运行后生成的文件：
- **GASTEST.DAT**: 主输出文件，包含运行结果和收敛历史

---

## 版本控制

### 不应提交的文件
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
GASTEST.DAT
python_matrix_iter0.txt
```

### 必须提交的文件
```
所有源代码文件 (*.py)
所有文档文件 (*.md)
数据文件 (START.DAT, Datain0.dat)
配置文件 (requirements.txt)
```

---

*最后更新: 2026-03-20*
