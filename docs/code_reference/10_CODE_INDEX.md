# 10. 源码符号索引

[手册首页](README.md) · [接口语义](04_API_REFERENCE.md)

由 `scripts/check_docs.py --write-index` 从AST生成，请勿手改。包含src、web_backend及两入口模块的类、函数、方法、嵌套函数；不导入这些模块。签名与定义行来自源码，末列仅摘录docstring首行，不代替前9章的前置条件、单位、公式和适用边界。

范围：27 个Python文件，192 个定义。测试/实验脚本见[验证章](09_VALIDATION_AND_LIMITATIONS.md)，原生JS接口见第4章。

## 模块导航

| 文件 | 定义数 |
|---|---:|
| [app.py](../../app.py) | 28 |
| [run_app.py](../../run_app.py) | 16 |
| [src/__init__.py](../../src/__init__.py) | 0 |
| [src/common/__init__.py](../../src/common/__init__.py) | 0 |
| [src/common/common_data.py](../../src/common/common_data.py) | 14 |
| [src/common/display_units.py](../../src/common/display_units.py) | 3 |
| [src/common/input_validation.py](../../src/common/input_validation.py) | 1 |
| [src/common/physical_constants.py](../../src/common/physical_constants.py) | 2 |
| [src/common/progress.py](../../src/common/progress.py) | 5 |
| [src/common/result_io.py](../../src/common/result_io.py) | 2 |
| [src/functions/__init__.py](../../src/functions/__init__.py) | 0 |
| [src/functions/feed_design.py](../../src/functions/feed_design.py) | 6 |
| [src/functions/fh2o_fortran.py](../../src/functions/fh2o_fortran.py) | 5 |
| [src/functions/gas_reactions.py](../../src/functions/gas_reactions.py) | 11 |
| [src/functions/math_utils.py](../../src/functions/math_utils.py) | 10 |
| [src/functions/reaction_rates.py](../../src/functions/reaction_rates.py) | 33 |
| [src/functions/rsc_design.py](../../src/functions/rsc_design.py) | 5 |
| [src/functions/steam_props.py](../../src/functions/steam_props.py) | 7 |
| [src/main.py](../../src/main.py) | 5 |
| [src/subroutines/__init__.py](../../src/subroutines/__init__.py) | 0 |
| [src/subroutines/gasifier_main.py](../../src/subroutines/gasifier_main.py) | 2 |
| [src/subroutines/initialization.py](../../src/subroutines/initialization.py) | 5 |
| [src/subroutines/mass_flow.py](../../src/subroutines/mass_flow.py) | 1 |
| [src/subroutines/output_results.py](../../src/subroutines/output_results.py) | 9 |
| [web_backend/__init__.py](../../web_backend/__init__.py) | 0 |
| [web_backend/app.py](../../web_backend/app.py) | 14 |
| [web_backend/dataparser.py](../../web_backend/dataparser.py) | 8 |

## app.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [parse_datain0](../../app.py#L163) | 函数/方法 | `parse_datain0(path)` | 解析 Datain0.dat，返回参数字典。 |
| [write_datain0](../../app.py#L184) | 函数/方法 | `write_datain0(path, params)` | 将参数字典写回 Datain0.dat。 |
| [_format_value](../../app.py#L218) | 函数/方法 | `_format_value(v)` | 格式化数值为 Fortran 风格。 |
| [parse_gastest](../../app.py#L229) | 函数/方法 | `parse_gastest(path)` | 解析 GASTEST.DAT，返回结构化结果字典。 |
| [_parse_float](../../app.py#L346) | 函数/方法 | `_parse_float(s)` | — |
| [_is_number](../../app.py#L353) | 函数/方法 | `_is_number(s)` | — |
| [calculate_wet_syngas](../../app.py#L361) | 函数/方法 | `calculate_wet_syngas(dry_flow, gas_profile_last)` | 根据干合成气体积流量和第30个cell的湿基气体组成，计算湿合成气组成。 |
| [_MockProcess](../../app.py#L405) | 类 | `_MockProcess()` | 用于模拟 subprocess.CompletedProcess 的简单容器。 |
| [_MockProcess.__init__](../../app.py#L407) | 函数/方法 | `__init__(self, returncode, stdout, stderr)` | — |
| [_run_simulation_direct](../../app.py#L413) | 函数/方法 | `_run_simulation_direct()` | 在 PyInstaller 打包环境中直接调用 src.main.main()。 |
| [run_simulation](../../app.py#L444) | 函数/方法 | `run_simulation()` | 调用 src/main.py 运行模拟（同步阻塞版本，保留兼容）。 |
| [_run_simulation_direct_async](../../app.py#L467) | 函数/方法 | `_run_simulation_direct_async()` | 在 PyInstaller 环境下于后台线程中直接运行 src.main.main()。 |
| [_run_simulation_direct_async.target](../../app.py#L471) | 函数/方法 | `target()` | — |
| [_run_simulation_direct_async.DirectHandle](../../app.py#L480) | 类 | `DirectHandle()` | — |
| [_run_simulation_direct_async.DirectHandle.done](../../app.py#L481) | 函数/方法 | `done(self)` | — |
| [_run_simulation_direct_async.DirectHandle.result](../../app.py#L484) | 函数/方法 | `result(self)` | — |
| [_run_simulation_direct_async.DirectHandle.terminate](../../app.py#L492) | 函数/方法 | `terminate(self)` | — |
| [_run_simulation_subprocess_async](../../app.py#L499) | 函数/方法 | `_run_simulation_subprocess_async()` | 以非阻塞子进程方式运行 src/main.py。 |
| [_run_simulation_subprocess_async.SubprocessHandle](../../app.py#L522) | 类 | `SubprocessHandle()` | — |
| [_run_simulation_subprocess_async.SubprocessHandle.done](../../app.py#L523) | 函数/方法 | `done(self)` | — |
| [_run_simulation_subprocess_async.SubprocessHandle.result](../../app.py#L526) | 函数/方法 | `result(self)` | — |
| [_run_simulation_subprocess_async.SubprocessHandle.terminate](../../app.py#L534) | 函数/方法 | `terminate(self)` | — |
| [run_simulation_async](../../app.py#L540) | 函数/方法 | `run_simulation_async()` | 在后台启动模拟，返回带 done()/result()/terminate() 接口的 handle。 |
| [rename_columns](../../app.py#L550) | 函数/方法 | `rename_columns(df, labels)` | 将 DataFrame 列名替换为中文标签。 |
| [style_dataframe](../../app.py#L555) | 函数/方法 | `style_dataframe(df, precision=4)` | 对 DataFrame 进行简单样式美化。 |
| [plot_line](../../app.py#L566) | 函数/方法 | `plot_line(df, x, y_list, title, y_title, color_map=None)` | 使用 Plotly 绘制交互式折线图。 |
| [plot_bar](../../app.py#L596) | 函数/方法 | `plot_bar(data_dict, title, y_title)` | 使用 Plotly 绘制柱状图。 |
| [main](../../app.py#L622) | 函数/方法 | `main()` | — |

## run_app.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [_LogFileWrapper](../../run_app.py#L50) | 类 | `_LogFileWrapper()` | 把输出同时写入日志文件；如果原流不可用则只写文件。 |
| [_LogFileWrapper.__init__](../../run_app.py#L53) | 函数/方法 | `__init__(self, name: str, orig_stream)` | — |
| [_LogFileWrapper.write](../../run_app.py#L67) | 函数/方法 | `write(self, s: str) -> int` | — |
| [_LogFileWrapper.flush](../../run_app.py#L81) | 函数/方法 | `flush(self) -> None` | — |
| [_LogFileWrapper.isatty](../../run_app.py#L93) | 函数/方法 | `isatty(self) -> bool` | — |
| [_LogFileWrapper.fileno](../../run_app.py#L96) | 函数/方法 | `fileno(self) -> int` | — |
| [_show_error_box](../../run_app.py#L109) | 函数/方法 | `_show_error_box(message: str) -> None` | 在 Windows 窗体模式下弹出错误对话框，让用户直接看到致命错误。 |
| [log](../../run_app.py#L121) | 函数/方法 | `log(msg: str) -> None` | 同时输出到 stdout（已被重定向到日志文件）和原 stderr。 |
| [log_exception](../../run_app.py#L128) | 函数/方法 | `log_exception(exc: BaseException) -> None` | 记录异常信息到日志。 |
| [_global_excepthook](../../run_app.py#L135) | 函数/方法 | `_global_excepthook(exc_type, exc_value, exc_tb)` | — |
| [_threading_excepthook](../../run_app.py#L148) | 函数/方法 | `_threading_excepthook(args)` | — |
| [resolve_path](../../run_app.py#L166) | 函数/方法 | `resolve_path(path: str) -> str` | 解析 PyInstaller 临时目录或当前工作目录下的路径。 |
| [open_browser_when_ready](../../run_app.py#L172) | 函数/方法 | `open_browser_when_ready(url: str, timeout: float=15.0)` | 后台线程：等待 Streamlit 服务就绪后打开系统默认浏览器。 |
| [_patch_streamlit_for_pyinstaller](../../run_app.py#L186) | 函数/方法 | `_patch_streamlit_for_pyinstaller()` | PyInstaller onefile 模式下修复 streamlit 运行环境： |
| [_patch_streamlit_for_pyinstaller._patched_get_static_dir](../../run_app.py#L207) | 函数/方法 | `_patched_get_static_dir() -> str` | — |
| [main](../../run_app.py#L229) | 函数/方法 | `main() -> int` | — |

## src/common/common_data.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [CommonData](../../src/common/common_data.py#L10) | 类 | `CommonData()` | 单例类，用于存储全局共享数据，对应Fortran的Common块 |
| [CommonData.__new__](../../src/common/common_data.py#L19) | 函数/方法 | `__new__(cls)` | — |
| [CommonData.reset](../../src/common/common_data.py#L25) | 函数/方法 | `reset(self)` | 原位清空计算状态，保留所有模块持有的单例引用。 |
| [CommonData.__init__](../../src/common/common_data.py#L31) | 函数/方法 | `__init__(self)` | — |
| [CommonData.init_parameters](../../src/common/common_data.py#L48) | 函数/方法 | `init_parameters(self)` | Common.00 - 基本参数 |
| [CommonData.init_structure](../../src/common/common_data.py#L53) | 函数/方法 | `init_structure(self)` | Common.00 - 结构参数和控制变量 |
| [CommonData.init_geometry](../../src/common/common_data.py#L113) | 函数/方法 | `init_geometry(self)` | Common.01 - 几何参数 |
| [CommonData.init_coal](../../src/common/common_data.py#L131) | 函数/方法 | `init_coal(self)` | Common.01 - 煤性质和操作参数 |
| [CommonData.init_unknowns](../../src/common/common_data.py#L182) | 函数/方法 | `init_unknowns(self)` | Common.02 - 求解变量 |
| [CommonData.init_flow](../../src/common/common_data.py#L198) | 函数/方法 | `init_flow(self)` | Common.02 - 流动参数 |
| [CommonData.init_feed](../../src/common/common_data.py#L207) | 函数/方法 | `init_feed(self)` | Common.02 - 进料参数 |
| [CommonData.init_volatile](../../src/common/common_data.py#L225) | 函数/方法 | `init_volatile(self)` | Common.02 - 挥发分释放 |
| [CommonData.init_enthalpy](../../src/common/common_data.py#L249) | 函数/方法 | `init_enthalpy(self)` | Common.02 - 焓值相关 |
| [CommonData.init_matrix](../../src/common/common_data.py#L287) | 函数/方法 | `init_matrix(self)` | Common.03 - 矩阵 |

## src/common/display_units.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [display_spec](../../src/common/display_units.py#L5) | 函数/方法 | `display_spec(unit)` | display = model * scale + offset。 |
| [to_display](../../src/common/display_units.py#L14) | 函数/方法 | `to_display(value, unit)` | — |
| [to_model](../../src/common/display_units.py#L19) | 函数/方法 | `to_model(value, unit)` | — |

## src/common/input_validation.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [validate_params](../../src/common/input_validation.py#L5) | 函数/方法 | `validate_params(params)` | 拒绝非有限数、非整数控制量和会导致除零/越界的输入。 |

## src/common/physical_constants.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [molar_masses](../../src/common/physical_constants.py#L35) | 函数/方法 | `molar_masses(legacy=False)` | — |
| [configure](../../src/common/physical_constants.py#L43) | 函数/方法 | `configure(common)` | 解析KMODEL后、计算进料源项之前统一选择常数；保留1-based气体数组约定。 |

## src/common/progress.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [set_progress_file](../../src/common/progress.py#L24) | 函数/方法 | `set_progress_file(path: os.PathLike) -> None` | 设置进度文件路径（主要用于测试）。 |
| [get_progress_file](../../src/common/progress.py#L30) | 函数/方法 | `get_progress_file() -> Path` | 获取当前进度文件路径。 |
| [write_progress](../../src/common/progress.py#L35) | 函数/方法 | `write_progress(iteration: int, max_iterations: int, residuals: Optional[Dict[str, float]]=None, status: str='running', message: str='') -> None` | 写入当前模拟进度到 JSON 文件。 |
| [read_progress](../../src/common/progress.py#L80) | 函数/方法 | `read_progress(path: Optional[os.PathLike]=None) -> Optional[Dict]` | 读取进度文件内容。 |
| [clear_progress](../../src/common/progress.py#L97) | 函数/方法 | `clear_progress(path: Optional[os.PathLike]=None) -> None` | 清除进度文件。 |

## src/common/result_io.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [read_result_text](../../src/common/result_io.py#L5) | 函数/方法 | `read_result_text(path)` | 新输出固定 UTF-8；仍支持历史 Windows GBK 文件。 |
| [parse_outlet](../../src/common/result_io.py#L14) | 函数/方法 | `parse_outlet(text)` | — |

## src/functions/feed_design.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [search_feed](../../src/functions/feed_design.py#L7) | 函数/方法 | `search_feed(evaluate, target_temperature, target_flow, initial, lower, upper, temperature_tolerance=0.5, flow_relative_tolerance=0.001, max_evaluations=40)` | 以 ln(氧煤比)、ln(水煤浆量) 为变量；有限差分雅可比与回溯控制步长。 |
| [search_feed.sample](../../src/functions/feed_design.py#L20) | 函数/方法 | `sample(x)` | — |
| [search_feed.finish](../../src/functions/feed_design.py#L33) | 函数/方法 | `finish(success, message)` | — |
| [run_feed_design](../../src/functions/feed_design.py#L94) | 函数/方法 | `run_feed_design(output_file, data_path, iterate)` | 完整重建每轮进料源项；只有双目标及可选废锅设计全部通过才写 START。 |
| [run_feed_design.outlet](../../src/functions/feed_design.py#L108) | 函数/方法 | `outlet()` | — |
| [run_feed_design.evaluate](../../src/functions/feed_design.py#L112) | 函数/方法 | `evaluate(oxy, slurry)` | — |

## src/functions/fh2o_fortran.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [cmp_fortran](../../src/functions/fh2o_fortran.py#L77) | 函数/方法 | `cmp_fortran(A, B, C, D, T, T0)` | Fortran CMP函数 - 计算热容积分 |
| [cmpt_fortran](../../src/functions/fh2o_fortran.py#L91) | 函数/方法 | `cmpt_fortran(A, B, C, D, T, T0)` | Fortran CMPT函数 - 计算熵积分 |
| [fpart_fortran](../../src/functions/fh2o_fortran.py#L106) | 函数/方法 | `fpart_fortran(A, B, C, D, E, F, G, T)` | Fortran FPART函数 - 计算饱和蒸汽压 |
| [fh2o_fortran_complete](../../src/functions/fh2o_fortran.py#L115) | 函数/方法 | `fh2o_fortran_complete(temp, ppp, x, iagg, kalzg)` | 完整的Fortran FH2O函数移植 |
| [test_fh2o](../../src/functions/fh2o_fortran.py#L290) | 函数/方法 | `test_fh2o()` | 测试FH2O函数 |

## src/functions/gas_reactions.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [xk1](../../src/functions/gas_reactions.py#L26) | 函数/方法 | `xk1(i)` | CO + 1/2 O2 -> CO2 反应速率 |
| [xk2](../../src/functions/gas_reactions.py#L71) | 函数/方法 | `xk2(i)` | H2 + 1/2 O2 -> H2O 反应速率 |
| [xk3](../../src/functions/gas_reactions.py#L116) | 函数/方法 | `xk3(i)` | CO + H2O -> CO2 + H2 水煤气变换反应速率 |
| [xk4](../../src/functions/gas_reactions.py#L161) | 函数/方法 | `xk4(i)` | CO2 + H2 -> CO + H2O 逆水煤气变换反应速率 |
| [xk5](../../src/functions/gas_reactions.py#L202) | 函数/方法 | `xk5(i)` | CH4 + H2O -> CO + 3H2 蒸汽重整反应速率 |
| [xk6](../../src/functions/gas_reactions.py#L246) | 函数/方法 | `xk6(i)` | CH4 + 2 O2 -> CO2 + 2H2O 反应速率 |
| [flucht](../../src/functions/gas_reactions.py#L291) | 函数/方法 | `flucht()` | 挥发分释放计算子程序 |
| [_flucht_balance_h_o](../../src/functions/gas_reactions.py#L467) | 函数/方法 | `_flucht_balance_h_o(vh2ok1, vh2ok2, vtark1, vtark2, rvh2o1, rvtar1, rco1, rco21, rvch41, rvh21, rh2_total, rh2s_total, ro2_total, fak1, fak2, fak3, fak4)` | H和O元素都不足时的平衡计算 |
| [_flucht_901](../../src/functions/gas_reactions.py#L562) | 函数/方法 | `_flucht_901(rvch41, rvh21, rvh2o1, rco1, rco21, rvtar1)` | H和O元素都有剩余时的处理 |
| [_flucht_902](../../src/functions/gas_reactions.py#L575) | 函数/方法 | `_flucht_902(rh2s_total, ren2_total, rh2_total, ro2_total, prc, prh, pro, prn, prs)` | 无挥发分时的处理 - 只计算元素释放 |
| [_flucht_distribute](../../src/functions/gas_reactions.py#L597) | 函数/方法 | `_flucht_distribute(rvch41, rvh21, rvh2o1, rco1, rco21, rvtar1, rh2s_total, ren2_total, rh2_total, ro2_total, prc, prh, pro, prn, prs)` | 将挥发分释放分配到各格子 |

## src/functions/math_utils.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [gausll](../../src/functions/math_utils.py#L16) | 函数/方法 | `gausll(n, ns, a)` | 高斯消元法求解线性方程组 (改进版 - 增强数值稳定性) |
| [matadd](../../src/functions/math_utils.py#L110) | 函数/方法 | `matadd(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2)` | 矩阵加法: MATOUT = MATIN1 + MATIN2 |
| [matsub](../../src/functions/math_utils.py#L137) | 函数/方法 | `matsub(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2)` | 矩阵减法: MATOUT = MATIN1 - MATIN2 |
| [matmult](../../src/functions/math_utils.py#L175) | 函数/方法 | `matmult(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2)` | 矩阵乘法: MATOUT = MATIN1 * MATIN2 |
| [matdiv](../../src/functions/math_utils.py#L256) | 函数/方法 | `matdiv(nf, ng, matin1, nan1x, matin2, nan2x, ndi1, ndi2)` | 矩阵除法: MATOUT = MATIN1 / MATIN2 |
| [matums](../../src/functions/math_utils.py#L355) | 函数/方法 | `matums(nf, nmat, matin1, nmat1, nx1, mx1, nmat2, nxu1)` | 矩阵复制: MATOUT = MATIN1 |
| [kolon1](../../src/functions/math_utils.py#L377) | 函数/方法 | `kolon1(omega=1.0)` | 更新求解变量，检查收敛性 |
| [newtra](../../src/functions/math_utils.py#L550) | 函数/方法 | `newtra(omega=1.0)` | 牛顿迭代 |
| [solve_banded_blocks](../../src/functions/math_utils.py#L579) | 函数/方法 | `solve_banded_blocks(nmat, nst)` | 将 Fortran 1-based 块三对角矩阵交给 SciPy 的 LAPACK 带状求解器。 |
| [blktrd](../../src/functions/math_utils.py#L614) | 函数/方法 | `blktrd(nmat, nst)` | 块三对角矩阵求解? |

## src/functions/reaction_rates.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [TPAR](../../src/functions/reaction_rates.py#L25) | 函数/方法 | `TPAR(I: int) -> float` | 计算颗粒温度 (Particle Temperature) |
| [PHI](../../src/functions/reaction_rates.py#L59) | 函数/方法 | `PHI(I: int) -> float` | 机械因子/结构参数 (Mechanical Factor) |
| [XKC_O2](../../src/functions/reaction_rates.py#L92) | 函数/方法 | `XKC_O2(I: int) -> float` | 计算碳与氧气反应的速率系数 |
| [XKC_H2O](../../src/functions/reaction_rates.py#L152) | 函数/方法 | `XKC_H2O(I: int) -> float` | 计算碳与水蒸气反应的速率系数 |
| [XKC_CO2](../../src/functions/reaction_rates.py#L208) | 函数/方法 | `XKC_CO2(I: int) -> float` | 计算碳与二氧化碳反应的速率系数 |
| [XKC_H2](../../src/functions/reaction_rates.py#L264) | 函数/方法 | `XKC_H2(I: int) -> float` | 计算碳与氢气反应的速率系数 |
| [_update_gas_fractions](../../src/functions/reaction_rates.py#L316) | 函数/方法 | `_update_gas_fractions(I: int) -> None` | 更新气体组分摩尔分数 Y[1:9] |
| [A1](../../src/functions/reaction_rates.py#L329) | 函数/方法 | `A1(I: int) -> float` | 计算碳与水蒸气反应速率 |
| [A2](../../src/functions/reaction_rates.py#L372) | 函数/方法 | `A2(I: int) -> float` | 计算碳与氢气反应速率 (甲烷化反应) |
| [A3](../../src/functions/reaction_rates.py#L416) | 函数/方法 | `A3(I: int) -> float` | 计算碳与氧气反应速率 (燃烧反应) |
| [A4](../../src/functions/reaction_rates.py#L447) | 函数/方法 | `A4(I: int) -> float` | 计算碳与二氧化碳反应速率 (Boudouard反应) |
| [A5](../../src/functions/reaction_rates.py#L476) | 函数/方法 | `A5(I: int) -> float` | 计算催化水煤气变换反应速率 |
| [RI](../../src/functions/reaction_rates.py#L528) | 函数/方法 | `RI(I: int) -> float` | 计算总碳消耗速率 |
| [CMP](../../src/functions/reaction_rates.py#L554) | 函数/方法 | `CMP(A: float, B: float, C: float, D: float, T: float, T0: float) -> float` | 计算热容积分 (用于气体组分) |
| [CMP_SOLID](../../src/functions/reaction_rates.py#L578) | 函数/方法 | `CMP_SOLID(A: float, B: float, C: float, D: float, T: float, T0: float) -> float` | 计算热容积分 (与Fortran CMP函数一致) |
| [CMPS](../../src/functions/reaction_rates.py#L609) | 函数/方法 | `CMPS(A: float, B: float, C: float, D: float, T: float, T0: float) -> float` | 计算热容积分 (H2S专用) |
| [CMPT](../../src/functions/reaction_rates.py#L634) | 函数/方法 | `CMPT(A: float, B: float, C: float, D: float, T: float, T0: float) -> float` | 计算热容除以温度的积分 (用于气体组分) |
| [CMPT_SOLID](../../src/functions/reaction_rates.py#L658) | 函数/方法 | `CMPT_SOLID(A: float, B: float, C: float, D: float, T: float, T0: float) -> float` | 计算热容除以温度的积分 (用于固体组分，与Fortran CMPT一致) |
| [FPART](../../src/functions/reaction_rates.py#L677) | 函数/方法 | `FPART(A: float, B: float, C: float, D: float, E: float, F: float, G: float, T: float) -> float` | 计算分压 |
| [FH2](../../src/functions/reaction_rates.py#L697) | 函数/方法 | `FH2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算H2的热力学性质 |
| [FSOLID](../../src/functions/reaction_rates.py#L755) | 函数/方法 | `FSOLID(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算固体灰分的热力学性质 |
| [FH2S](../../src/functions/reaction_rates.py#L802) | 函数/方法 | `FH2S(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算H2S的热力学性质 |
| [FO2](../../src/functions/reaction_rates.py#L834) | 函数/方法 | `FO2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算O2的热力学性质 |
| [FC](../../src/functions/reaction_rates.py#L892) | 函数/方法 | `FC(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算固体碳(C)的热力学性质 |
| [FN2](../../src/functions/reaction_rates.py#L941) | 函数/方法 | `FN2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算N2的热力学性质 |
| [FCO2](../../src/functions/reaction_rates.py#L999) | 函数/方法 | `FCO2(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算CO2的热力学性质 |
| [FCO](../../src/functions/reaction_rates.py#L1039) | 函数/方法 | `FCO(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算CO的热力学性质 |
| [FCH4](../../src/functions/reaction_rates.py#L1098) | 函数/方法 | `FCH4(TEMP: float, PP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算CH4的热力学性质 |
| [FH2O](../../src/functions/reaction_rates.py#L1138) | 函数/方法 | `FH2O(TEMP: float, PPP: float, X: float, IAGG: str, KALZG: str) -> float` | 计算H2O的热力学性质 (Fortran 完整移植版本) |
| [ENTHP](../../src/functions/reaction_rates.py#L1165) | 函数/方法 | `ENTHP(KOMP: int, IAGG: str, T: float, P: float) -> float` | 焓值计算分发函数 |
| [ENTHP_DELTA](../../src/functions/reaction_rates.py#L1209) | 函数/方法 | `ENTHP_DELTA(KOMP: int, IAGG: str, T: float, T_REF: float, P: float) -> float` | 计算相对于参考温度的焓值差 |
| [WDKR](../../src/functions/reaction_rates.py#L1232) | 函数/方法 | `WDKR(T: float, TW: float) -> float` | 计算辐射换热系数 |
| [FXMUG](../../src/functions/reaction_rates.py#L1253) | 函数/方法 | `FXMUG(Y_array: np.ndarray, T: float) -> float` | 计算气体混合物粘度 |

## src/functions/rsc_design.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [search_height](../../src/functions/rsc_design.py#L7) | 函数/方法 | `search_height(evaluate, target, initial, lower, upper, tolerance=0.5, max_evaluations=18)` | 有界扩展 + 保守割线搜索；仅接受内层收敛且温差满足容差的候选。 |
| [search_height.sample](../../src/functions/rsc_design.py#L11) | 函数/方法 | `sample(height)` | — |
| [search_height.finish](../../src/functions/rsc_design.py#L19) | 函数/方法 | `finish(success, message)` | — |
| [run_target_design](../../src/functions/rsc_design.py#L51) | 函数/方法 | `run_target_design(output_file, iterate, finalize=True)` | 每个高度重算全炉；回收热量与蒸汽量始终取同一收敛状态。 |
| [run_target_design.evaluate](../../src/functions/rsc_design.py#L62) | 函数/方法 | `evaluate(height)` | — |

## src/functions/steam_props.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [_pressure](../../src/functions/steam_props.py#L11) | 函数/方法 | `_pressure(p_pa)` | — |
| [_saturation](../../src/functions/steam_props.py#L18) | 函数/方法 | `_saturation(p_pa)` | — |
| [tsat_water](../../src/functions/steam_props.py#L24) | 函数/方法 | `tsat_water(p_pa: float) -> float` | — |
| [h_sat_steam](../../src/functions/steam_props.py#L28) | 函数/方法 | `h_sat_steam(p_pa: float) -> float` | — |
| [latent_heat](../../src/functions/steam_props.py#L32) | 函数/方法 | `latent_heat(p_pa: float) -> float` | — |
| [h_feedwater](../../src/functions/steam_props.py#L38) | 函数/方法 | `h_feedwater(t_k: float, p_pa: float) -> float` | 给水压缩液焓；压力必填，禁止默认为大气压或忽略压力。 |
| [steam_production](../../src/functions/steam_props.py#L46) | 函数/方法 | `steam_production(q_w: float, p_drum_pa: float, t_fw_k: float) -> float` | 回收热负荷W / 汽水焓差J/kg → 饱和蒸汽kg/s。 |

## src/main.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [calculate_residuals](../../src/main.py#L23) | 函数/方法 | `calculate_residuals()` | 汇总线性求解后原始牛顿修正量的绝对值和，不是守恒残差。 |
| [print_matrices_iter0](../../src/main.py#L57) | 函数/方法 | `print_matrices_iter0()` | 打印第一次迭代前的矩阵（用于与Fortran对比） |
| [_run](../../src/main.py#L103) | 函数/方法 | `_run(output_file, data_path)` | TEXACO气化炉一维稳态模拟主程序 (残差输出版) |
| [_iterate](../../src/main.py#L129) | 函数/方法 | `_iterate(output_file, trial_label=None)` | 在当前几何上求解；设计迭代保留上轮收敛状态作为初值。 |
| [main](../../src/main.py#L227) | 函数/方法 | `main(data_path='data/Datain0.dat')` | 返回 0=收敛且目标满足，2=内层或设计未收敛；异常记录进度并抛出。 |

## src/subroutines/gasifier_main.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [_calculate_dmat_for_cell](../../src/subroutines/gasifier_main.py#L19) | 函数/方法 | `_calculate_dmat_for_cell(i, xmass_func, entfed_func, entkol_func, xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func, a1_func, a2_func, a3_func, a4_func, a5_func, phi_func, ri_func, enthp_func, wdkr_func=None)` | 计算单格缩放后的守恒残差R，暂存DMAT；gasifier末尾取负成为线性RHS。 |
| [gasifier](../../src/subroutines/gasifier_main.py#L435) | 函数/方法 | `gasifier(xmass_func, entfed_func, entkol_func, xk1_func, xk2_func, xk3_func, xk4_func, xk5_func, xk6_func, a1_func, a2_func, a3_func, a4_func, a5_func, phi_func, ri_func, enthp_func, wdkr_func=None)` | GASIFIER主计算子程序 |

## src/subroutines/initialization.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [eingab](../../src/subroutines/initialization.py#L20) | 函数/方法 | `eingab(data_path='data/Datain0.dat', output_file=None, overrides=None)` | 输入数据和初始化子程序 |
| [eingab.parse_line](../../src/subroutines/initialization.py#L49) | 函数/方法 | `parse_line(line)` | 解析数据行,提取数值 |
| [_read_start_file](../../src/subroutines/initialization.py#L419) | 函数/方法 | `_read_start_file(filepath)` | 从START.DAT读取初始值 |
| [geometry](../../src/subroutines/initialization.py#L451) | 函数/方法 | `geometry()` | 计算气化炉几何结构 |
| [qhcrct](../../src/subroutines/initialization.py#L604) | 函数/方法 | `qhcrct()` | 热量校正计算 |

## src/subroutines/mass_flow.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [xmass](../../src/subroutines/mass_flow.py#L11) | 函数/方法 | `xmass(cells=None)` | 计算每个小格的质量流量 |

## src/subroutines/output_results.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [RI](../../src/subroutines/output_results.py#L63) | 函数/方法 | `RI(i)` | 计算碳反应速率 (辅助函数) |
| [kolerg](../../src/subroutines/output_results.py#L78) | 函数/方法 | `kolerg(output_file=None, write_restart=True)` | 主输出子程序 - 将计算结果输出到文件 |
| [write_start](../../src/subroutines/output_results.py#L300) | 函数/方法 | `write_start(outfile)` | 写当前状态，是否已接受由调用者控制；本函数不检查KONVER。 |
| [entkol](../../src/subroutines/output_results.py#L330) | 函数/方法 | `entkol(cells=None, cache=None)` | 按各格当前T/P刷新气体摩尔焓、固体比焓和温度导数（不是煤入口焓）。 |
| [entfed](../../src/subroutines/output_results.py#L384) | 函数/方法 | `entfed()` | 计算进料焓 - 计算进料流股的焓值 |
| [tpar](../../src/subroutines/output_results.py#L440) | 函数/方法 | `tpar(i)` | 计算焦炭颗粒温度 (简化模型) |
| [tpar1](../../src/subroutines/output_results.py#L470) | 函数/方法 | `tpar1(i)` | 计算焦炭颗粒温度 (详细模型) |
| [kontr](../../src/subroutines/output_results.py#L534) | 函数/方法 | `kontr()` | 质量/能量平衡检查 - 计算进出系统的质量和能量流 |
| [hcrt](../../src/subroutines/output_results.py#L647) | 函数/方法 | `hcrt()` | 热校正 - 第一格子的初始能量检查 |

## web_backend/app.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [_is_running](../../web_backend/app.py#L74) | 函数/方法 | `_is_running() -> bool` | — |
| [_serialized_write](../../web_backend/app.py#L84) | 函数/方法 | `_serialized_write(func)` | 检查、参数写入和启动共用一把锁（单进程服务）。 |
| [_serialized_write.wrapped](../../web_backend/app.py#L87) | 函数/方法 | `wrapped(*args, **kwargs)` | — |
| [_update_params](../../web_backend/app.py#L98) | 函数/方法 | `_update_params()` | — |
| [_ordered_groups](../../web_backend/app.py#L119) | 函数/方法 | `_ordered_groups()` | — |
| [_grouped_params](../../web_backend/app.py#L130) | 函数/方法 | `_grouped_params(params)` | — |
| [index](../../web_backend/app.py#L141) | 函数/方法 | `index()` | — |
| [get_params](../../web_backend/app.py#L146) | 函数/方法 | `get_params()` | — |
| [set_params](../../web_backend/app.py#L160) | 函数/方法 | `set_params()` | — |
| [run_simulation](../../web_backend/app.py#L166) | 函数/方法 | `run_simulation()` | — |
| [get_progress](../../web_backend/app.py#L205) | 函数/方法 | `get_progress()` | — |
| [get_results](../../web_backend/app.py#L249) | 函数/方法 | `get_results()` | — |
| [get_output_raw](../../web_backend/app.py#L270) | 函数/方法 | `get_output_raw()` | — |
| [main](../../web_backend/app.py#L280) | 函数/方法 | `main()` | — |

## web_backend/dataparser.py

| 定义/源码 | 类型 | 签名 | 源码摘要 |
|---|---|---|---|
| [_parse_float](../../web_backend/dataparser.py#L188) | 函数/方法 | `_parse_float(s: str) -> float` | — |
| [_is_number](../../web_backend/dataparser.py#L195) | 函数/方法 | `_is_number(s: str) -> bool` | — |
| [_format_value](../../web_backend/dataparser.py#L203) | 函数/方法 | `_format_value(v: Any) -> str` | — |
| [parse_datain0](../../web_backend/dataparser.py#L213) | 函数/方法 | `parse_datain0(path: Path) -> Dict[str, Any]` | 解析 Datain0.dat，返回参数字典。 |
| [write_datain0](../../web_backend/dataparser.py#L240) | 函数/方法 | `write_datain0(path: Path, params: Dict[str, Any]) -> None` | 将参数字典写回 Datain0.dat。 |
| [parse_gastest](../../web_backend/dataparser.py#L285) | 函数/方法 | `parse_gastest(path: Path) -> Optional[Dict[str, Any]]` | 解析 GASTEST.DAT，返回结构化结果字典。 |
| [parse_outlet_sections](../../web_backend/dataparser.py#L424) | 函数/方法 | `parse_outlet_sections(text, result)` | 读取 KOLERG 的两出口对照表；只用本次输出，不混用当前输入参数。 |
| [calculate_wet_syngas](../../web_backend/dataparser.py#L485) | 函数/方法 | `calculate_wet_syngas(dry_flow: Dict[str, float], gas_profile_last: Dict[str, float])` | 根据干合成气体积流量和最后一个 cell 的湿基气体组成计算湿合成气。 |
