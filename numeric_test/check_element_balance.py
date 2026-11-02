"""进口/燃烧室/废锅独立元素衡算；所有求解及候选修正都在隔离目录。

只读取完整精度状态，不调用 KONTR 或由干基百分比反推质量。
运行：python numeric_test/check_element_balance.py --output numeric_test/python_output/element-balance
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
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


def elemental_stream(gas_kmol_s, solid_kg_s=0.0, carbon_fraction=0.0):
    """气相全部八组分＋固体残碳/灰，返回六项 kg/h。"""
    result = ELEMENT_MATRIX @ np.asarray(gas_kmol_s, dtype=float)
    result[0] += solid_kg_s * carbon_fraction
    result[5] += solid_kg_s * (1 - carbon_fraction)
    return result * 3600


def inlet_components(state):
    """物理进料独立核算：原煤元素、水煤浆水、氧化剂/稀释气。

    保留输入煤分析基准，不归一化；ELH2O 的水单独分配给 H/O。
    各燃烧室进料点一并计入，冷却水/副产蒸汽属于独立公用工程侧。
    """
    coal = float(state['BSLURRY'] * state['RATIO_COAL'])
    coal_elements = coal * np.array([float(state[k]) for k in ('ELC', 'ELH', 'ELO', 'ELN', 'ELS', 'ELAS')]) * 3600
    water = float(state['BSLURRY'] * (1 - state['RATIO_COAL']) + coal * state['ELH2O'])
    water_gas = np.zeros(8)
    water_gas[7] = water / 18
    oxidant_gas = np.zeros(8)
    # 从输入氧煤比、纯度和分析值计算总物理进料，独立于源项分配数组。
    pure_o2 = float(state['FOXY']) * coal * (1 - float(state['ELH2O']) - float(state['ELAS'])) / 32
    oxygen_stream = pure_o2 / float(state['PURE_O2'])
    oxidant_gas[0] = pure_o2
    oxidant_gas[6] = oxygen_stream * (1 - float(state['PURE_O2']))
    oxidant_gas[3] = oxygen_stream * float(state['RATIO_CO2'])
    return {'coal': coal_elements, 'water': elemental_stream(water_gas),
            'oxidant_and_co2': elemental_stream(oxidant_gas)}


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


def ledger(state):
    """输出逐格元素流及三截面差值；审计容差与求解器容差相互独立。"""
    if int(state['KMODEL']) != 1 or int(state['KCHECK']) != 0:
        raise ValueError('此实验针对晋华炉正常模式 KMODEL=1、KCHECK=0')
    inputs = inlet_components(state)
    inlet = sum(inputs.values())
    flows = np.array([elemental_stream(state['FEMF'][1:9, i], state['WE'][i], state['X'][i])
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
    predicted = np.array([12 * .2 * sw, 2 * (1/1.02 - 1) * (sw - 3*sm), 32 * .2 * sw, 0, 0, 0]) * 3600
    rows = []
    for i, flow in enumerate(flows, 1):
        previous = inlet if i == 1 else flows[i-2]
        # 第1格尚未加入二次氧；仅把31..NZRE的逐格差用于RSC无进料诊断。
        rows.append(dict(cell=i, elements_kg_h=flow.tolist(),
                         adjacent_delta_kg_h=(flow-previous).tolist()))
    return dict(elements=list(ELEMENTS), units='kg/h', atomic_weights='C12 H1 O16 N14 S32',
        input_components_kg_h={k:v.tolist() for k,v in inputs.items()}, inlet_kg_h=inlet.tolist(),
        chamber_kg_h=chamber.tolist(), rsc_kg_h=outlet.tolist(),
        chamber_temperature_c=float(state['T'][int(state['NZRC'])]-273.15),
        rsc_temperature_c=float(state['T'][int(state['NZRE'])]-273.15),
        tolerance_kg_h=tolerance.tolist(), comparisons=comparisons,
        total_mass_kg_h=dict(inlet=float(inlet.sum()), chamber=float(chamber.sum()), rsc=float(outlet.sum())),
        sum_rsc_wgs_kmol_s=sw, sum_rsc_meth_kmol_s=sm,
        predicted_original_scaling_defect_kg_h=predicted.tolist(),
        prediction_gap_kg_h=(outlet-chamber-predicted).tolist(), cells=rows,
        rsc_rates=[dict(cell=i, wgs_kmol_s=w, meth_kmol_s=m) for i,w,m in rates])


def run_case(name, source, destination, original_input, updates, backend='scipy', candidate=False):
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
    if timing['returncode'] != 0:
        raise RuntimeError(f'{name} 未收敛，不能验收元素衡算：{folder}')
    with np.load(folder/'state.npz') as state:
        result = ledger(state)
    result.update(case=name, timing=timing, linear_backend=backend, candidate_only=candidate,
                  original_scaling_prediction_applicable=not candidate)
    if candidate:
        result['prediction_gap_kg_h'] = None  # 原缺陷公式不适用于修正后的方程
    (folder/'element_balance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(case=name, chamber_pass=result['comparisons']['inlet_to_chamber']['passed'],
        rsc_pass=result['comparisons']['chamber_to_rsc']['passed'],
        delta_kg_h=result['comparisons']['chamber_to_rsc']['delta_kg_h']), ensure_ascii=False), flush=True)
    return result


def run_experiment(destination, input_path):
    destination.mkdir(parents=True, exist_ok=True)
    # 先记录原模型，再进行控制变量实验；候选修正只写入实验副本。
    cases = [run_case('baseline', ROOT, destination, input_path, {}),
        run_case('tighter', ROOT, destination, input_path,
                 dict(ITMAX=200, SKONFE=1e-8, SKONWE=1e-8, SKONX=1e-8, SKONT=1e-5)),
        run_case('legacy', ROOT, destination, input_path, {}, backend='legacy'),
        run_case('no-rsc-relax', ROOT, destination, input_path, dict(KRELAX_WGS=0, KRELAX_METH=0))]
    candidate = destination/'candidate_source'
    shutil.copytree(ROOT/'src', candidate/'src', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
    path = candidate/'src/subroutines/gasifier_main.py'
    original = path.read_text(encoding='utf-8')
    replacements = {
        'common.DMAT[4, i] += r_wgs ': 'common.DMAT[4, i] += r_wgs / 1.2 ',
        'common.DMAT[6, i] += r_wgs - 3.0 * r_meth ': 'common.DMAT[6, i] += (r_wgs - 3.0 * r_meth) * 1.02 ',
    }
    changed = original
    for old, new in replacements.items():
        if changed.count(old) != 1:
            raise RuntimeError('候选修正上下文已变，需重新审查源项缩放')
        changed = changed.replace(old, new)
    path.write_text(changed, encoding='utf-8')
    candidate_result = run_case('consistent-rsc-scaling', candidate, destination, input_path, {}, candidate=True)
    cases.append(candidate_result)
    compact = [{k:v for k,v in case.items() if k not in ('cells', 'rsc_rates')} for case in cases]
    report = dict(input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        mode='给定进料、固定高度、KTRL=1；不读取根目录START', cases=compact,
        candidate_replacements=replacements)
    (destination/'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'data/Datain0.dat')
    parser.add_argument('--output', type=Path, default=ROOT/'numeric_test/python_output/element-balance')
    args = parser.parse_args()
    run_experiment(args.output.resolve(), args.input.resolve())
