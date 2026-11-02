# 项目文档总索引

这里区分**当前说明**、**有明确版本的验收记录**和**历史移植资料**。当前详细说明以[代码与数学物理手册](code_reference/README.md)为入口。文档描述实际实现；已知近似或疑点不会因写入文档而变成已验证的物理结论。

## 当前说明

| 文档 | 内容 |
|---|---|
| [代码与数学物理手册，10章](code_reference/README.md) | 状态/变量、完整守恒方程、动力学、热力学、数值算法、输入输出、API、验证、源码符号 |
| [项目结构与维护边界](PROJECT_STRUCTURE.md) | 目录、模块层次、数据/生成物、依赖、扩展位置 |
| [可复现运行示例](USAGE_EXAMPLES.md) | 安装、隔离正算/反算、API、结果读取、验收命令 |
| [物理常数及物性来源](PHYSICAL_CONSTANTS.md) | CIAAW/CODATA/IAPWS权威出处、精度、兼容配置和未更换的拟合系数 |
| [现行问题登记](ISSUE_REGISTRY.md) | 当前未解决项、影响与可执行的验收条件 |
| [后续工作](TODO.md) | 按依赖关系安排能量审计、网格/闭合、服务和可维护性工作 |
| [Web工艺工作台设计](UI_REDESIGN_2026-11-02.md) | 当前视觉体系、工艺示意、响应式布局、数据来源和验收边界 |
| [图表与数据表细节](UI_DATA_PRESENTATION.md) | 双出口矩阵、干湿基图表、数值精度、单位切换、CSV与浏览器验收 |
| [仓库协作约定](../AGENTS.md) | 分支、实现约束、测试与文档更新要求 |

## 功能与验收记录

这些文件记录特定变更及当时的计算。若后续物理修复改变数值，引用结果时应同时注明版本；最新元素/物性验收优先于早期温度和产汽基准。

| 文档 | 用途/版本边界 |
|---|---|
| [元素守恒修复及验收](ELEMENT_BALANCE_FIX.md) | 当前模型基线；修复RSC缩放、统一常数与IF97后的真实求解结果 |
| [修复后精简JSON证据](element_balance_fixed_results.json) | 原始精度账项、源码哈希、工况摘要 |
| [原元素守恒实验](ELEMENT_BALANCE_EXPERIMENT.md) | 修复前缺口及定位证据，保留供追溯 |
| [修复前实验JSON](element_balance_results.json) | 历史状态数据，不代表当前缺陷仍存在 |
| [求解器性能](SOLVER_PERFORMANCE.md) | LAPACK、差分/缓存优化及当时基准；当前性能需本机复测 |
| [燃烧室双目标反算](FEED_TARGET_DESIGN.md) | 目标定义、搜索边界、组合设计、当时验收 |
| [废锅目标温度模式](RSC_TARGET_DESIGN.md) | 高度/热负荷/产汽联动、外层搜索和失败语义 |
| [初版Web设计记录](UI_DESIGN.md) | 初版设计规格、交互状态和当次浏览器验收 |
| [2026-11-02代码审查](CODE_REVIEW_2026-11-02.md) | 早期审查修复记录，需结合后续功能和物性更新阅读 |

## 历史材料与维护

[归档说明](archive/README.md)保留旧TODO、旧问题登记与旧手册Git版本入口。历史材料不再混入现行问题清单；不会因归档而声称其未解决问题都已修复。

运行`.venv\Scripts\python.exe scripts/check_docs.py`检查维护范围内本地链接、源码行号、围栏、输入参数行序及符号索引新鲜度。`--write-index`只更新第10章；公式和物理结论需要人工审读。具体维护要求见[第9章](code_reference/09_VALIDATION_AND_LIMITATIONS.md)。
