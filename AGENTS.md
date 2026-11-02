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
- DMAT 的雅可比通过数值微分（扰动 0.0001）自动获得：新增任何连续的源项/汇项都会被
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
- **蒸汽物性**：4–10 MPa 范围内简化关联式（Tsat、h″、汽化潜热），精度需以权威物性库独立验证，当前无全范围误差保证

### 新增输入参数（Datain0.dat 第 12-14 行，可选）
- 行12: KMODEL, P_DRUM(Pa), T_FW(K)
- 行13: TW_WALL(K), TW_RSC(K), D_RSC(m), H_RSC(m), N_RSC
- 行14: KRELAX_WGS, KRELAX_METH

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

## 晋华炉3.0 验证结果（2026-08-18, data/Datain0.dat 典型工况）
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
