"""隔离复算基线与工作区；不会覆盖项目输入或根目录结果。

用法：python numeric_test/run_regression.py --baseline b0c386d
每个版本运行晋华炉与 11 行 TEXACO 输入，结果保存在 python_output/review。
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from common.result_io import parse_outlet, read_result_text


def compare_pair(base, case):
    before, after = (base / f'{stage}-{case}' for stage in ('before', 'after'))
    progress = [json.loads((p / 'simulation_progress.json').read_text()) for p in (before, after)]
    assert all(p['status'] == 'completed' for p in progress), f'{case}: 未收敛'
    assert progress[0]['iteration'] == progress[1]['iteration'], f'{case}: 迭代次数变化'
    np.testing.assert_array_equal(np.fromstring((before / 'START.DAT').read_text(), sep=' '),
                                  np.fromstring((after / 'START.DAT').read_text(), sep=' '))
    # 出口状态在输出精度内一致；派生量刷新允许修正末位流量/热负荷。
    outlets = [parse_outlet(read_result_text(p / 'GASTEST.DAT')) for p in (before, after)]
    assert outlets[0] == outlets[1], f'{case}: 出口温度或转化率变化'
    return {'case': case, 'iterations': progress[1]['iteration'], 'outlet': outlets[1],
            'restart_values_identical': True, 'residuals': progress[1]['residuals']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='b0c386d')
    parser.add_argument('--compare-only', action='store_true', help='只比较已有隔离输出')
    args = parser.parse_args()
    base = ROOT / 'numeric_test/python_output/review'
    if not args.compare_only:
        commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.baseline + '^{commit}'], cwd=ROOT).decode().strip()
        tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit, 'src', 'data'], cwd=ROOT).decode().splitlines()
        current_input = (ROOT / 'data/Datain0.dat').read_text(encoding='utf-8')

        def run(job):
            stage, case = job
            folder = base / f'{stage}-{case}'
            folder.mkdir(parents=True, exist_ok=True)
            if stage == 'before':
                for name in tracked:
                    target = folder / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(subprocess.check_output(['git', 'show', commit + ':' + name], cwd=ROOT))
            else:
                shutil.copytree(ROOT / 'src', folder / 'src', dirs_exist_ok=True)
            (folder / 'data').mkdir(exist_ok=True)
            lines = current_input.splitlines()
            if case == 'texaco':
                lines = lines[:11]
                lines[10] = '0.03/ QLOSS'
            (folder / 'data/Datain0.dat').write_text('\n'.join(lines) + '\n', encoding='utf-8')
            with (folder / 'run.log').open('w', encoding='utf-8') as log:
                subprocess.run([sys.executable, 'src/main.py'], cwd=folder, stdout=log,
                               stderr=subprocess.STDOUT, check=True, timeout=1800,
                               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(run, [(stage, case) for stage in ('before', 'after')
                                for case in ('jinhualu', 'texaco')]))
    results = [compare_pair(base, case) for case in ('jinhualu', 'texaco')]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
