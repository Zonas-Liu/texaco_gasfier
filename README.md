# TEXACO / 晋华炉 3.0 气化炉模拟

Fortran 水煤浆气化炉程序的 Python 移植与晋华炉扩展，采用一维轴向控制体、气固反应及质量/能量平衡和块三对角牛顿求解器。该模型不解析三维流场。

## 分支与模型

- `main`：稳定主干；`texaco`：原 TEXACO 基准。
- `jinhualu`：膜式水冷壁燃烧室 + 辐射废锅开发分支。
- `KMODEL=0`：30 格原 TEXACO；`KMODEL=1`：30 格燃烧室加 1–30 格 RSC，数组尺寸 61，索引 0 闲置。

当前输入 `data/Datain0.dat` 采用 30 格 RSC、高度 30 m、直径 2.6 m、汽包压力 6.5 MPa、给水 423.15 K。TW_WALL=1773 K、TW_RSC=673 K 为有效表面温度，不是金属管壁温度。

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

计算在工作目录写入 UTF-8 `GASTEST.DAT`、`START.DAT`、`simulation_progress.json` 和首次迭代矩阵。推荐从项目根目录运行。命令退出码：0=收敛，2=迭代上限未收敛，其他非零=异常。未收敛输出仅供诊断。

`KTRL=1` 使用默认初值；`KTRL=0` 优先读取工作目录的 START.DAT，找不到时读取输入文件同目录的 START.DAT。重启文件必须与本次网格一致，支持 Fortran D 指数；无效文件会明确报错。

## 输入与单位

输入逐行读取，前 11 行为 TEXACO 参数；第 12–14 行为可选扩展。两套界面当前编辑前 11 行，保留末尾扩展行；晋华炉参数需要编辑数据文件。

| 行 | 参数 |
|---|---|
| 12 | KMODEL, P_DRUM (Pa), T_FW (K) |
| 13 | TW_WALL (K), TW_RSC (K), D_RSC (m), H_RSC (m), N_RSC |
| 14 | KRELAX_WGS, KRELAX_METH |

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
| `app.py` | Streamlit 界面 |
| `web_backend/`、`web/` | Flask API、HTML/JS 界面 |
| `fortran_base/`、`numeric_test/` | 原始代码及数值对比资料、回归测试 |

## 验证及模型边界

```powershell
.venv\Scripts\python.exe -m unittest discover -s numeric_test -p test_review.py -v
```

审查发现、修复和本次数值复算记录见 [2026-11-02 审查报告](docs/CODE_REVIEW_2026-11-02.md)。历史 Python/Fortran 对比摘要在 `numeric_test/comparison_summary.txt`；不是本次重新编译 Fortran 的结果。

界面中传统称为“残差”的 SUMFE/SUMWE/SUMX/SUMT 是牛顿修正量绝对值和，收敛阈值取输入第 2 行。修正量收敛不等同于独立的元素、能量闭合验证。

RSC 的平衡常数近似、逐格松弛系数、有效壁温以及 4–10 MPa 蒸汽关联式均需工程标定。本仓库的数值回归不证明工业工况精度；目前不再宣称蒸汽关联式全范围误差小于 2%。其余 `docs/code_reference` 与旧 TODO 为历史移植参考，当前结构与行为以代码、AGENTS.md 和最新审查报告为准。

MIT 许可证，见 LICENSE。
