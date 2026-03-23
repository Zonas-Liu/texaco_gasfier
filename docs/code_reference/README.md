# TEXACO Python版本 - 代码详细文档

本文档集合提供了TEXACO气化炉CFD模拟程序的完整技术参考。

---

## 文档列表

### 1. [模块划分与架构概述](./01_MODULE_OVERVIEW.md)

**内容**:
- 程序总体架构图
- 各模块详细说明
- 函数输入输出列表
- 变量索引说明
- 程序执行流程图

**适用读者**: 项目架构师、技术负责人

---

### 2. [函数调用关系与代码架构](./02_CALL_HIERARCHY.md)

**内容**:
- 完整的函数调用层次图
- Python与Fortran代码对照
- 详细的代码块示例
- 调用关系总图

**适用读者**: 开发人员、代码审查者

**包含代码对照**:
- `main()` - 主程序
- `eingab()` - 初始化
- `geometry()` - 几何计算
- `gasifier()` - 气化炉主计算
- `xk1()-xk6()` - 气相反应
- `flucht()` - 挥发分释放
- `A1()-A5()` - 碳反应速率
- `blktrd()` - 块三对角求解

---

### 3. [数学物理模型详解](./03_MATHEMATICAL_MODELS.md)

**内容**:
- 质量平衡方程（气体组分、固体）
- 能量平衡方程
- 气相反应动力学（XK1-XK6）
- 异相反应动力学（A1-A5）
- 扩散与传质模型（Wen模型）
- 热力学性质计算

**适用读者**: 研究人员、算法工程师

**包含公式**:
- 所有平衡方程的数学表达式
- 反应速率方程
- 扩散系数计算
- 热容积分公式

---

### 4. [API函数参考手册](./04_API_REFERENCE.md)

**内容**:
- 所有函数的完整API文档
- 参数类型和说明
- 返回值说明
- 调用示例
- 常量参考表

**适用读者**: 应用开发者、测试工程师

**包含API**:
- 主程序模块 (main.py)
- 全局数据模块 (common_data.py)
- 初始化模块 (initialization.py)
- 气化炉主模块 (gasifier_main.py)
- 质量流模块 (mass_flow.py)
- 气相反应模块 (gas_reactions.py)
- 反应速率模块 (reaction_rates.py)
- 数学工具模块 (math_utils.py)

---

## 快速导航

### 按主题查找

| 主题 | 推荐文档 |
|------|----------|
| 想了解程序整体结构 | [01_MODULE_OVERVIEW.md](./01_MODULE_OVERVIEW.md) |
| 想理解函数调用关系 | [02_CALL_HIERARCHY.md](./02_CALL_HIERARCHY.md) |
| 想查看数学方程 | [03_MATHEMATICAL_MODELS.md](./03_MATHEMATICAL_MODELS.md) |
| 想查阅函数API | [04_API_REFERENCE.md](./04_API_REFERENCE.md) |

### 按角色查找

| 角色 | 推荐文档 |
|------|----------|
| 项目经理/架构师 | [01_MODULE_OVERVIEW.md](./01_MODULE_OVERVIEW.md) |
| 开发人员 | [02_CALL_HIERARCHY.md](./02_CALL_HIERARCHY.md) |
| 研究人员 | [03_MATHEMATICAL_MODELS.md](./03_MATHEMATICAL_MODELS.md) |
| 测试/应用工程师 | [04_API_REFERENCE.md](./04_API_REFERENCE.md) |

---

## 文档使用建议

### 初次接触项目

1. 先阅读 [01_MODULE_OVERVIEW.md](./01_MODULE_OVERVIEW.md) 了解整体架构
2. 查看 [02_CALL_HIERARCHY.md](./02_CALL_HIERARCHY.md) 的主程序调用层次
3. 根据需要深入查看具体模块

### 进行代码开发

1. 使用 [04_API_REFERENCE.md](./04_API_REFERENCE.md) 查找函数API
2. 参考 [02_CALL_HIERARCHY.md](./02_CALL_HIERARCHY.md) 了解调用关系
3. 查看 [03_MATHEMATICAL_MODELS.md](./03_MATHEMATICAL_MODELS.md) 理解数学原理

### 进行模型研究

1. 重点阅读 [03_MATHEMATICAL_MODELS.md](./03_MATHEMATICAL_MODELS.md)
2. 对比Fortran代码理解实现细节
3. 参考 [02_CALL_HIERARCHY.md](./02_CALL_HIERARCHY.md) 查看代码对照

---

## 相关文档

- [项目README](../README.md) - 项目总体介绍
- [问题登记册](../ISSUE_REGISTRY.md) - 已知问题跟踪
- [项目结构说明](../PROJECT_STRUCTURE.md) - 目录结构规范
- [使用示例](../USAGE_EXAMPLES.md) - 使用指南

---

## 文档维护

- **创建日期**: 2026-03-20
- **最后更新**: 2026-03-20
- **版本**: v1.0
- **维护者**: TEXACO Python移植项目组

---

## 反馈与建议

如发现文档错误或有改进建议，请：
1. 在ISSUE_REGISTRY.md中登记
2. 或直接联系项目维护者

---

*本文档遵循MIT许可证*
