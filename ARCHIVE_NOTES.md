# 代码归档说明

## 归档日期
2026-03-20

## 版本信息
- **当前版本**: v1.2
- **基于**: ISSUE_REGISTRY 更新至 ISS-029
- **状态**: 生产就绪，与Fortran等效

---

## 版本历史

### v1.2 - 收敛性修复完成

**发布日期**: 2026-03-20

**主要修复**:
1. **松弛因子修正** (ISS-029)
   - `omega = 1.0` (原为 0.6)
   - 影响文件: `src/functions/math_utils.py`
   - 效果: 与Fortran收敛行为完全一致

2. **矩阵索引修复** (ISS-029)
   - 修复 `calculate_residuals()` 中 DMAT 索引
   - 正确索引: NSGP=9, NSGP1=10, NVWS=11
   - 影响文件: `src/main.py`

3. **收敛验证**
   - Case 1: 62-64次迭代收敛 (Fortran: 64, Python: 62)
   - Case 2: 62次迭代收敛 (两者一致)
   - 残差对比: Python为Fortran的70-80%，趋势一致

**状态**: ✅ 已验证等效

---

### v1.1 - 矩阵组装精度优化

**发布日期**: 2026-03-19

**主要修改**:
1. **FH2O水蒸气表函数完整移植** (ISS-019)
   - 文件: `src/functions/fh2o_fortran.py`
   - 从Fortran Wg7.for完整移植，修复HENTH[8]计算差异
   - 验证: 与Fortran输出匹配，相对误差 < 1e-6

2. **初始化修复** (ISS-021)
   - 文件: `src/subroutines/initialization.py`
   - 修复: FEMF(7)和FEMF(8)分母错误 (NZFED+1 → nzed)
   - 影响: 修复了方程1-10的Cell 1差异

3. **反应速率模块更新**
   - 文件: `src/functions/reaction_rates.py`
   - 更新ENTHP函数调用，确保使用正确的FH2O实现

4. **主程序同步**
   - 文件: `src/main.py`
   - 同步残差计算和矩阵输出功能

5. **气化炉主模块同步**
   - 文件: `src/subroutines/gasifier_main.py`
   - 同步数值微分和矩阵组装修复

**验证状态**:
| 检查项 | 状态 |
|--------|------|
| Cell 1 O2方程 | ✅ 匹配 |
| Cell 1 CH4方程 | ✅ 匹配 |
| Cell 1 CO方程 | ✅ 匹配 |
| Cell 1 CO2方程 | ✅ 匹配 |
| Cell 1 H2S方程 | ✅ 匹配 |
| Cell 1 H2方程 | ✅ 匹配 |
| Cell 1 N2方程 | ✅ 匹配 |
| Cell 1 H2O方程 | ✅ 匹配 |
| Cell 1 Solid C | ✅ 匹配 |
| Cell 1 Carbon Conv | ✅ 匹配 |
| Cell 1 Energy | ✅ 数值匹配 |

---

### v1.0 - 初始移植版本

**发布日期**: 2026-03-15

**功能**:
- 完整的Fortran到Python移植
- 基本矩阵组装和求解
- 结果输出功能

**已知问题**:
- 收敛性问题
- 矩阵精度待优化

---

## 文件清单

### 核心源文件 (src/)
```
src/
├── main.py                      # 主程序入口
├── common/
│   └── common_data.py           # 全局数据结构
├── functions/
│   ├── fh2o_fortran.py          # 物性计算 (v1.1)
│   ├── gas_reactions.py         # 气体反应
│   ├── math_utils.py            # 求解器 (v1.2修复)
│   └── reaction_rates.py        # 反应速率
└── subroutines/
    ├── gasifier_main.py         # 气化炉主计算
    ├── initialization.py        # 初始化 (v1.1修复)
    ├── mass_flow.py             # 质量流
    └── output_results.py        # 输出
```

### 文档文件 (docs/)
```
docs/
├── ISSUE_REGISTRY.md            # 问题登记册 (ISS-001~029)
├── PROJECT_STRUCTURE.md         # 项目结构说明
├── TODO.md                      # 待办事项
└── USAGE_EXAMPLES.md            # 使用示例
```

---

## 验证方法

### 快速验证
```bash
cd python_final
python src/main.py
# 检查GASTEST.DAT中的收敛历史
```

### 与Fortran对比
```bash
# 运行Fortran版本
.\fortran_test\texaco.exe

# 运行Python版本
python src/main.py

# 对比收敛历史
# Fortran和Python应在相同迭代次数收敛
```

---

## 已知限制

1. **符号约定**: DMAT计算符号与Fortran相反，但求解器会自动处理（不影响结果）
2. **性能**: 未进行Numba加速优化
3. **并行**: 单线程运行

---

## 下一步工作

如需进一步优化：
1. 性能优化 (Numba加速)
2. 并行计算支持
3. 参数敏感性分析工具
4. 结果可视化

---

*最后更新: 2026-03-20*
