# AGENTS.md — TEXACO / 晋华炉3.0 气化炉模拟项目

## 项目概述
TEXACO（德士古）水煤浆气化炉 Fortran 程序的 Python 移植版（1D 活塞流 + 块三对角牛顿求解器）。
在 `jinhualu` 分支上扩展为**晋华炉3.0**模型：膜式水冷壁燃烧室 + 辐射废锅（RSC）。

## 分支策略
- `main`：稳定主干
- `texaco`：TEXACO 原版模型基准（30 网格，耐火砖壁面），用于对比验证
- `jinhualu`：晋华炉3.0 开发分支（当前工作分支）

## 代码结构要点
- `src/main.py`：主迭代循环（对应 Wg1.for）
- `src/common/common_data.py`：全局数据单例（Fortran COMMON 块）。数组 1-based 索引，索引 0 闲置
- `src/subroutines/initialization.py`：输入解析（EINGAB）、几何（GEOMETRY）、热校正（QHCRCT）
- `src/subroutines/gasifier_main.py`：核心——DMAT/AMAT/BMAT/CMAT 组装，数值微分求雅可比
- `src/subroutines/mass_flow.py`：固体质量流（XMASS）
- `src/subroutines/output_results.py`：结果输出（KOLERG → GASTEST.DAT + START.DAT）
- `src/functions/gas_reactions.py`：气相反应 XK1-XK6 + 挥发分释放（FLUCHT）
- `src/functions/reaction_rates.py`：碳反应 A1-A5、ENTHP 焓值（含生成焓）、WDKR 辐射换热系数
- `src/functions/steam_props.py`：（晋华炉新增）饱和蒸汽物性关联式
- `numeric_test/`：Python vs Fortran 数值对比验证

## 关键设计约束
- **ENTHP 焓值含标准生成焓**（如 CO: HMT=-110594.12 kJ/kmol，ENTHP 返回时乘 1000 转为 J/kmol），因此通过 DMAT 组分源项改变
  FEMF 时，反应热自动计入能量平衡，无需额外处理
- DMAT 的雅可比通过数值微分自动获得（通常扰动 0.0001；KMODEL=1 的残碳 X 使用下述相对步长）：新增任何连续的源项/汇项都会被
  自动线性化，无需手写偏导
- 挥发分与煤浆进料分布在第 1 格；OX_PART<1 时第 N2FED=7 格可有二次氧气进料，RSC 段无进料
- 输入文件 `data/Datain0.dat` 按行解析；新增参数追加在末尾新行，缺失时用默认值（向后兼容）
- GUI（app.py / web_backend）按固定行数读写 Datain0.dat，新增行需注意保留

## 晋华炉3.0 模型设计（jinhualu 分支）

### 与 TEXACO 的物理差异
1. 燃烧室周围为**膜式水冷壁**（非耐火砖）：壁面有效辐射温度大幅降低，
   吸收热量产出饱和蒸汽（约 2 t/h）
2. 燃烧室下方接**辐射废锅（RSC）**：粗煤气进一步辐射降温至 750~800℃，产出大量饱和蒸汽

### 建模方案（已经用户确认）
- **网格扩展**：燃烧室 1..30 格（不变）+ RSC 段 31..60 格（默认 N_RSC=30，等分 H_RSC）。
  数组尺寸 NZDIM=61（支持 1≤N_RSC≤30）。KMODEL=0 时退化为原 TEXACO（NZRE=30）
- **水冷壁**：DMAT 能量行热汇 QKW[i]=WDKR(T,TW_i)·AR·DELZ·(T−TW_i)，
  燃烧室段 TW_i=TW_WALL（渣层表面有效温度），RSC 段 TW_i=TW_RSC。
  回收热量 → 蒸汽产量 = Q/(h″(P_DRUM) − h_fw(T_FW))
- **QLOSS 经验热损失项**仅作用于燃烧室段（i ≤ NZRC）
- **RSC 平衡反应**（部分平衡/松弛源项法，仅 i > NZRC）：
  - 水煤气变换 WGS：CO+H2O↔CO2+H2，K_WGS(T)=exp(4577.8/T − 4.33)
  - 甲烷化：CO+3H2↔CH4+H2O，K_METH(T)=exp(24766/T − 25.82)（298K 标准态范特霍夫近似）
  - R = KRELAX · 驱动力 · FEM[i]，作为 DMAT 组分源项（能量效应经 HENTH 自动计入）
- **蒸汽物性**：汽包4–10 MPa绝压范围采用IAPWS-IF97，给水焓按汽包压力计算压缩液；已用官方校核点验证。水侧焓不得直接替换含生成焓的气侧ENTHP。

### 新增输入参数（Datain0.dat 第 12-17 行，可选）
- 行12: KMODEL, P_DRUM(Pa), T_FW(K)
- 行13: TW_WALL(K), TW_RSC(K), D_RSC(m), H_RSC(m), N_RSC
- 行14: KRELAX_WGS, KRELAX_METH
- 行15: RSC_MODE, T_RSC_OUT_C(°C), H_RSC_MIN(m), H_RSC_MAX(m)；缺失为固定高度模式。
- 行16: FEED_MODE, T_CHAMBER_C(℃), EFFECTIVE_GAS_NMH(Nm³/h)；缺失为给定进料模式。
- 行17: FOXY_MIN, FOXY_MAX, SLURRY_MIN(kg/s), SLURRY_MAX(kg/s)。

### 典型参数（晋华炉3.0，已按典型工况调定）
- P_DRUM=6.5 MPa（Tsat≈281℃），T_FW=150℃
- TW_WALL=1773 K（渣层表面），TW_RSC=673 K（积灰壁面）
- D_RSC=2.6 m，H_RSC=30 m，N_RSC=30（NZDIM=61，支持 N_RSC≤30）
- QLOSS=0.01（水冷壁炉型取低值，原 TEXACO 为 0.03）
- KRELAX_WGS=2.0，KRELAX_METH=0.02

## 运行与测试
- 运行：`python src/main.py`（输出 GASTEST.DAT / START.DAT / simulation_progress.json）
- GUI：`.venv\Scripts\streamlit run app.py`
- Web 版：`python web_backend/app.py`（http://127.0.0.1:5000）

## 晋华炉3.0 历史验证结果（2026-08-18；已被后续守恒修复更新）

以下数值保留作历史记录。当前基准及新物性来源见 `docs/ELEMENT_BALANCE_FIX.md`、`docs/PHYSICAL_CONSTANTS.md`；不得继续将旧废锅结果作为正确目标值。
- 63 次迭代收敛（KONVER=0），残差 FE=2.7e-6 / T=2.0e-3
- 燃烧室出口 1228℃（膜式壁炉型合理区间），干基 CO 42.4% / H2 37.2%
- 辐射废锅出口 **756.9℃**（目标 750~800℃ ✓）
- 水冷壁产汽 **2.13 t/h**（目标 ~2 t/h ✓），废锅产汽 24.3 t/h，合计 26.4 t/h
- 最终干基合成气：CO 37.2% / H2 39.7% / CO2 20.8% / CH4 1.05%
- 向后兼容：KMODEL=0 + 原 11 行输入，结果与 texaco 分支逐位一致（62 次迭代，出口 1145.283℃）
- GUI 兼容：app.py / web_backend 的 write_datain0 会保留第 12-14 行新增参数

## 编码约定
- 中文注释、docstring 标注对应 Fortran 来源
- 与 Fortran 对齐处保留 1-based 索引注释
- 修改公共结构/流程时同步更新本文件

## 2026-11-02 审查后的流程约定
- `eingab()` 原位调用 `common.reset()`，每次运行从默认状态开始；缺失可选行不得继承前次模型。
- 输入必须为有限数，整数控制量不得截断；N_RSC 为 1–30，P_DRUM 为 4–10 MPa。
- `main()` 返回 0 表示收敛，2 表示迭代上限未收敛；异常上报 error 后抛出。
- SUMFE/SUMWE/SUMX/SUMT 实际为 BLKTRD 求解后的牛顿修正量绝对值和，不是原始守恒方程残差。
- GASTEST.DAT 固定 UTF-8；两套界面兼容读取历史 GBK 输出。输出前刷新派生流量、速度、焓及壁面热负荷。
- START.DAT 写入工作目录；KTRL=0 优先读取工作目录文件，缺失时读取输入文件同目录文件。
  重启文件必须匹配网格（每格 11 个值）；缺失或损坏会报错，改为 KTRL=1 可重新初始化。
- Flask 参数修改和启动共用锁，仅支持一个服务进程；不要同时从两个界面/CLI 运行同一目录。
- 审查说明与验证命令见 `docs/CODE_REVIEW_2026-11-02.md`；新回归测试使用标准库 unittest。

## Web 界面设计（2026-11-02）
- `web/index.html` / `web/static/css/style.css` / `web/static/js/app.js` 采用浅色工作台，设计规格见 `docs/UI_DESIGN.md`。
- Web 首次加载读取已有结果；参数搜索/折叠、结果标签页、窄屏抽屉及运行状态在原生 JavaScript 管理。
- `web_backend/dataparser.py` 返回可选 `heat_recovery`，数值只解析同次 GASTEST 输出；无该段的 TEXACO 输出不显示产汽数据。
- 图表按标签延迟绘制，显示缺值为破折号，不用设计稿示例数据；改参或计算中明确标记上次结果。
- 本次只改 HTML + Flask，Streamlit 保持独立。

## 辐射废锅目标温度模式（2026-11-02）
- RSC_MODE=0 保持固定 H_RSC；RSC_MODE=1 给定 T_RSC_OUT_C，以 H_RSC 为搜索初值，在指定高度范围内求解。
- `src/functions/rsc_design.py` 负责有界扩展和保守割线搜索。每个候选调用 `main._iterate()` 完整求解，几何随高度更新，沿用上一候选的收敛状态；不修改 DMAT 方程和反应系数。
- 仅当内层收敛且目标温差 ≤0.5℃ 才成功；最多 18 个候选。返回 2 还包括目标温度未达到。失败搜索不得覆盖 START.DAT。
- 各候选的 Q_RSC=sum(QKW) 与产汽量 Q_RSC/[h_steam(P_DRUM)-h_fw(T_FW,P_DRUM)] 联动；注意kJ/kg转J/kg，不得单独改显示温度或把蒸汽量当独立自由量。
- GASTEST 追加 `RSC_DESIGN_JSON` 保存同次设计结果与轨迹。双出口流量从已有 KOLERG 对照表解析；不从当前输入反推历史结果。
- Web 可编辑第 12–15 行，未变动可选行原样保留。Streamlit 仍只提供前 11 行编辑。
- 方法、验证、模型适用限制见 `docs/RSC_TARGET_DESIGN.md`；新测试见 `numeric_test/test_rsc_design.py`。

## 燃烧室双目标反算及界面单位（2026-11-02）
- `FEED_MODE=1` 以燃烧室出口温度和 CO+H2 标方流量（Nm³/h，使用本次 `VM_NORMAL`）为双目标，求 FOXY 与 BSLURRY；煤浆浓度、氧气纯度及其余参数不变。
- `src/functions/feed_design.py` 使用有界阻尼牛顿、有限差分雅可比及回溯。仅接受内层收敛、温差≤0.5℃、气量差≤max(1,0.001×目标) Nm³/h；最多40次试算，失败恢复最佳候选最多再算1次。
- `eingab(overrides=...)` 只接受 FOXY/BSLURRY/KTRL 覆盖，必须在派生量和源项初始化前应用。反算忽略历史 START，先正常初始化，再将本次已收敛状态按负荷缩放作为候选初值，仍完整重算源项并验证收敛。
- 可与 RSC_MODE=1 联用：先满足燃烧室双目标，再求废锅高度/产汽并复核最终燃烧室双目标。联合模式通过 `run_target_design(finalize=False)` 延迟最终状态与重启写入，全部通过才写 START。
- GASTEST 追加 `FEED_DESIGN_JSON` 记录目标、解、偏差、搜索范围、试算轨迹及 overall_success。输出条件必须来自最终候选，不能保留原始搜索初值作为结果条件。
- `OUTLET_FLOWS_JSON` 按格号记录温度、FEMF×3600 的 kmol/h、WE×(1−X)×3600 的灰 kg/h。WE 为总固体流，X 为其中碳质量分数。不得用当前输入补算历史结果中的灰。
- UI 压力为 MPaG、温度为℃，文件/API/核心原有压力仍为绝压 Pa、温度为K；目标温度字段自身保持℃。换算使用 `src/common/display_units.py`，参考大气压101325 Pa，Web 用 `info.display` 元数据双向转换。Streamlit 现有压力温度输入也同步转换。
- Web 编辑前17行，反算解显示在结果中、不自动改写初值；Streamlit仍只编辑前11行并保留扩展。测试：`numeric_test/test_feed_design.py`；实际隔离验收：`numeric_test/check_feed_design.py`。

## 求解性能与稳定性（2026-11-02）
- 晋华炉默认使用 `scipy.linalg.solve_banded`（LAPACK），按方程行最大系数缩放后求解；仍是原牛顿方程，收敛判据不变。仅 DMAT 写回修正量，A/B/C 不被线性求解修改。
- KMODEL=0 默认保留 BLKTRD 和固定差分，支持原 TEXACO 逐位对照。环境变量 `TEXACO_LINEAR_SOLVER=scipy|legacy` 可指定线性后端；legacy 仅切换线性求解，不关闭晋华炉自适应差分。
- KMODEL=1 的 X 列差分步长为 `max(1e-12,min(1e-4,abs(X)*0.01))`；其余变量和 KMODEL=0 仍为 1e-4。避免微量残碳附近固定步长引起修正量振荡，不放宽任何 SKON 阈值。
- ENTKOL 以 `(T,PWK)` 缓存完整十种组分焓和温度导数，缓存仅存活于一次 GASIFIER 组装。ENTFED 每次组装计算一次。局部物性更新包含本格和上游格；XMASS 的上游 ROS 必须有效，不能无条件将其他物性更新也裁成单格。
- 结果输出仍全炉刷新派生量。基准脚本 `numeric_test/benchmark_solver.py` 在隔离目录保存状态/计时；`--linear-only` 比较同一实际雅可比的求解耗时及后向误差。细节见 `docs/SOLVER_PERFORMANCE.md`；回归见 `numeric_test/test_solver_performance.py`。

## 元素守恒与物性基准修复（2026-11-02）
- 原RSC源项缩放不一致已在正式DMAT修复：CO2新增项同除1.2，H2新增项同乘1.02。不得只缩放基础项；回归直接检查实际DMAT新增源项的原子守恒。
- `numeric_test/check_element_balance.py` 从煤/水/氧化剂独立构造进口，对照湿气+残碳+灰两处出口；审计阈值为max(1e-6 kg/h,进口×1e-8)，不等同于牛顿修正量判据。默认7工况全部闭合，联合设计完整状态另验通过。
- 常数统一在 `src/common/physical_constants.py`：KMODEL=1使用CIAAW2024简明原子量及CODATA2022；气体摩尔质量、进料、源项、焓换算和输出不得另写整数质量。KMODEL=0保留fortran-legacy，完整状态及START逐位对照通过。
- 标况为273.15 K/101325 Pa。晋华炉 `VM_NORMAL=R_kmol*T/P≈22.413969545014`；TEXACO保留22.4。OUTLET_FLOWS_JSON保存当次体积和常数基准，历史缺失元数据时仅按旧22.4解析。
- 汽包/给水使用iapws>=1.5.5，`h_feedwater(T,P)`压力必填；IF97仅用于水侧。气侧旧热容系数、生成焓和水表归一化参数不可与新参考态零散混用。
- 典型新基准：64次收敛，燃烧室1232.374℃、废锅791.480℃、水冷壁2.157 t/h、废锅30.465 t/h；旧756.86℃与24.32 t/h已失效。46项单元回归通过。
- XVM=0源项传参及H2S耗氢已修正，但全炉默认100次仍未收敛，仅保留为可选诊断；KCHECK辅助模式、独立能量闭合和全操作范围不在本次验收范围。
- 当前证据见 `docs/ELEMENT_BALANCE_FIX.md`、`docs/element_balance_fixed_results.json`；常数来源、经验近似及适用边界见 `docs/PHYSICAL_CONSTANTS.md`。原缺陷历史报告保留。
