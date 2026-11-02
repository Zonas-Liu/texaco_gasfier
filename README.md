# TEXACO / 晋华炉 3.0 气化炉模拟

Fortran 水煤浆气化炉程序的 Python 移植与晋华炉扩展，采用一维轴向控制体、气固反应及质量/能量平衡和块三对角牛顿求解器。该模型不解析三维流场。

## 分支与模型

- `main`：稳定主干；`texaco`：原 TEXACO 基准。
- `jinhualu`：膜式水冷壁燃烧室 + 辐射废锅开发分支。
- `KMODEL=0`：30 格原 TEXACO；`KMODEL=1`：30 格燃烧室加 1–30 格 RSC，数组尺寸 61，索引 0 闲置。

当前输入 `data/Datain0.dat` 采用 30 格 RSC、高度 30 m、直径 2.6 m、汽包压力 6.5 MPa、给水 423.15 K。TW_WALL=1773 K、TW_RSC=673 K 为有效表面温度，不是金属管壁温度。

2026-11-02独立[元素守恒实验](docs/ELEMENT_BALANCE_EXPERIMENT.md)发现：当前RSC源项与基础方程缩放不一致，典型工况燃烧室守恒、废锅C/H/O不守恒。候选修正已在隔离副本恢复闭合，本次尚未修改正式方程；现有废锅结果需要修正后重新验证，不能以数值收敛代替物理守恒检查。

## 安装与运行

需要 Python 3.10+。Windows 示例：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src/main.py
# 两种界面任选其一
.venv\Scripts\streamlit.exe run app.py
.venv\Scripts\python.exe web_backend/app.py
```

Streamlit 默认端口 8501，Flask 默认监听 `127.0.0.1:5000`。同一个项目目录仅运行一个计算任务，不要同时使用两个界面或多个 Web worker。

计算在工作目录写入 UTF-8 `GASTEST.DAT`、`START.DAT`、`simulation_progress.json` 和首次迭代矩阵。推荐从项目根目录运行。命令退出码：0=收敛且满足启用的设计目标，2=内层未收敛或目标温度未达到，其他非零=异常。未通过全部条件的输出仅供诊断。

`KTRL=1` 使用默认初值；`KTRL=0` 优先读取工作目录的 START.DAT，找不到时读取输入文件同目录的 START.DAT。重启文件必须与本次网格一致，支持 Fortran D 指数；无效文件会明确报错。

晋华炉默认通过 SciPy/LAPACK 求解带状线性系统，并复用局部物性；微量残碳使用相对差分步长，收敛阈值保持不变。更新后请重新安装 `requirements.txt`（新增 SciPy）。本机典型 60 格正算由约161秒降至约9秒；TEXACO 默认保留旧线性后端和逐位基准。方法、实际工况对比及复现命令见 [求解性能与稳定性](docs/SOLVER_PERFORMANCE.md)。

## 输入与单位

输入逐行读取，前 11 行为 TEXACO 参数；第 12–17 行为可选扩展。Web 的“燃烧室反算”和“辐射废锅设计”组可编辑扩展参数；Streamlit 编辑前 11 行并保留扩展行。Web 也会原样保留没有修改的可选行。

**界面输入统一为 MPaG、℃**，包括 Web 的汽包、给水、有效壁温；Streamlit 现有压力/温度控件同步转换。以 0.101325 MPa 为表压参考：`P_abs(Pa) = (P_g(MPaG) + 0.101325) × 10⁶`，`T(K) = t(℃) + 273.15`。下表为 **Datain0.dat 文件单位**，历史文件和 API 数值仍用绝压 Pa、K；API `info.display` 提供显示换算元数据。汽包物性范围对应 3.898675–9.898675 MPaG。

| 行 | 参数 |
|---|---|
| 12 | KMODEL, P_DRUM (Pa), T_FW (K) |
| 13 | TW_WALL (K), TW_RSC (K), D_RSC (m), H_RSC (m), N_RSC |
| 14 | KRELAX_WGS, KRELAX_METH |
| 15 | RSC_MODE, T_RSC_OUT_C (°C), H_RSC_MIN (m), H_RSC_MAX (m) |
| 16 | FEED_MODE, T_CHAMBER_C (℃), EFFECTIVE_GAS_NMH (Nm³/h) |
| 17 | FOXY_MIN, FOXY_MAX, SLURRY_MIN (kg/s), SLURRY_MAX (kg/s) |

第 15 行缺失时按固定高度计算（RSC_MODE=0），与原输入兼容。RSC_MODE=1 时给定出口温度，H_RSC 作为高度搜索初值，在 H_RSC_MIN–H_RSC_MAX 内迭代寻找有效高度。各候选都重新求解全炉，按 RSC 壁面吸热量和汽水焓差同步计算废锅产汽量；汽包压力、给水温度可在 Web 修改。默认目标 780℃、高度范围 1–120 m，温度允许偏差 ±0.5℃，最多 18 个候选。目标温度、高度和产汽量不是三个独立固定量。

合成气页并列展示燃烧室与辐射废锅出口的温度、干湿基组成和流量；总览提供目标温度、高度、热负荷、产汽量及设计迭代明细。目标未达到时不覆盖重启文件。方法、约束及验证见 [辐射废锅目标温度设计](docs/RSC_TARGET_DESIGN.md)。

在“燃烧室反算”中选择“温度＋有效气量反算”，输入燃烧室出口温度和 CO＋H₂ 的 Nm³/h。程序保持煤浆浓度、氧气纯度及其余工况，联动反算 FOXY（纯氧 / 无水无灰煤）与 BSLURRY（水煤浆总量 kg/s）。进料栏的对应数值作为搜索初值；结果在总览单独显示，不自动改写初值。默认搜索范围为氧煤比 0.7–1.3、煤浆 5–30 kg/s，均可调整。缺少第 16 行时保持给定进料正算（FEED_MODE=0）。

双目标允许偏差为温度 ±0.5℃、气量 ±0.1%（最小 ±1 Nm³/h）。反算先进行正常初始化，后续可复用本次已收敛状态；不读取历史 START 作为反算初值。可同时启用废锅目标温度模式，继续计算有效高度、热负荷和产汽量；只有全部启用目标通过才保存 START。算法、边界及验收见 [燃烧室双目标反算](docs/FEED_TARGET_DESIGN.md)。

两处合成气表均增加摩尔流量 kmol/h，并单列灰质量流量 kg/h。摩尔流量取 FEMF×3600；灰取 WE×(1−X)×3600，不包含未反应碳。新输出通过 `OUTLET_FLOWS_JSON` 保存精确截面数据；历史输出可用标准体积流量换算摩尔流量，缺失灰量显示“—”，需重新计算补全。

`BSLURRY` 是水煤浆总质量流量（kg/s）；`RATIO_COAL` 是煤的质量分数（0–1），干煤量为两者乘积。气体摩尔流量单位 kmol/s，标准体积沿用原程序 22.4 m³/kmol 近似。`X` 是固体碳质量分数，输出的碳转化率由它与固体流量换算。

气体编号：1 O₂、2 CH₄、3 CO、4 CO₂、5 H₂S、6 H₂、7 N₂、8 H₂O。ENTHP 返回 J/kmol 并包含生成焓；通过组分变化反映反应热，不另行叠加同一反应热。

## 代码导航

| 路径 | 职责 |
|---|---|
| `src/main.py` | 初始化、牛顿迭代、退出状态与进度 |
| `src/common/` | COMMON 单例、输入校验、进度及共享结果读取 |
| `src/subroutines/initialization.py` | EINGAB、几何、热校正及重启读取 |
| `src/subroutines/gasifier_main.py` | 守恒方程、壁面热汇、RSC 松弛反应及数值雅可比 |
| `src/functions/math_utils.py` | 块三对角求解与变量更新 |
| `src/subroutines/output_results.py` | 派生量刷新、结果、重启文件及平衡诊断 |
| `src/functions/steam_props.py` | 简化蒸汽物性与热回收产汽 |
| `src/functions/rsc_design.py` | 目标出口温度的有界高度搜索与设计状态 |
| `src/functions/feed_design.py` | 燃烧室温度与有效气量的双变量进料反算 |
| `app.py` | Streamlit 界面 |
| `web_backend/`、`web/` | Flask API、HTML/JS 界面 |
| `fortran_base/`、`numeric_test/` | 原始代码及数值对比资料、回归测试 |

## 验证及模型边界

```powershell
.venv\Scripts\python.exe -m unittest discover -s numeric_test -p "test_*.py" -v
```

审查发现、修复和本次数值复算记录见 [2026-11-02 审查报告](docs/CODE_REVIEW_2026-11-02.md)。历史 Python/Fortran 对比摘要在 `numeric_test/comparison_summary.txt`；不是本次重新编译 Fortran 的结果。

界面中传统称为“残差”的 SUMFE/SUMWE/SUMX/SUMT 是牛顿修正量绝对值和，收敛阈值取输入第 2 行。修正量收敛不等同于独立的元素、能量闭合验证。

RSC 的平衡常数近似、逐格松弛系数、有效壁温以及 4–10 MPa 蒸汽关联式均需工程标定。本仓库的数值回归不证明工业工况精度；目前不再宣称蒸汽关联式全范围误差小于 2%。其余 `docs/code_reference` 与旧 TODO 为历史移植参考，当前结构与行为以代码、AGENTS.md 和最新审查报告为准。

MIT 许可证，见 LICENSE。
