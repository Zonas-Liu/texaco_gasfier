# 4. Python接口与Web API

[手册首页](README.md) · [完整签名与源码行号](10_CODE_INDEX.md)

以下接口服务于现有共享状态模型。多数函数有COMMON副作用，并非纯函数。导入时应将仓库src加入sys.path，统一用`common.../functions.../subroutines...`模块路径；不要在同一进程以不同模块名重复装入不同的COMMON实例。

## 4.1 主计算与初始化接口

| 接口 | 输入与前置条件 | 返回/副作用 |
|---|---|---|
| main(data_path) | 已存在有效工况；输出工作目录可写；没有另一计算共用目录 | 0或2；异常上报后抛出；覆盖GASTEST、进度及可能的START |
| eingab(data_path,output_file=None,overrides=None) | 路径相对仓库或绝对；overrides仅FOXY/BSLURRY/KTRL | None；原位清空COMMON并完整构建当前工况，可能读取START |
| geometry() | KMODEL/格子范围、RSC尺寸和边界已设置 | None；写H/DELZ/AT/AR/HREAK/HFED/HNZFR，不自动重建进料 |
| qhcrct() | FLUCHT释放量及煤质已有效 | None；写QH_CRCT/DELTH/H_RACT/H_IN；历史热校正待核验 |
| CommonData.reset() | 不得与另一计算并发 | 清空并初始化同一实例；外部引用保持 |
| configure(common) | 已确定KMODEL，且尚未构造源项 | 写质量表、常数和CONSTANTS_BASIS |
| validate_params(params) | 字典值可转换为有限数，包含模式所需字段 | None或ValueError；不归一化煤分析、不运行求解 |

仅调用geometry不会自动改变FOXY派生氧量或挥发分；变进料应重新EINGAB。仅把common.T写成目标值也不会得到守恒解。

## 4.2 方程与线性求解接口

`gasifier`接收XMASS、ENTFED、ENTKOL、XK1–6、A1–5、PHI、RI、ENTHP、可选WDKR回调；原生回调启用局部/缓存优化，外部注入回调保持旧调用约定。返回累计碳反应速率诊断，主要结果写入A/B/C和DMAT=−R。

`_calculate_dmat_for_cell(i,...)`仅计算指定格当前R，并改派生流量、物性、QKW等。它不解线性系统；调用前需确保几何、源项、上下游状态和回调有效。不要在模型已收敛后无条件调用它再误将DMAT解释为Δu。

`newtra(omega)`选择线性后端后调用kolon1；`solve_banded_blocks(m,N)`只线性求解并写DMAT，不更新FEMF/T/WE/X；`blktrd(m,N)`还会原地改变矩阵。`kolon1`要求DMAT已经是有限修正量。

matadd/matsub/matmult/matdiv/matums、gausll是旧BLKTRD基础设施，保留Fortran尺寸/负号表示转置的参数协议；正常新增模型代码优先使用上层求解入口，勿直接混用0-based NumPy切片与其1-based参数。

## 4.3 物性、源项与派生量

| 接口族 | 关键前置条件 | 输出 |
|---|---|---|
| xk1..xk6(i) | FEM/FEMF/T/P/AT/DELZ有效，FEM>0 | 气相反应速率kmol/s；修改Y |
| flucht() | 煤质、质量基准、BSMS/BSWAF及分配区已设 | 原位写挥发分与固定碳源项，可能截XVM上限 |
| A1..A5(i), RI(i) | 当前持料量XMS、ROS及气体状态有效 | A为kmol/s；RI为kg/s；修改Y |
| TPAR(i), PHI(i), XKC_*(i) | 同次状态及粒径 | K、无量纲、kmol/(m²·Pa·s) |
| xmass(cells=None) | 按上游→下游更新；上游ROS须有效 | (选中格停留时间合计s,持料量合计kg)；修改多组数组 |
| entfed() | 外部/挥发进料已构建 | 写FEEDH、FEDPH、HFH2O |
| entkol(cells=None,cache=None) | 各格T/P有效；cache仅用于同次组装/同一常数配置 | 写HENTH、DHDT；cache为(T,P)→两个10元素副本 |
| ENTHP(KOMP,IAGG,T,P) | KOMP1..10；相态G/L/S按物种支持 | 气体J/kmol，固体J/kg，含生成焓 |
| ENTHP_DELTA(...) | 与ENTHP相同，附T_REF | 同一基准下的焓差；不用于替代完整反应焓 |
| FH2/FCO等 | KALZG为ENTH/MOLG等受支持字符串 | 物种特定性质；未支持的请求可能返回0 |
| WDKR(T,TW) | 正常调用者保证T>TW | W/(m²·K)；本函数未处理T=TW除零 |
| FXMUG(Y_array,T) | 晋华炉需9槽1-based数组、8个非负组分且总和>0 | Pa·s；不等于主XMASS当前粘度 |
| steam_production(Q,P,Tfw) | 有限Q，4–10MPa绝压，液态给水温度 | kg/s；负Q返回0 |

两个RI要区分：`functions.reaction_rates.RI`重新算碳反应；`subroutines.output_results.RI`只读RAC诊断。两个TPAR/tpar也不能凭同名就认为所有辅助温度接口都被主流程调用。`tpar1`、`hcrt`、纯组分IDIC/IVIS等属于保留辅助路径，其存在不代表验证完备。

## 4.4 输出及文件工具

- `kolerg(output_file=None,write_restart=True)`刷新主要派生量、输出KONTR诊断与剖面/出口/产汽；None写stdout；write_restart控制调用START写入，不自动验收KONVER。
- `write_start(outfile)`把当前状态保存到工作目录START；写入异常仅向outfile报告警告，未自动改变求解返回码。
- `kontr()`返回`(hein,haus,dh,dm,xmein,xmaus)`，能量项W、质量kg/s；是同模型内置账，不是独立模型验证。
- `read_result_text(Path)`先UTF-8含BOM兼容，失败再GBK；不静默替换错误字节。
- `parse_outlet(text)`返回Temperature(C)/CarbonConversion或空字典，按明确标识搜索。
- `write_progress`使用临时文件+os.replace避免半截JSON；写入失败不阻断计算，进度不应成为唯一成功证据。

## 4.5 外层纯搜索接口

`search_feed(evaluate,...)`的回调返回至少temperature_c、effective_gas_nmh、converged；实际驱动还返回iterations。输入initial/lower/upper均为两个正数，目标和范围应先通过校验。返回包含最终候选、success、目标/容差/误差、evaluations、trials。

`search_height(evaluate,...)`的回调返回temperature_c、converged；实际驱动另外返回热负荷/产汽/iterations。返回success及最后候选，不承诺失败时自动选取全轨迹中温差最小者。

`run_feed_design`和`run_target_design`是模型驱动层：管理COMMON、输出头、同次状态复用及START接受条件。外部应用通常调用main而不是手动嵌套这两个函数。

## 4.6 Flask HTTP接口

服务器绑定127.0.0.1，默认5000；当前任务可临时用其他端口。请求体及响应**仍使用核心单位Pa绝压/K**，前端显示转换见第5章。

| 路由 | 请求 | 返回及状态 |
|---|---|---|
| GET / | 无 | index.html |
| GET /api/params | 无 | info、lines、values、groups、grouped；200 |
| POST /api/params | JSON对象，可局部更新 | 合并校验并保存；values；400非法/409计算中 |
| POST /api/run | JSON对象，`{}`表示按已保存参数运行 | 保存后启动子进程；status=started、pid、data_file；400/409/500失败 |
| GET /api/progress | 无 | 进度字段及running/completed、进程returncode等；200 |
| GET /api/results | 无 | parse_gastest结构化结果、湿气补充字段；无文件404 |
| GET /api/output | 无 | `{"text":"..."}`原始文本；无文件404 |

未知参数拒绝；布尔值不能作为数值；整数控制量不得截断小数。JSON根必须是对象，空请求体不等于`{}`。服务无通用多用户认证/作业队列，当前仅本机单用户单任务设计。

只读检查示例（不会启动计算或改参数）：

```python
import json
from urllib.request import urlopen
with urlopen('http://127.0.0.1:5000/api/results') as response:
    result = json.load(response)
for section in result['outlet_sections']:
    print(section['label'], section['temperature_c'], section['ash_kg_h'])
```

## 4.7 前端关键函数与状态

`loadParams/renderParams/collectParams`读元数据并双向转换显示单位；`saveParams/runSimulation`分别保存和启动；`pollProgress`跟踪进程/计算状态；`loadResults`加载输出；`activateTab/renderTab`延迟绘图；`renderOutlets`使用同次出口JSON；`renderFeedDesign/renderDesign`展示外层轨迹。

`showSummary/renderProcess`把同次输出的摘要、出口和热回收数据绑定到工艺示意；不使用编辑中的参数补齐旧结果。TEXACO只显示一个出口且隐藏RSC与产汽区。`plotLine`温度图以第30格为交界分段着色并共用交界点，不平滑或改写原始数据；`syncDrawer/drawer`管理窄屏抽屉、inert和焦点回退。视觉规范及浏览器验收见[工艺工作台设计](../UI_REDESIGN_2026-11-02.md)。

用户改参后旧结果仍可能保留显示，需要标记为上次结果；未达目标的结果只作诊断。前端缺数值显示破折号，不用默认零或示例结果填补。
