# 项目结构与维护边界

[文档总索引](README.md) · [代码与数学物理手册](code_reference/README.md)

本项目保留Fortran移植的COMMON单例和函数名称，并在外层增加模型配置、设计反算和两套界面。本轮采用文档导航、符号索引和注释清理来整理代码；不搬动数值模块或改写全局状态，以免把重构与物理修订混在一起。

## 目录地图

```text
texaco_gasfier/
├── README.md / AGENTS.md         项目入口 / 开发约定
├── requirements.txt             Python依赖（未锁定完整环境）
├── src/
│   ├── main.py                  主迭代、运行模式、返回码
│   ├── common/
│   │   ├── common_data.py       COMMON、数组、默认状态
│   │   ├── physical_constants.py  现代与TEXACO兼容常数
│   │   ├── input_validation.py  输入/目标边界
│   │   ├── display_units.py     MPaG/℃显示转换
│   │   └── ...                 进度/输出文本等共享工具
│   ├── subroutines/
│   │   ├── initialization.py   EINGAB / GEOMETRY / QHCRCT
│   │   ├── gasifier_main.py    每格残差、源项、数值雅可比
│   │   ├── mass_flow.py        XMASS颗粒流闭合
│   │   └── output_results.py   焓、最终刷新、结果/重启
│   └── functions/
│       ├── gas_reactions.py    FLUCHT / XK1–XK6
│       ├── reaction_rates.py   A1–A5、物性、辐射等
│       ├── fh2o_fortran.py     反应侧历史水表
│       ├── steam_props.py      独立水侧IF97
│       ├── math_utils.py       带状/块三对角求解、更新
│       ├── feed_design.py      温度/有效气量反算进料
│       └── rsc_design.py       废锅目标温度反算高度
├── data/                       输入模板及历史START
├── web_backend/                Flask服务、文件解析/参数元数据
├── web/                        HTML、CSS、原生JS、本地Plotly
├── app.py                      Streamlit界面
├── run_app.py / run_app.*       桌面/脚本启动辅助
├── TEXACO_GUI.spec / hooks/     PyInstaller打包配置
├── numeric_test/                unittest、独立账/流程/性能验收
├── fortran_base/                原始Fortran、输入和历史可执行文件
├── scripts/                    文档检查与发布辅助
└── docs/                       当前手册、版本验收与历史归档
```

详尽模块和函数签名见[自动源码索引](code_reference/10_CODE_INDEX.md)，不在此重复维护可能过期的行号。

## 四层依赖及修改入口

| 层次 | 允许依赖/状态 | 常见修改位置 |
|---|---|---|
| 物性/速率 | COMMON配置及数值库 | 常数表、气体/固体焓、反应速率、IF97 |
| 控制体/求解 | 上层提供函数，COMMON共享数组 | 11个方程、雅可比、XMASS、线性解与限步 |
| 运行/设计 | 初始化、完整内层求解、候选状态 | main、feed_design、rsc_design、输出/进度 |
| 界面/协议 | 通过输入文件/子进程/API访问模型 | dataparser、Flask、Streamlit、原生JS |

这不是严格纯函数分层：ENTKOL、XMASS等会写全局数组，有限差分也会临时扰动状态。实现前置条件和缓存生命周期见手册第2、4章。直接绕过EINGAB混用旧状态可能得到形式合理但错误的结果。

## 输入、输出、证据的分离

- `data/Datain0.dat`为版本化典型输入；计算不应悄悄改写它以满足验收。
- `data/START.DAT`为仓库已有历史重启数据，不能保证符合当前60格模型；KTRL=1更适合作为新验收起点。
- 根目录GASTEST/START/进度/日志属于运行生成物，通常被Git忽略，不是源码版本证据。
- `numeric_test/python_output/<独立案例>/`保存输入副本、run.log、结果及完整状态；目录被忽略，关键精简验收JSON放docs并注明源码/输入哈希。
- `fortran_base/`是兼容比较资料，除明确的历史基准维护任务外不改动。
- `docs/archive/`是时间明确的旧文档；当前说明链接应优先指向手册和现行登记册。

## 依赖和启动

NumPy负责数组；SciPy提供带状LAPACK；iapws提供水侧IF97；Flask/Streamlit是两套独立界面；Plotly负责可视化；PyInstaller用于打包。`requirements.txt`为最低版本范围，不是可复现环境锁文件。验收需记录实际Python/NumPy/SciPy/iapws版本。

Web使用本地`web/static/js/plotly.min.js`，没有Node构建步骤。服务默认单进程、单任务；Python模块本身不保证线程安全。打包配置是维护入口，不表示本轮重新构建并验证了exe。

## 文档与源码同步

新增/改名符号后运行`python scripts/check_docs.py --write-index`。改参数同步第5章，改方程同步第3/6/7章，改收敛或搜索同步第8章，改失败行为同步第2/4/9章。AGENTS保留简明约束，详细推导集中在手册，避免把同一公式分散复制到多个入口。
