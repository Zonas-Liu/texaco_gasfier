# 求解性能与稳定性优化（2026-11-02）

对照版本：`3fadb108a590db6ea78772219f034790609b3909`。本次优化保留物理方程、反应热口径、网格、默认初值、牛顿更新限幅及全部 SKON 收敛阈值。晋华炉采用 SciPy/LAPACK 带状线性求解、局部物性复用和微量残碳相对差分；原 TEXACO 默认保留旧线性求解及固定差分，以支持逐位对照。

后续[元素守恒实验](ELEMENT_BALANCE_EXPERIMENT.md)确认原RSC方程存在源项缩放不一致，优化前后均保留了该问题。本文的速度、收敛和兼容性验收不代表元素守恒或物理正确性验收；废锅结果须在正式修正后重验。

## 为什么没有直接换成一个通用非线性优化器

对原版典型 60 格的一次迭代做 cProfile：约3.75秒（含分析器开销），约689万次调用。ENTKOL 累计约3.06秒，占82%；BLKTRD 约0.064秒，占2%。1380次单格方程评估中，每次都调用全炉焓、停留时间及进料焓计算；ENTHP 共调用约167万次。只替换线性求解器不能消除主要耗时。

选用公开维护的 [SciPy 项目](https://github.com/scipy/scipy) 的 [`scipy.linalg.solve_banded`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html)。它直接求解带状 Ax=b，适合现有块三对角雅可比。没有改成 [`least_squares`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)：该接口求残差平方和的最小值，停止条件不能直接等同于本项目的炉内收敛条件；本次实际瓶颈也首先在重复组装。

## 实现

1. **局部物性和缓存**：ENTKOL 按 `(T, PWK)` 缓存全部十种组分焓和温度导数，缓存仅在一次 GASIFIER 调用中有效；不跨候选或跨运行复用。当前方程只需要本格、上游格的物性，XMASS/ENTKOL 因此只更新这两个格子。XMASS 保持上游到下游顺序及有效的上游 ROS。ENTFED 每次组装只计算一次。全炉速度和状态恢复改为 NumPy 数组操作。
2. **开源线性后端**：11×11 块组成的全系统直接存为带状格式，半带宽 `2*nmat-1`；不构造生产用的稠密全矩阵。能量方程和组分方程的数量级悬殊，求解前按每行最大系数缩放。A/B/C 不被修改，解写回 DMAT。非有限数和奇异矩阵明确失败。
3. **微量残碳导数**：晋华炉 X 列使用 `max(1e-12, min(1e-4, abs(X)*0.01))`，其余变量仍为1e-4。X 是固体碳质量分数；当其远小于1e-4时，原固定扰动不能代表当前点附近的反应核斜率，会出现接近收敛的周期振荡。相对步长修复该数值问题，没有修改反应速率公式。
4. **兼容路径**：KMODEL=0 默认仍用 BLKTRD 和1e-4差分。`TEXACO_LINEAR_SOLVER=legacy` 可为晋华炉指定旧线性后端进行诊断；这只替换线性后端，不关闭局部物性和残碳相对差分。`scipy` 可显式选新后端；其他值报错。

输出前仍通过 KOLERG 全炉刷新派生量。`SUMFE/SUMWE/SUMX/SUMT` 仍为牛顿修正量绝对值和，不能将其解释成原始守恒残差。本次不以放宽阈值、提高最大迭代次数或复用根目录 START 获得速度提升。

## 同机实际工况

Windows，Python 3.14.0，NumPy 2.4.6，SciPy 1.18.1。每个案例在独立子进程/目录启动，KTRL=1；包含求解、首次 SciPy 导入及原有文件输出，不含子进程启动前的模块导入。联合设计包含全部内外层试算。下表为单次墙钟时间，系统负载会影响计时，作为本机实际收益参考。

| 案例 | 优化前 | 优化后 | 迭代/结果 |
|---|---:|---:|---|
| 晋华炉典型60格，固定高度/进料 | 161.21 s | 9.07 s | 均63次收敛，约17.8倍 |
| TEXACO 30格，QLOSS=0.03 | 45.98 s | 5.69 s | 均62次收敛，约8.1倍 |
| FOXY=1.04、BSLURRY=12 kg/s | 259.89 s | 9.43 s | 原100次失败；现66次收敛 |
| 双目标1228℃/52000 Nm³/h＋废锅780℃ | 251.56 s | 13.65 s | 内层累计97→95次；全部目标通过，约18.4倍 |
| 固定FOXY=0.9715、BSLURRY=11.942 kg/s | 本轮未重新计旧版 | 9.13 s | 64次收敛 |

典型工况新旧全炉温度最大差0.000150 K，气体摩尔流量最大差5.30e-8 kmol/s；最终出口温度756.86224105→756.86224115℃。相对差分改变了末段迭代轨迹，因此晋华炉不再声称逐位一致。TEXACO 的 T/FEMF/WE/X/QKW 数组逐位一致，START 文件字节一致。

高氧工况原 SUMT 在约0.01154 K振荡，仍大于0.005 K判据；新结果 SUMT=3.13e-6 K。不是把旧失败结果当成功基准比较。联合设计新旧全炉温度最大差0.000465 K；最终温度与有效气量仍逐项按原容差验收。

同一实际初始雅可比，预热后20次线性求解中位数：BLKTRD 49.47 ms，SciPy带状求解（含存储转换和行缩放）1.28 ms，约38.6倍。以原矩阵检查 `max(|Ax-b|/(|A||x|+|b|))`，两者分别为1.34e-10和2.83e-14。行缩放改善了不同单位量级下的线性精度。

## 验收和复现

36项 unittest 通过。新增测试覆盖60格/11方程、10方程、单块、非零上下对角、跨块主元、奇异/NaN拒绝、相差24个数量级的方程行、不同温压下的水/固体焓缓存，以及非均匀温度/微量残碳下局部组装对全炉重算的矩阵逐位一致性。

实际模型验收还覆盖：基准反算、联合设计、ITMAX=1失败、废锅401℃/高度上限120 m不可达；失败设计保留既有START。此前的高氧初值反算和1200℃/42000 Nm³/h低负荷反算均完成并通过目标容差；单格RSC和OX_PART=0.9二次供氧亦收敛。它们是已检查的案例，不代表全操作范围均可解或物理模型已获独立验证。

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s numeric_test -p "test_*.py"
.venv\Scripts\python.exe numeric_test/benchmark_solver.py --output numeric_test/python_output/performance/reproduce
.venv\Scripts\python.exe numeric_test/benchmark_solver.py --linear-only --output numeric_test/python_output/performance/reproduce
.venv\Scripts\python.exe numeric_test/check_feed_design.py --output numeric_test/python_output/performance/reproduce-feed
```

`benchmark_solver.py --source <包含src的版本目录> --output <独立输出目录> --cases fixed texaco high-oxygen combined` 可对导出的旧提交运行相同输入。脚本不修改根目录工况或重启；保存输入、日志、GASTEST、START、`state.npz`、计时及汇总。联合模式汇总中的 `total_iterations` 为累计次数，`iterations` 只是最后一次内层次数。

本次旧版快照位于 `numeric_test/python_output/performance/baseline/src`，旧版计时在 `before`、`before-design`，最终计时在 `final`，实际设计验收在 `final-feed`、`final-extended`；这些生成数据按仓库约定忽略。精简验收数据随本文保存为 `docs/solver_performance_results.json`。

现有 Flask 每次启动计算都会创建新的 Python 子进程，更新代码及虚拟环境后下一次计算自动使用新求解器，无需修改用户输入。PyInstaller spec 已添加 SciPy 隐藏导入；本次验证的是源码运行，未重新发布可执行文件。
