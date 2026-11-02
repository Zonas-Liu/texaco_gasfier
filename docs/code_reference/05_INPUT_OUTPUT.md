# 5. 输入、输出与单位协议

[手册首页](README.md) · [接口说明](04_API_REFERENCE.md) · [可运行示例](../USAGE_EXAMPLES.md)

## 5.1 Datain0.dat语法与兼容

前11行必需；12–17行为可选扩展。每行逗号分隔，首个`/`后为注释，支持E/e和Fortran D/d指数。按行号解析，不能随意插入空行或把参数分组换位置。可选行可留空以保留后续行号；第9行历史6项形式缺ELH2O时默认为0。

输入列数依次为`1,5,2,4,4,2,1,2,7,3,1,3,5,2,4,3,4`。前11行缺失不会由默认值补齐；下表前11行的“默认”指界面元数据备用值，实际计算必须提供。第12–17行缺失采用COMMON默认配置。当前仓库典型输入为14行，启用晋华炉、QLOSS=0.01、固定进料/高度。

KMODEL=0时13、14行物理参数不用于构建RSC；目标模式另有约束。API字段`PFEED_O2/TFEED_O2`映射到内部COMMON的`PFEED_OX/TFEED_OX`，文件仍是第5行相同位置。

## 5.2 全参数字典

压力文件/API值为Pa绝压；温度为K；名称以`_C`结尾的目标温度原生就是℃。比例输入是0–1的小数，默认值的0.6代表60%，不是填60。

| 行 | 参数 | 文件/API单位 | 界面显示单位 | 界面/可选默认 | 含义 |
|---:|---|---|---|---:|---|
| 1 | `KTRL` | 无量纲 | 无量纲 | 1 | 1=默认初始化，0=读取START重启 |
| 2 | `ITMAX` | 无量纲 | 无量纲 | 100 | 牛顿迭代最大步数 |
| 2 | `SKONFE` | kmol/s | 元数据未标注 | 0.0005 | SUMFE 收敛判据 |
| 2 | `SKONWE` | kg/s | 元数据未标注 | 0.0005 | SUMWE 收敛判据 |
| 2 | `SKONX` | 无量纲 | 无量纲 | 0.0005 | SUMX 收敛判据 |
| 2 | `SKONT` | K | 元数据未标注 | 0.005 | SUMT 收敛判据 |
| 3 | `BSLURRY` | kg/s | kg/s | 14 | 水煤浆总质量流量（含煤和水） |
| 3 | `RATIO_COAL` | 无量纲 | 无量纲 | 0.6 | 输入煤占煤浆总质量的比例；煤内水由ELH2O单独指定 |
| 4 | `FOXY` | kg O₂/kg BSWAF | kg O₂/kg BSWAF | 0.98 | 纯氧质量流量与无水无灰煤质量流量之比 |
| 4 | `PURE_O2` | 无量纲 | 无量纲 | 0.996 | 工业氧气中 O₂ 的摩尔分数 |
| 4 | `OX_PART` | 无量纲 | 无量纲 | 1 | 一次氧气占总氧气比例 |
| 4 | `RATIO_CO2` | 无量纲 | 无量纲 | 0 | 进料 CO₂ 比例 |
| 5 | `PFEED_SL` | Pa | MPaG | 8.1e+06 | 水煤浆喷嘴前压力 |
| 5 | `TFEED_SL` | K | ℃ | 318.15 | 水煤浆入口温度 |
| 5 | `PFEED_O2` | Pa | MPaG | 8.1e+06 | 氧气喷嘴前压力 |
| 5 | `TFEED_O2` | K | ℃ | 293.15 | 氧气入口温度 |
| 6 | `PFEED_CO2` | Pa | MPaG | 8.1e+06 | CO₂ 喷嘴前压力 |
| 6 | `TFEED_CO2` | K | ℃ | 293.15 | CO₂ 入口温度 |
| 7 | `DP` | m | m | 0.0001 | 颗粒平均直径 |
| 8 | `HU` | kJ/kg | kJ/kg | 25900 | 收到基低位发热量 |
| 8 | `XVM` | 无量纲 | 无量纲 | 0.28 | 煤中挥发分质量分数 |
| 9 | `ELC` | 无量纲 | 无量纲 | 0.6802 | 输入煤同一分析基准的碳质量分数；不自动换基 |
| 9 | `ELH` | 无量纲 | 无量纲 | 0.0404 | 输入煤同一分析基准的氢质量分数；不自动换基 |
| 9 | `ELO` | 无量纲 | 无量纲 | 0.0985 | 输入煤同一分析基准的氧质量分数；不自动换基 |
| 9 | `ELN` | 无量纲 | 无量纲 | 0.0249 | 输入煤同一分析基准的氮质量分数；不自动换基 |
| 9 | `ELS` | 无量纲 | 无量纲 | 0.006 | 输入煤同一分析基准的硫质量分数；不自动换基 |
| 9 | `ELAS` | 无量纲 | 无量纲 | 0.15 | 灰分质量分数 |
| 9 | `ELH2O` | 无量纲 | 无量纲 | 0 | 煤中水分质量分数 |
| 10 | `TU` | K | ℃ | 298.15 | 参考环境温度 |
| 10 | `TW` | K | ℃ | 2200 | 气化炉壁面温度 |
| 10 | `PWK` | Pa | MPaG | 6.7e+06 | 气化炉内操作压力 |
| 11 | `QLOSS` | 无量纲 | 无量纲 | 0.03 | 除壁面辐射外的附加热损失比例 |
| 12 | `KMODEL` | 无量纲 | 无量纲 | 0 | 选择 TEXACO 或晋华炉 3.0 |
| 12 | `P_DRUM` | Pa | MPaG | 6.5e+06 | 影响饱和蒸汽焓与产汽量；适用范围 3.898675–9.898675 MPaG |
| 12 | `T_FW` | K | ℃ | 423.15 | 与饱和蒸汽焓共同决定单位回收热量的产汽量 |
| 13 | `TW_WALL` | K | ℃ | 1773 | 燃烧室渣层表面温度 |
| 13 | `TW_RSC` | K | ℃ | 673 | 积灰壁面等效辐射温度 |
| 13 | `D_RSC` | m | m | 2.6 | 影响换热面积与气体速度 |
| 13 | `H_RSC` | m | m | 30 | 固定高度模式的给定值；目标温度模式的搜索初值 |
| 13 | `N_RSC` | 无量纲 | 无量纲 | 30 | 1–30；典型算例使用30格；需网格敏感性验证 |
| 14 | `KRELAX_WGS` | 无量纲 | 无量纲 | 2 | 辐射废锅水煤气变换反应 |
| 14 | `KRELAX_METH` | 无量纲 | 无量纲 | 0.02 | 辐射废锅甲烷化反应 |
| 15 | `RSC_MODE` | 无量纲 | 无量纲 | 0 | 目标温度模式同时求有效高度、回收热量和产汽量 |
| 15 | `T_RSC_OUT_C` | °C | °C | 780 | 目标温度模式启用；需高于废锅有效壁温 |
| 15 | `H_RSC_MIN` | m | m | 1 | 目标温度模式的搜索边界 |
| 15 | `H_RSC_MAX` | m | m | 120 | 未括住目标时报告失败，不超出范围外推 |
| 16 | `FEED_MODE` | 无量纲 | 无量纲 | 0 | 按燃烧室出口温度与 CO+H₂ 标方流量反算氧煤比和水煤浆总量 |
| 16 | `T_CHAMBER_C` | ℃ | ℃ | 1228 | 允许温差 ±0.5 ℃ |
| 16 | `EFFECTIVE_GAS_NMH` | Nm³/h | Nm³/h | 49600 | 燃烧室出口；0℃、101.325 kPa，晋华炉约22.41397 Nm³/kmol；允许误差为目标的 0.1%（最小 1 Nm³/h） |
| 17 | `FOXY_MIN` | kg O₂/kg BSWAF | kg O₂/kg BSWAF | 0.7 | 纯氧 / 无水无灰煤 |
| 17 | `FOXY_MAX` | kg O₂/kg BSWAF | kg O₂/kg BSWAF | 1.3 | 纯氧 / 无水无灰煤 |
| 17 | `SLURRY_MIN` | kg/s | kg/s | 5 | 水煤浆总量，包含煤和水 |
| 17 | `SLURRY_MAX` | kg/s | kg/s | 30 | 保持煤浆浓度、氧气纯度及其余参数不变 |


各行具体补充：

- 第1行KTRL=1是正常初始化，0是读取重启；FEED_MODE=1会忽略历史重启并强制本次初始化。
- 第2行SKONFE/WE/X/T的实际单位分别为kmol/s、kg/s、无量纲、K，表示**全炉原始牛顿修正量绝对值和**阈值；元数据空unit不等于这些量都无量纲。
- 第3/9行煤分析同一基准。BSMS可能包含ELH2O对应煤内水；程序不会把输入分析自动换干基。ELC/H/O/N/S不应再包含已单列为水或灰的质量。
- 第4行RATIO_CO2实际是CO₂/整个氧化剂的摩尔或同标况体积比；杂质N₂全部在首格，OX_PART只拆O₂。
- 第7行DP是m，100μm应填0.0001；第8行HU是kJ/kg，25900相当于25.9MJ/kg。HU基准应与输入煤配套，界面历史“收到基”名称不自动执行基准换算。
- 第8行XVM大于0.5166时FLUCHT会截至0.5166；这发生在COMMON，未自动回写文件。0–1输入校验不是挥发分经验式的全范围有效性保证。
- 第10行TU被读入，但多数物性函数使用自身固定298.15K基准；不应以修改TU来期待整体焓参考态迁移。TW仅用于KMODEL=0；晋华炉取TW_WALL/TW_RSC。
- 第12行P_DRUM与PWK是不同压力：前者水侧汽包，后者气侧炉膛；没有要求二者数值相等。
- 第13行H_RSC固定模式是给定高度，设计模式是初猜；N_RSC受1–30容量限制。有效壁温不是金属管壁温度，也不会随P_DRUM自动更新。
- 第14行松弛系数是每格经验参数；不能直接解释为s⁻¹。第15行目标温度必须严格高于TW_RSC。
- 第16行有效气量是燃烧室第30格CO+H₂之和，不是废锅出口总干气，也不是全部合成气。
- 第17行反算进料初值必须在给定正边界内；搜索解单独输出，不自动覆盖用户输入初值。

## 5.3 校验范围

所有已知数值必须有限；布尔值拒绝。KTRL/KMODEL/RSC_MODE/FEED_MODE只能0/1，ITMAX和N_RSC必须整数。输入行层也检查控制整数，不以int()静默截断。

BSLURRY、RATIO_COAL、PURE_O2、DP、HU、ELC、正绝温/绝压及收敛阈值必须>0。元素、灰、水、XVM、OX_PART、QLOSS等比例限制0–1；FOXY、RATIO_CO2、两松弛系数非负；ELAS+ELH2O<1。

RSC启用时H/D/有效壁温>0；P_DRUM绝压4–10MPa；T_FW在0℃到该压力饱和温度之间。反算需正目标气量、温度高于绝对零度、正且有序边界、初值在界内。RSC目标模式仅KMODEL=1，Hmin<Hmax且均正。

**没有实现的校验**：元素总和=1、全部动力学适用域、灰矿物组成、TW与汽包/材料条件相容性、全目标可达性、每格EPS合法性。通过输入校验仅表示基本格式和数值边界成立。

## 5.4 显示单位双向转换

[display_units.py](../../src/common/display_units.py)为共享约定：

$$
P_{abs}[Pa]=(P_g[MPaG]+0.101325)10^6,\quad
T[K]=t[℃]+273.15.
$$

反向减去相同偏置。例：PWK=6.7e6 Pa显示6.598675 MPaG；P_DRUM=6.5e6 Pa显示6.398675 MPaG；423.15K显示150℃。目标温度字段原单位℃不再减273.15。

浏览器根据`info.display`换算输入/显示；API发送的仍是模型单位。直接调用API时发送`P_DRUM:6.5`会被当成6.5Pa而报错，不会自动推测单位。

## 5.5 输出文件与可信度

| 文件 | 内容 | 注意 |
|---|---|---|
| GASTEST.DAT | 当次条件、末候选收敛历史、剖面、出口、产汽及JSON | 每次main覆盖；UTF-8；失败也可产生诊断结果 |
| START.DAT | 下一次初始化状态 | 无版本/常数元数据；不是验收证明；只含格式化后的有限精度数值 |
| simulation_progress.json | 当前内层迭代、修正量和状态 | 原子替换；写失败不终止求解；设计每候选进度会重置 |
| python_matrix_iter0.txt | 首轮前5格矩阵片段 | 外层多候选会覆盖；不是完整全炉雅可比 |
| .simulation_stdout.log/.simulation_stderr.log | 界面启动的计算进程日志 | 新任务覆盖，故重要验收需另存 |

KOLERG内部剖面字段实际意义：

| 文本/解析键 | 实际内容 |
|---|---|
| I | 格子号，1-based |
| H(m) | 历史H位置，整炉不连续，不能直接等同流向距离 |
| U0(m/s) | 表观气速 |
| ResidenceTime(s) | **累计**颗粒停留时间ΣTRZ，非单格TRZ |
| WE(kg/s)，旧表头“碳流量” | **总固体**WE，非残碳WE·X |
| T(C) | T−273.15 |
| X(%) | 历史FOC指标×100，非common.X×100 |
| outlet.CarbonConversion | 1−残碳出口/(煤中元素碳入口)，0–1 |

文本剖面通常舍入到3位小数，出口干基/体积部分为4位；不要据此进行高精度独立守恒核算。完整状态由隔离验收脚本存state.npz。

## 5.6 START布局

N个有效格，共11N个数：先每格4个组分n1..n4（4N个），再每格n5..n8（4N个），然后N个T、N个X、N个WE。不是每行直接一个11变量状态向量。当前写法分别为2N行气体和3N行标量。

读取要求恰好11N个有限数，气体≥0、T>0、0≤X≤1、WE>0；允许D指数。读完校验后才整体写COMMON，避免半读状态。网格不匹配或文件损坏报错，KTRL=1可重新初始化。

写入仅6位科学计数法小数，故START不保存全精度解；微量物种/严格比较应另存NPZ。旧START没有CONSTANTS_BASIS，即使数量匹配也不能证明适用于新质量基准。正算失败写入的已知限制见第2、9章。

## 5.7 三种结构化JSON记录

每行前缀加一个JSON对象，数值来自同次最终候选：

**OUTLET_FLOWS_JSON**：以字符串格号`"30"`和`"60"`（或实际末格）为键。TEXACO只有一个出口键。每个值含：

| 字段 | 含义 |
|---|---|
| molar_flow_kmol_h | 8物种字典，FEMF×3600 |
| ash_kg_h | WE·(1−X)×3600 |
| temperature_c | 完整精度截面温度 |
| normal_molar_volume_nm3_kmol | 当次标方摩尔体积 |
| normal_temperature_k / normal_pressure_pa | 273.15K、101325Pa |
| constants_basis | CIAAW-2024-CODATA-2022或fortran-legacy |

它没有保存完整固体X/WE及所有输入，因此仅凭这个JSON仍不足以核算含残碳的完整元素账。

**FEED_DESIGN_JSON**：success为燃烧室目标状态，overall_success还包括废锅设计；oxygen_coal_ratio、slurry_kg_s、temperature_c、effective_gas_nmh、目标、容差、偏差、evaluations、trials、bounds，以及煤/纯氧质量流。历史`dry_coal_kg_h`字段实际使用BSMS×3600，煤内水非零时名称不严谨。

**RSC_DESIGN_JSON**：success、mode、target_temperature_c、temperature_c、temperature_error_c、height_m、height_min_m/height_max_m、heat_rsc_mw、steam_rsc_tph、steam_total_tph、iterations、evaluations和trials。success要求内层收敛且目标偏差≤0.5℃。

## 5.8 Web解析结果

parse_gastest返回operating_conditions、convergence_history、internal_profile、gas_composition_profile、syngas_composition、volume_flow、outlet，并添加heat_recovery、outlet_sections及可选设计对象。operating_conditions的param_i是早期文本位置派生键，不是稳定的完整工况快照。

outlet_sections含key/label/cell、干湿组成、Nm³/s流量、kmol/h摩尔流、总量、灰、有效气量和H₂/CO比。计算：

$$
y_j^{wet}=n_j/\sum n_j,\quad y_j^{dry}=n_j/(\sum n_j-n_{H_2O}),
$$
$$
V_j[Nm^3/s]=n_jVM_{normal},\quad Q_{eff}[Nm^3/h]=(n_{CO}+n_{H_2})VM_{normal}3600.
$$

优先使用精确JSON重建出口百分比/体积，避免从舍入剖面反推。历史无元数据时按22.4换算；无灰数据时为空，不能用当前输入补算历史灰流。heat_recovery来自同次文本，精度受文本舍入限制；设计JSON的热/汽值通常保留更高精度。

旧GBK结果可读；新结果固定UTF-8。发生解析失败应检查原始文件/编码和版本，不应填假零。读取前端结果也需结合进程returncode及overall_success，输出对象存在不代表成功。
