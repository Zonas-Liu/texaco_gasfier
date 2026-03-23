# TEXACO Python 版本项目 TODO 文档

**创建日期**: 2026-03-20  
**最后更新**: 2026-03-20  
**项目版本**: v1.0 Final+

---

## 📋 项目概述

本文档总结 TEXACO 气化炉 CFD 模拟程序 Python 移植项目的当前进度、关键成就和下一步工作计划。

### 项目背景
- **原始代码**: Fortran 77 固定格式代码 (Wg1-Wg9.for)
- **目标代码**: Python 3 实现，保持数值计算精度
- **验证标准**: 与 Fortran 版本的矩阵组装精度 >99%，收敛行为一致

---

## ✅ 已完成工作

### 1. 核心功能移植
| 模块 | Fortran 文件 | Python 模块 | 状态 |
|------|-------------|------------|------|
| 主程序 | Wg1.for | main.py | ✅ 完成 |
| 初始化 | Wg2.for | initialization.py | ✅ 完成 |
| 气化炉计算 | Wg3.for | gasifier_main.py | ✅ 完成 |
| 气相反应 | Wg6.for | gas_reactions.py | ✅ 完成 |
| 反应速率 | Wg7.for | reaction_rates.py | ✅ 完成 |
| 结果输出 | Wg8.for | output_results.py | ✅ 完成 |
| 求解器 | Wg9.for | math_utils.py | ✅ 完成 |

### 2. 关键问题修复 (基于 ISSUE_REGISTRY.md)

#### 已修复问题 (22/29)
| 问题ID | 描述 | 严重程度 | 修复内容 |
|--------|------|---------|---------|
| ISS-001 | START.DAT 文件格式问题 | 🔴 Critical | 修复多值行读取逻辑 |
| ISS-002 | 模块导入路径不一致 | 🔴 Critical | 统一使用相对路径导入 |
| ISS-003 | DMAT 符号错误 | 🔴 Critical | 恢复 DMAT 取负操作 |
| ISS-004 | 数值微分 XMS 副作用 | 🔴 Critical | 添加状态保存/恢复机制 |
| ISS-006 | matmult 索引错误 | 🔴 Critical | 修复向量/矩阵判断和索引 |
| ISS-007 | matdiv 标量情况越界 | 🟠 High | 修复向量形状处理 |
| ISS-008 | blktrd 缺少返回值 | 🟡 Medium | 添加 return 语句 |
| ISS-009 | Fortran 收敛测试版本编译 | 🟡 Medium | 修复字符串长度和子程序问题 |
| ISS-013 | Fortran FEMF 数组越界 Bug | 🔴 Critical | 添加边界检查保护 |
| ISS-015 | Python 残差计算索引错误 | 🔴 Critical | 修复 range(1, NVE+1) 索引 |
| ISS-016 | KOLON1 温度方程索引错误 | 🔴 Critical | 使用 NVWS 替代 ng2 |
| ISS-017 | 数组索引 0-based 转换 | 🔴 Critical | 修正 NZRA/NZRE 等索引变量 |
| ISS-018 | 矩阵组装差异 | 🔴 Critical | 修复 A1/A3 反应速率调用顺序 |
| ISS-020 | DMAT[1,1] 反应项差异 | 🔴 Critical | 修复数值微分循环边界 |
| ISS-021 | FEMF 初始化分母错误 | 🔴 Critical | 修复 nzed 计算逻辑 |
| ISS-022 | Cell 1 能量方程不匹配 | 🔴 Critical | 完整移植 FH2O 水蒸气表函数 |
| ISS-023 | DMAT 符号约定差异 | 🟡 Info | 确认为设计等效，非问题 |
| ISS-024 | AMAT CO2 对角元素不匹配 | 🔴 Critical | 删除显式对角覆盖 |
| ISS-025 | XMASS/TRZ 计算差异 | 🔴 Critical | 修复 NZR7 值 (4→5) |
| ISS-026 | NZR1-NZR6 几何参数错误 | 🔴 Critical | 全部 NZR 参数修复 |
| ISS-028 | Fortran 收敛历史输出 | 🟢 Feature | 添加残差历史记录功能 |
| ISS-029 | Python 残差计算与松弛因子 | 🔴 Critical | 修复 omega=1.0, 索引修正 |

### 3. 当前矩阵组装精度 (Case 1)
| 矩阵 | 匹配率 | 最大相对误差 | 状态 |
|------|--------|-------------|------|
| DMAT | 99.98% | 1.76e-05 | ✅ 优秀 |
| BMAT | 99.26% | - | ✅ 优秀 |
| AMAT | 90.91% | - | ⚠️ 可接受 |
| CMAT | 100% | - | ✅ 完全匹配 |

### 4. 收敛验证结果
| 案例 | Fortran 迭代 | Python 迭代 | 结果 |
|------|-------------|-------------|------|
| Case 1 | 64 | 64 | ✅ 匹配 |
| Case 2 | 62 | 62 | ✅ 匹配 |

**残差对比 (最终迭代)**:
- SUMFE: Fortran 3.16e-6 vs Python 3.16e-6 ✅
- SUMWE: Fortran 4.06e-6 vs Python 4.06e-6 ✅
- SUMX: Fortran 2.87e-6 vs Python 2.87e-6 ✅
- SUMT: Fortran 2.85e-2 vs Python 2.85e-2 ✅

---

## 🔄 进行中工作

### ISS-027: 整体收敛迭代测试
**状态**: 🔄 进行中  
**目标**: 验证修复后 Python 版本的完整收敛行为

**已完成**:
- [x] 矩阵组装精度验证 (99.98%)
- [x] Case 1 收敛测试 (64 次迭代)
- [x] Case 2 收敛测试 (62 次迭代)
- [x] GASTEST.DAT 出口参数对比 (<0.2% 误差)

**待完成**:
- [ ] 长周期稳定性测试 (300+ 迭代)
- [ ] 不同初始猜测的鲁棒性测试
- [ ] 边界条件变化测试

---

## 📊 GitHub 仓库状态

### 本地提交已完成
- **提交 1**: `2646199` - 初始代码导入
- **提交 2**: `729bf1e` - 最终版本整合

### 待完成
- [ ] 解决 GitHub 认证问题 (SSH/PAT)
- [ ] 推送本地提交到 origin/main
- [ ] 验证远程仓库完整性

**认证问题详情**:
- HTTPS 连接超时 (60s+)
- SSH 密钥已生成 (`C:\Users\ADMIN\.ssh\id_rsa.pub`)
- 需要在 https://github.com/settings/keys 添加 SSH 密钥
- 或使用 TortoiseGit + Personal Access Token (PAT)

---

## 📝 下一步工作计划

### 高优先级

#### 1. GitHub 仓库同步
| 任务 | 预计时间 | 依赖 |
|------|---------|------|
| 添加 SSH 密钥到 GitHub 账户 | 10 分钟 | 需要 GitHub 登录 |
| 或使用 TortoiseGit PAT 认证 | 20 分钟 | 需要生成 PAT |
| 推送本地提交到远程 | 5 分钟 | 认证完成后 |
| 验证远程仓库文件完整性 | 10 分钟 | 推送完成后 |

#### 2. 文档归档
| 任务 | 说明 |
|------|------|
| 归档 E:\Texco\docs\code_reference\ | 内容已整合到 README.md |
| 更新 AGENTS.md (如需要) | 记录项目结构变化 |
| 清理临时调试文件 | 保留关键调试脚本 |

### 中优先级

#### 3. 代码优化
| 优化项 | 说明 | 预期收益 |
|--------|------|---------|
| Numba JIT 加速 | 关键循环加速 | 5-10x 性能提升 |
| 并行计算支持 | 多线程/多进程 | 利用多核 CPU |
| 内存使用优化 | 减少大型数组拷贝 | 降低内存占用 |

#### 4. 功能扩展
| 功能 | 说明 | 优先级 |
|------|------|--------|
| 图形化输出 | Matplotlib 可视化 | 中 |
| 参数扫描工具 | 批量运行不同参数 | 中 |
| 收敛诊断工具 | 自动分析不收敛原因 | 高 |

### 低优先级

#### 5. 长期维护
| 任务 | 说明 |
|------|------|
| 建立 CI/CD 流程 | GitHub Actions 自动化测试 |
| 代码覆盖率测试 | pytest-cov 集成 |
| 性能基准测试 | 追踪版本性能变化 |

---

## 🐛 已知限制

### 当前版本限制
1. **收敛阈值**: 原始阈值 (5.0e-4) 对某些案例过于严格
   - 建议放宽至 1.0e-3 或调整松弛因子 omega
   
2. **CMAT 矩阵**: 上对角块在两种实现中都为 0
   - 这是原始 Fortran 代码的设计，非移植错误
   
3. **Cell 1 边界处理**: Fortran 存在数组越界访问
   - Python 版本已正确实现边界保护

### 数值精度说明
- 气体组分方程: 相对误差 < 0.1% ✅
- 能量方程: 相对误差 < 15% (主要来自 Cell 1 差异)
- 固体方程: 完全匹配 ✅

---

## 📁 关键文件位置

### 工作目录
```
E:\Texco\                       # 原始项目位置
├── python_test\                # 当前测试分支
│   ├── src\                    # Python 源代码
│   │   ├── main.py             # 主程序入口
│   │   ├── subroutines\        # 子程序模块
│   │   └── functions\          # 函数模块
│   ├── data\                   # 输入数据文件
│   └── docs\                   # 项目文档
├── fortran_test\               # Fortran 测试分支
│   ├── Wg1-Wg9.for             # Fortran 源码
│   └── texaco_test.exe         # 可执行文件
├── docs\                       # 文档目录
│   ├── ISSUE_REGISTRY.md       # 问题登记册 (29 个 Issue)
│   └── code_reference\         # 代码参考文档
└── final_version\              # 最终版本 (GitHub 镜像)
```

### GitHub 仓库
```
E:\self-proj\texaco_gasifier\   # GitHub 本地镜像
├── src\                        # Python 源代码
├── docs\                       # 整合文档
├── README.md                   # 超级文档 (21.6 KB)
└── .git\                       # Git 版本控制
```

---

## 🔍 参考文档

### 技术文档
| 文档 | 位置 | 说明 |
|------|------|------|
| ISSUE_REGISTRY.md | `E:\Texco\docs\` | 29 个开发问题的完整记录 |
| STAGE2_DEBUG_REPORT.md | `E:\Texco\` | Stage 2 调试报告 |
| CELL1_FIX_GUIDE.md | `E:\Texco\` | Cell 1 修复指南 |

### 代码文档 (已整合到 README.md)
- 01_MODULE_OVERVIEW.md
- 02_CALL_HIERARCHY.md
- 03_MATHEMATICAL_MODELS.md
- 04_API_REFERENCE.md

---

## 💡 关键经验总结

### 翻译最佳实践
1. **索引转换**: Fortran 1-based → Python 0-based 需要仔细处理边界条件
2. **数组维度**: Fortran 列优先 vs Python 行优先影响矩阵运算
3. **全局状态**: COMMON 块 → Python 单例模式需保持状态一致
4. **数值精度**: 使用 numpy.float64 确保双精度计算

### 调试方法论
1. **矩阵对比**: 输出完整 330×330 矩阵进行元素级对比
2. **中间变量**: 在关键计算点打印中间结果
3. **逐步验证**: 从初始化 → 矩阵组装 → 求解 → 更新逐步验证
4. **边界条件**: 特别注意 Cell 1 (NZRA) 和挥发分释放区边界

---

## 📅 时间线

| 日期 | 里程碑 |
|------|--------|
| 2026-03-17 | 项目开始，核心功能移植 |
| 2026-03-18 | 矩阵求解器修复，收敛性验证开始 |
| 2026-03-19 | 发现 Fortran 数组越界 Bug，修复关键索引错误 |
| 2026-03-20 | ISS-029 修复完成，收敛验证通过 |
| 待完成 | GitHub 推送，文档归档 |

---

## 📞 联系信息

如需进一步信息，请参考：
- 详细问题记录: `E:\Texco\docs\ISSUE_REGISTRY.md`
- 调试报告: `E:\Texco\STAGE2_DEBUG_REPORT.md`
- 完整技术文档: `E:\self-proj\texaco_gasifier\README.md`

---

*文档生成时间: 2026-03-20*  
*版本: v1.0 Final+*
