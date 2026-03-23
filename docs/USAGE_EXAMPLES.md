# TEXACO Python版本 - 使用示例

本文档提供TEXACO气化炉模拟程序的常见使用场景和示例。

---

## 快速开始

### 1. 基础运行

```bash
cd python_final
python src/main.py
```

程序将读取默认的 `data/START.DAT` 和 `data/Datain0.dat`，输出结果到 `GASTEST.DAT`。

### 2. 指定不同输入文件

```bash
# 使用Case 1参数
cp data/Datain0_case1.dat data/Datain0.dat
python src/main.py

# 使用Case 2参数
cp data/Datain0_case2.dat data/Datain0.dat
python src/main.py
```

---

## 输入文件配置

### Datain0.dat 主要参数

```
&CONTRL
  MATER = 0.55          # 煤进料量 [kg/s]
  OXY = 0.46888         # 氧气进料量 [kg/s]
  YO2 = 0.95            # 氧气浓度
  H2OI = 0.14083        # 水蒸气进料量 [kg/s]
  P = 25.0              # 操作压力 [bar]
  TRCOAL = 300.0        # 煤入口温度 [K]
  TGO = 500.0           # 气体入口温度 [K]
/

&GEOM
  NMAX = 15             # 径向网格数
  NZ = 30               # 轴向网格数
  ZMAX = 15.0           # 反应器高度 [m]
  RMAX = 0.5            # 反应器半径 [m]
/

&CONVER
  MAXIT = 200           # 最大迭代次数
  EPS = 1.0E-4          # 收敛准则
/
```

### START.DAT 初始条件格式

```
变量标签行（27个变量名）
数据行（每行NZ个值，空格分隔）
```

---

## 输出结果解读

### GASTEST.DAT 输出示例

```
  输  出  打  印  ---  第  1  次

径向     高度[m]  温度[K]  CH4     CO      CO2     H2      H2O     N2      O2      气体质量流   固体质量流

 1        0.50     1873.2   0.052   0.458   0.085   0.289   0.058   0.042   0.016    2.45        0.85
 2        1.00     1789.5   0.048   0.462   0.089   0.295   0.052   0.041   0.013    2.52        0.82
...
```

### 收敛历史格式

```
迭代    SUMFE       SUMWE       SUMX        SUMT        状态
  1     1.234E-02   5.678E-03   2.345E-02   8.901E-03   未收敛
  2     9.876E-03   4.567E-03   1.987E-02   7.654E-03   未收敛
...
 62     3.456E-05   2.109E-05   4.321E-05   1.987E-05   收敛
```

收敛准则：
- `SUMFE` < 1.0E-4：气体组分收敛
- `SUMWE` < 1.0E-4：固体质量流收敛
- `SUMX` < 1.0E-4：碳转化率收敛
- `SUMT` < 1.0E-4：温度收敛

---

## 常见问题

### 问题1: 程序不收敛

**可能原因:**
1. 初始条件不合理
2. 网格划分过密或过疏
3. 松弛因子不合适

**解决方法:**
```python
# 检查松弛因子设置 (math_utils.py中的kolon1函数)
omega = 1.0  # 默认值，可适当减小（如0.8）以改善收敛
```

### 问题2: 结果与Fortran版本不一致

**检查清单:**
1. 确认使用的是相同版本的START.DAT和Datain0.dat
2. 检查Python和Fortran的浮点精度设置
3. 验证矩阵求解器参数（NSGP, NSGP1, NVWS等）

### 问题3: 内存错误

**原因:** 网格数过多导致数组过大

**解决方法:**
```
&GEOM
  NMAX = 10        # 减小径向网格数
  NZ = 20          # 减小轴向网格数
/
```

---

## 高级用法

### 参数敏感性分析

```python
import subprocess

# 批量运行不同煤进料量
for mater in [0.50, 0.55, 0.60, 0.65]:
    # 修改Datain0.dat中的MATER值
    modify_datain0(mater=mater)
    
    # 运行程序
    subprocess.run(['python', 'src/main.py'])
    
    # 保存结果
    copy_result(f'result_mater_{mater}.dat')
```

### 自定义输出

```python
from common.common_data import common
from subroutines.output_results import write_convergence

# 在特定迭代保存中间结果
if iteration % 10 == 0:
    write_convergence(iteration, common)
```

---

## 故障排除

### 运行时错误

| 错误信息 | 可能原因 | 解决方法 |
|---------|---------|---------|
| `IndexError: index out of bounds` | 数组索引越界 | 检查NZEL1/NZEL2设置 |
| `ValueError: math domain error` | 对数/平方根负数 | 检查输入数据的合理性 |
| `MemoryError` | 内存不足 | 减小网格数量 |
| `Convergence failed` | 不收敛 | 调整松弛因子或初始条件 |

### 调试模式

```python
# 在main.py中启用调试输出
DEBUG = True

if DEBUG:
    print(f"DMAT[1,1] = {common.DMAT[1,1]}")
    print(f"T[1] = {common.T[1]}")
```

---

## 联系与支持

如有问题，请参考：
- `docs/ISSUE_REGISTRY.md`: 已知问题列表
- `docs/TODO.md`: 开发计划和待办事项
- `ARCHIVE_NOTES.md`: 版本历史

---

*最后更新: 2026-03-20*
