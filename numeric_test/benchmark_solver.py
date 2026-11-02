"""隔离的求解耗时与状态验收；每个工况单进程顺序计时，结果写到指定目录。"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def benchmark_linear(output):
    """同一实际雅可比比较两种线性后端；导入和矩阵恢复不计时。"""
    import numpy as np
    from scipy.linalg import solve_banded  # 预热导入
    sys.path.insert(0, str(ROOT / 'src'))
    import main as solver
    from common.common_data import common
    from functions.math_utils import blktrd, solve_banded_blocks
    with contextlib.redirect_stdout(io.StringIO()):
        solver.eingab(str(ROOT / 'data/Datain0.dat'))
    names = dict(xmass='xmass', entfed='entfed', entkol='entkol', phi='PHI', ri='RI', enthp='ENTHP', wdkr='WDKR')
    names.update({f'xk{i}': f'xk{i}' for i in range(1, 7)})
    names.update({f'a{i}': f'A{i}' for i in range(1, 6)})
    solver.gasifier(**{f'{key}_func': getattr(solver, name) for key, name in names.items()})
    saved = {k: getattr(common, k).copy() for k in ('AMAT', 'BMAT', 'CMAT', 'DMAT')}
    size, cells = common.NVWS, common.NZEL2
    dense = np.zeros((size * cells, size * cells))
    for i in range(cells):
        here = slice(i * size, (i + 1) * size)
        dense[here, here] = saved['BMAT'][1:size+1, 1:size+1, i+1]
        if i + 1 < cells:
            after = slice((i + 1) * size, (i + 2) * size)
            dense[after, here] = saved['AMAT'][1:size+1, 1:size+1, i+1]
            dense[here, after] = saved['CMAT'][1:size+1, 1:size+1, i+1]
    rhs = saved['DMAT'][1:size+1, 1:cells+1].T.ravel()
    report, solutions = {}, {}
    for name, solve in (('legacy', blktrd), ('scipy', solve_banded_blocks)):
        samples = []
        for _ in range(21):
            for key, value in saved.items():
                getattr(common, key)[:] = value
            start = time.perf_counter()
            solve(common.NVWS, common.NZEL2)
            samples.append(time.perf_counter() - start)
        report[name] = dict(median_seconds=float(np.median(samples[1:])), samples=20)
        solutions[name] = common.DMAT.copy()
        vector = common.DMAT[1:size+1, 1:cells+1].T.ravel()
        # 实际雅可比能量/组分量级悬殊，以逐行后向误差验收线性解。
        denominator = np.abs(dense) @ np.abs(vector) + np.abs(rhs)
        backward_error = float(np.max(np.abs(dense @ vector - rhs) / np.maximum(denominator, 1e-30)))
        report[name]['componentwise_backward_error'] = backward_error
        if name == 'scipy':
            assert backward_error < 1e-12, (name, backward_error)
    report['max_correction_difference'] = float(np.max(np.abs(solutions['legacy'] - solutions['scipy'])))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'linear_comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


def worker(source, folder):
    import numpy as np
    sys.path.insert(0, str(source / 'src'))
    from main import main
    from common.common_data import common
    os.chdir(folder)
    start = time.perf_counter()
    code = main(str(folder / 'Datain0.dat'))
    seconds = time.perf_counter() - start
    state = {k: v for k, v in vars(common).items() if isinstance(v, np.ndarray) or type(v) in (int, float)}
    np.savez(folder / 'state.npz', **state)
    (folder / 'timing.json').write_text(json.dumps(dict(returncode=code, seconds=seconds,
        iterations=common.ITERAT, temperature_c=float(common.T[common.NZRE]-273.15),
        corrections={k: float(getattr(common, k)) for k in ('SUMFE', 'SUMWE', 'SUMX', 'SUMT')},
        python=sys.version.split()[0], numpy=np.__version__), indent=2), encoding='utf-8')
    return 0  # 失败工况也是待比较的验收数据


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', default=['fixed', 'texaco', 'high-oxygen', 'low-load', 'combined'])
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--linear-only', action='store_true', help='仅比较同一实际矩阵的线性求解耗时')
    args = parser.parse_args()
    if args.linear_only:
        benchmark_linear(args.output)
        sys.exit(0)
    if args.worker:
        sys.exit(worker(args.source.resolve(), args.output.resolve()))
    sys.path.insert(0, str(ROOT))
    from web_backend.dataparser import parse_datain0, write_datain0
    cases = {'fixed': {}, 'texaco': {'KMODEL': 0, 'QLOSS': .03},
             'high-oxygen': {'FOXY': 1.04, 'BSLURRY': 12},
             'low-load': {'FOXY': .9715, 'BSLURRY': 11.942},
             'combined': {'FEED_MODE': 1, 'T_CHAMBER_C': 1228, 'EFFECTIVE_GAS_NMH': 52000, 'RSC_MODE': 1}}
    summaries = []
    for name in args.cases:
        folder = (args.output / name).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'Datain0.dat'
        path.write_bytes((ROOT / 'data/Datain0.dat').read_bytes())
        params = parse_datain0(path)
        params.update(KTRL=1, FEED_MODE=0, RSC_MODE=0)
        params.update(cases[name])
        write_datain0(path, params)
        with (folder / 'run.log').open('w', encoding='utf-8') as log:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', '--source', str(args.source.resolve()),
                            '--output', str(folder)], stdout=log, stderr=log, check=True,
                           env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=3600)
        result = {'case': name, **json.loads((folder / 'timing.json').read_text())}
        result['total_iterations'] = sum(line.startswith('Iter:') for line in (folder / 'run.log').read_text(encoding='utf-8').splitlines())
        summaries.append(result)
        print(json.dumps(result), flush=True)
    (args.output / 'summary.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
