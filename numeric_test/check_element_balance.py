"""进口/燃烧室/废锅独立元素衡算；所有求解都在隔离目录。

只读取完整精度状态，不调用 KONTR 或由干基百分比反推质量。
运行：python numeric_test/check_element_balance.py --output numeric_test/python_output/element-balance
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS = ('C', 'H', 'O', 'N', 'S', 'Ash')
GASES = ('O2', 'CH4', 'CO', 'CO2', 'H2S', 'H2', 'N2', 'H2O')
# kg元素/kmol分子。原模型整数原子量 C=12,H=1,O=16,N=14,S=32。
ELEMENT_MATRIX = np.array([
    [0, 12, 12, 12, 0, 0, 0, 0],
    [0, 4, 0, 0, 2, 2, 0, 2],
    [32, 0, 16, 32, 0, 0, 0, 16],
    [0, 0, 0, 0, 0, 0, 28, 0],
    [0, 0, 0, 0, 32, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
], dtype=float)


def _atomic(state):
    # 状态文件明确保存运行所用原子量；历史文件没有该字段则用旧整数基准。
    return np.array([float(state.get(k, old)) for k, old in zip(
        ('MC', 'MH', 'MO', 'MN', 'MS'), (12., 1., 16., 14., 32.))])


def elemental_stream(gas_kmol_s, solid_kg_s=0.0, carbon_fraction=0.0, atoms=None):
    """气相全部八组分＋固体残碳/灰，返回六项 kg/h。"""
    matrix = ELEMENT_MATRIX.copy()
    if atoms is not None:
        matrix[:5] *= (np.asarray(atoms) / np.array([12., 1., 16., 14., 32.]))[:, None]
    result = matrix @ np.asarray(gas_kmol_s, dtype=float)
    result[0] += solid_kg_s * carbon_fraction
    result[5] += solid_kg_s * (1 - carbon_fraction)
    return result * 3600


def inlet_components(state):
    """物理进料独立核算：原煤元素、水煤浆水、氧化剂/稀释气。

    保留输入煤分析基准，不归一化；ELH2O 的水单独分配给 H/O。
    各燃烧室进料点一并计入，冷却水/副产蒸汽属于独立公用工程侧。
    """
    atoms = _atomic(state)
    mc, mh, mo, mn, ms = atoms
    coal = float(state['BSLURRY'] * state['RATIO_COAL'])
    coal_elements = coal * np.array([float(state[k]) for k in ('ELC', 'ELH', 'ELO', 'ELN', 'ELS', 'ELAS')]) * 3600
    water = float(state['BSLURRY'] * (1 - state['RATIO_COAL']) + coal * state['ELH2O'])
    water_gas = np.zeros(8)
    water_gas[7] = water / (2*mh + mo)
    oxidant_gas = np.zeros(8)
    # 从输入氧煤比、纯度和分析值计算总物理进料，独立于源项分配数组。
    pure_o2 = float(state['FOXY']) * coal * (1 - float(state['ELH2O']) - float(state['ELAS'])) / (2*mo)
    oxygen_stream = pure_o2 / float(state['PURE_O2'])
    oxidant_gas[0] = pure_o2
    oxidant_gas[6] = oxygen_stream * (1 - float(state['PURE_O2']))
    oxidant_gas[3] = oxygen_stream * float(state['RATIO_CO2'])
    return {'coal': coal_elements, 'water': elemental_stream(water_gas, atoms=atoms),
            'oxidant_and_co2': elemental_stream(oxidant_gas, atoms=atoms)}


def total_mass_ledger(state):
    """直接按物料流核算总质量，独立检查煤分析闭合与运行摩尔质量。"""
    mc, mh, mo, mn, ms = _atomic(state)
    slurry = float(state['BSLURRY'])
    coal = slurry * float(state['RATIO_COAL'])
    oxygen = float(state['FOXY']) * coal * (1 - float(state['ELH2O']) - float(state['ELAS']))
    oxidant_kmol_s = oxygen / (2 * mo) / float(state['PURE_O2'])
    nitrogen = oxidant_kmol_s * (1 - float(state['PURE_O2'])) * (2 * mn)
    co2 = oxidant_kmol_s * float(state['RATIO_CO2']) * (mc + 2 * mo)
    inlet_parts = dict(slurry=slurry * 3600, oxygen=oxygen * 3600,
                       oxidant_nitrogen=nitrogen * 3600, dilution_co2=co2 * 3600)
    masses = np.asarray(state['XMOL'][:8], dtype=float)
    expected_masses = np.array([2*mo, mc+4*mh, mc+mo, mc+2*mo,
                               2*mh+ms, 2*mh, 2*mn, 2*mh+mo])
    totals = dict(inlet=sum(inlet_parts.values()))
    outlet_parts = {}
    for name, index in (('chamber', int(state['NZRC'])), ('rsc', int(state['NZRE']))):
        gas = float(state['FEMF'][1:9, index] @ masses) * 3600
        solid = float(state['WE'][index]) * 3600
        carbon = solid * float(state['X'][index])
        outlet_parts[name] = dict(wet_gas=gas, solid=solid, residual_carbon=carbon, ash=solid-carbon)
        totals[name] = gas + solid
    tolerance = max(1e-6, abs(totals['inlet']) * 1e-8)
    comparisons = {}
    for upstream, downstream in (('inlet', 'chamber'), ('chamber', 'rsc'), ('inlet', 'rsc')):
        delta = totals[downstream] - totals[upstream]
        comparisons[f'{upstream}_to_{downstream}'] = dict(delta_kg_h=delta,
            relative_percent=delta / totals[upstream] * 100 if totals[upstream] else None,
            passed=bool(abs(delta) <= tolerance))
    analysis_sum = sum(float(state[k]) for k in ('ELC', 'ELH', 'ELO', 'ELN', 'ELS', 'ELAS', 'ELH2O'))
    analysis_gap = coal * (analysis_sum - 1) * 3600
    return dict(total_mass_kg_h=totals, inlet_mass_components_kg_h=inlet_parts,
        outlet_mass_components_kg_h=outlet_parts, mass_tolerance_kg_h=tolerance,
        mass_comparisons=comparisons,
        coal_analysis=dict(sum=analysis_sum, mass_gap_kg_h=analysis_gap, passed=bool(abs(analysis_gap) <= tolerance)),
        molar_mass_check=dict(max_error_kg_kmol=float(np.max(np.abs(masses-expected_masses))),
                             passed=bool(np.allclose(masses, expected_masses, rtol=0, atol=1e-12))))


def rsc_rates(state):
    """按收敛气体组成独立重算 RSC 源项，正号为反应式正向。"""
    rates = []
    for cell in range(int(state['NZRC']) + 1, int(state['NZRE']) + 1):
        gas = state['FEMF'][1:9, cell]
        total = float(gas.sum())
        y = gas / total
        temperature = max(float(state['T'][cell]), 500.0)
        kw = np.exp(4577.8 / temperature - 4.33)
        km = np.exp(24766 / temperature - 25.82)
        rw = float(state['KRELAX_WGS']) * (y[2] * y[7] - y[3] * y[5] / max(kw, 1e-30)) * total
        rm = float(state['KRELAX_METH']) * (y[2] * y[5] ** 3 - y[1] * y[7] /
             max(km * (float(state['PWK']) / float(state['P0'])) ** 2, 1e-30)) * total
        rates.append((cell, float(rw), float(rm)))
    return rates


def ledger(state, *, consistent_scaling=True):
    """输出逐格元素流及三截面差值；审计容差与求解器容差相互独立。"""
    if int(state['KMODEL']) != 1 or int(state['KCHECK']) != 0:
        raise ValueError('此实验针对晋华炉正常模式 KMODEL=1、KCHECK=0')
    atoms = _atomic(state)
    inputs = inlet_components(state)
    inlet = sum(inputs.values())
    flows = np.array([elemental_stream(state['FEMF'][1:9, i], state['WE'][i], state['X'][i], atoms)
                      for i in range(1, int(state['NZRE']) + 1)])
    chamber = flows[int(state['NZRC']) - 1]
    outlet = flows[-1]
    tolerance = np.maximum(1e-6, np.abs(inlet) * 1e-8)  # kg/h；相对0.000001%
    comparisons = {}
    for name, upstream, downstream in (('inlet_to_chamber', inlet, chamber),
            ('chamber_to_rsc', chamber, outlet), ('inlet_to_rsc', inlet, outlet)):
        delta = downstream - upstream
        comparisons[name] = dict(delta_kg_h=delta.tolist(),
            relative_percent=[float(d / u * 100) if u != 0 else None for d, u in zip(delta, upstream)],
            passed_by_element=(np.abs(delta) <= tolerance).tolist(),
            passed=bool(np.all(np.abs(delta) <= tolerance)))
    rates = rsc_rates(state)
    sw, sm = sum(r[1] for r in rates), sum(r[2] for r in rates)
    # 原实现：CO2 基础方程 /1.2 后再加 rw；H2 基础方程 *1.02 后再加 rw-3rm。
    predicted = np.zeros(6) if consistent_scaling else np.array([atoms[0] * .2 * sw, 2*atoms[1] * (1/1.02 - 1) * (sw - 3*sm), 2*atoms[2] * .2 * sw, 0, 0, 0]) * 3600
    rows = []
    for i, flow in enumerate(flows, 1):
        previous = inlet if i == 1 else flows[i-2]
        # 第1格尚未加入二次氧；仅把31..NZRE的逐格差用于RSC无进料诊断。
        rows.append(dict(cell=i, elements_kg_h=flow.tolist(),
                         adjacent_delta_kg_h=(flow-previous).tolist()))
    mass = total_mass_ledger(state)
    passed = (all(item['passed'] for item in comparisons.values())
              and all(item['passed'] for item in mass['mass_comparisons'].values())
              and mass['coal_analysis']['passed'] and mass['molar_mass_check']['passed'])
    return dict(elements=list(ELEMENTS), units='kg/h', atomic_weights=dict(zip(ELEMENTS[:5], atoms.tolist())),
        input_components_kg_h={k:v.tolist() for k,v in inputs.items()}, inlet_kg_h=inlet.tolist(),
        chamber_kg_h=chamber.tolist(), rsc_kg_h=outlet.tolist(),
        chamber_temperature_c=float(state['T'][int(state['NZRC'])]-273.15),
        rsc_temperature_c=float(state['T'][int(state['NZRE'])]-273.15),
        tolerance_kg_h=tolerance.tolist(), comparisons=comparisons,
        **mass, balance_passed=passed,
        sum_rsc_wgs_kmol_s=sw, sum_rsc_meth_kmol_s=sm,
        predicted_scaling_defect_kg_h=predicted.tolist(),
        prediction_gap_kg_h=(outlet-chamber-predicted).tolist(), cells=rows,
        rsc_rates=[dict(cell=i, wgs_kmol_s=w, meth_kmol_s=m) for i,w,m in rates])


def run_case(name, source, destination, original_input, updates, backend='scipy', *, allow_nonconverged=False):
    sys.path.insert(0, str(ROOT))
    from web_backend.dataparser import parse_datain0, write_datain0
    folder = destination / name
    folder.mkdir(parents=True, exist_ok=True)
    datain = folder / 'Datain0.dat'
    datain.write_bytes(original_input.read_bytes())
    params = parse_datain0(datain)
    params.update(KTRL=1, FEED_MODE=0, RSC_MODE=0)
    params.update(updates)
    write_datain0(datain, params)
    with (folder / 'run.log').open('w', encoding='utf-8') as log:
        subprocess.run([sys.executable, str(ROOT/'numeric_test/benchmark_solver.py'), '--worker',
            '--source', str(source), '--output', str(folder)], stdout=log, stderr=log, check=True,
            env={**os.environ, 'PYTHONIOENCODING':'utf-8', 'TEXACO_LINEAR_SOLVER':backend}, timeout=1800)
    timing = json.loads((folder/'timing.json').read_text(encoding='utf-8'))
    with np.load(folder/'state.npz') as state:
        result = ledger(state)
        solved = {k: float(state[k]) for k in ('BSLURRY', 'FOXY', 'H_RSC')}
    result.update(case=name, timing=timing, linear_backend=backend, input_parameters=params,
                  solved_parameters=solved, solver_success=timing['returncode'] == 0,
                  accepted=timing['returncode'] == 0 and result['balance_passed'])
    (folder/'element_balance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(case=name, solver_success=result['solver_success'], accepted=result['accepted'],
        iterations=timing['iterations'], seconds=round(timing['seconds'], 2),
        max_mass_delta_kg_h=max(abs(c['delta_kg_h']) for c in result['mass_comparisons'].values()),
        max_element_delta_kg_h=max(abs(d) for c in result['comparisons'].values() for d in c['delta_kg_h'])),
        ensure_ascii=False), flush=True)
    if not result['solver_success'] and not allow_nonconverged:
        raise RuntimeError(f'{name} 求解失败，状态仅供诊断：{folder}')
    return result


def expanded_variants(params):
    """围绕输入工况改变负荷、煤质、氧气、几何、压力及计算模式。"""
    wet = {k: params[k] * .95 / (1-params['ELH2O'])
           for k in ('ELC', 'ELH', 'ELO', 'ELN', 'ELS', 'ELAS')}
    wet['ELH2O'] = .05
    return {
        'current-input': {k: params[k] for k in ('RSC_MODE', 'FEED_MODE')},
        'baseline': {},
        'low-load': dict(BSLURRY=10),
        'high-load': dict(BSLURRY=18),
        'oxygen-lean': dict(FOXY=.92),
        'oxygen-rich': dict(FOXY=1.04),
        'slurry-dilute': dict(RATIO_COAL=.55),
        'slurry-dense': dict(RATIO_COAL=.65),
        'oxygen-95': dict(PURE_O2=.95),
        'secondary-co2': dict(OX_PART=.75, RATIO_CO2=.1),
        'wet-coal-5': wet,
        'sulfur-2': dict(ELS=.02, ELC=params['ELC']+params['ELS']-.02),
        'ash-20': dict(ELAS=.2, ELC=params['ELC']+params['ELAS']-.2),
        'rsc-short': dict(H_RSC=15),
        'rsc-tall': dict(H_RSC=60),
        'rsc-one': dict(N_RSC=1),
        'rsc-ten': dict(N_RSC=10),
        'no-rsc-relax': dict(KRELAX_WGS=0, KRELAX_METH=0),
        'low-pressure': dict(PWK=4.1e6),
        'high-pressure': dict(PWK=8.1e6, PFEED_SL=9.1e6, PFEED_O2=9.1e6, PFEED_CO2=9.1e6),
        'combined-design': dict(FEED_MODE=1, T_CHAMBER_C=1250, EFFECTIVE_GAS_NMH=55000,
                                RSC_MODE=1, T_RSC_OUT_C=780),
        'zero-volatiles': dict(XVM=0),
    }


def run_experiment(destination, input_path, selected=None, *, suite='standard', max_iterations=None):
    destination.mkdir(parents=True, exist_ok=True)
    # 固定输入快照，批量运行中界面改参也不会改变后续试算的基线。
    snapshot = destination / 'source_input.dat'
    snapshot.write_bytes(input_path.read_bytes())
    sys.path.insert(0, str(ROOT))
    from web_backend.dataparser import parse_datain0
    params = parse_datain0(snapshot)
    wet_coal = {k:v*.98 for k,v in dict(ELC=.6802, ELH=.0404, ELO=.0985, ELN=.0249, ELS=.006, ELAS=.15).items()}
    wet_coal['ELH2O'] = .02
    variants = {
        'baseline': {},
        'tighter': dict(ITMAX=200, SKONFE=1e-8, SKONWE=1e-8, SKONX=1e-8, SKONT=1e-5),
        'legacy': {},
        'no-rsc-relax': dict(KRELAX_WGS=0, KRELAX_METH=0),
        'secondary-co2': dict(OX_PART=.9, RATIO_CO2=.05),
        'wet-coal': wet_coal,
        'zero-volatiles': dict(XVM=0),
        'rsc-one': dict(N_RSC=1),
    }
    if suite == 'expanded':
        variants = expanded_variants(params)
    names = selected or [n for n in variants if suite == 'expanded' or n != 'zero-volatiles']
    unknown = set(names) - variants.keys()
    if unknown:
        raise ValueError(f'未知工况 {sorted(unknown)}')
    cases = []
    # XVM=0 是可选诊断：默认输入的该边界在100次内未收敛，不列入已验收工况。
    for name in names:
        updates = dict(variants[name])
        if max_iterations is not None:
            updates['ITMAX'] = max_iterations
        result = run_case(name, ROOT, destination, snapshot, updates,
                          backend='legacy' if name == 'legacy' else 'scipy', allow_nonconverged=suite == 'expanded')
        if suite == 'standard' and not result['balance_passed']:
            raise AssertionError(f'{name}: 元素不守恒，详见element_balance.json')
        cases.append(result)
        # 每个已完成工况均落盘，保留非收敛诊断，accepted同时要求求解成功与守恒通过。
        report = dict(input_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            suite=suite, mode='KTRL=1；各工况模式、初值与最终解记录在cases中',
            cases=[{k:v for k,v in case.items() if k not in ('cells', 'rsc_rates')} for case in cases])
        (destination/'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'data/Datain0.dat')
    parser.add_argument('--output', type=Path, default=ROOT/'numeric_test/python_output/element-balance-fixed')
    parser.add_argument('--cases', nargs='+')
    parser.add_argument('--suite', choices=('standard', 'expanded'), default='standard')
    parser.add_argument('--max-iterations', type=int, help='统一覆盖ITMAX，收敛阈值沿用输入')
    args = parser.parse_args()
    report = run_experiment(args.output.resolve(), args.input.resolve(), args.cases,
                            suite=args.suite, max_iterations=args.max_iterations)
    sys.exit(0 if all(c['accepted'] for c in report['cases']) else 2)
