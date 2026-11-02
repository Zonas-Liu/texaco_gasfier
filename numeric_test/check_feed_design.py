r"""实际全炉反算验收；各工况在独立目录运行，不改根目录输入/结果/START。

运行：.venv\Scripts\python.exe numeric_test/check_feed_design.py
"""
import concurrent.futures
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from web_backend.dataparser import parse_datain0, write_datain0, parse_gastest

DEST = ROOT / 'numeric_test/python_output/feed-design'


def run_case(name, updates, expected=0):
    folder = DEST / name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'Datain0.dat'
    path.write_bytes((ROOT / 'data/Datain0.dat').read_bytes())
    params = parse_datain0(path)
    params.update(FEED_MODE=0, RSC_MODE=0, KTRL=1)
    params.update(updates)
    write_datain0(path, params)
    sentinel = 'preserve previous accepted restart\n'
    (folder / 'START.DAT').write_text(sentinel)
    code = "import sys;sys.path.insert(0,sys.argv[1]);from main import main;sys.exit(main(sys.argv[2]))"
    with (folder / 'run.log').open('w', encoding='utf-8') as log:
        proc = subprocess.run([sys.executable, '-c', code, str(ROOT / 'src'), str(path)], cwd=folder,
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, stdout=log, stderr=log, timeout=2400)
    assert proc.returncode == expected, (name, proc.returncode, str(folder / 'run.log'))
    data = parse_gastest(folder / 'GASTEST.DAT')
    feed = data.get('feed_design', {})
    if feed:
        assert feed['overall_success'] == (expected == 0), name
        if feed['success']:
            assert abs(feed['temperature_error_c']) <= feed['temperature_tolerance_c']
            assert abs(feed['flow_error_nmh']) <= feed['flow_tolerance_nmh']
    if expected != 0:
        assert (folder / 'START.DAT').read_text() == sentinel, name
    else:
        assert (folder / 'START.DAT').read_text() != sentinel, name
    for section in data['outlet_sections']:
        slurry = feed.get('slurry_kg_s', params['BSLURRY'])
        if data['convergence_history'][-1]['KONVER'] == 0:
            assert abs(section['ash_kg_h'] - slurry * params['RATIO_COAL'] * params['ELAS'] * 3600) < .02
        assert abs(section['total_molar_kmol_h'] * 22.4 / 3600 - section['total_wet_nms']) < 1e-9
    report = dict(name=name, returncode=proc.returncode, feed=feed, rsc=data.get('rsc_design'),
                  outlets=data['outlet_sections'], iterations=data['convergence_history'][-1]['Iter'])
    (folder / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('feed', 'rsc', 'outlets')} |
                     {k: feed.get(k) for k in ('oxygen_coal_ratio', 'slurry_kg_s', 'temperature_error_c', 'flow_error_nmh', 'evaluations')}, ensure_ascii=False), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-forward', action='store_true', help='复用此次验收已完成的正算报告')
    parser.add_argument('--cases', nargs='+', help='只运行指定案例')
    parser.add_argument('--output', type=Path, default=DEST, help='隔离验收目录')
    args = parser.parse_args()
    DEST = args.output.resolve()
    base = json.loads((DEST / 'forward/report.json').read_text(encoding='utf-8')) if args.reuse_forward else run_case('forward', {})
    chamber = base['outlets'][0]
    targets = dict(FEED_MODE=1, T_CHAMBER_C=chamber['temperature_c'],
                   EFFECTIVE_GAS_NMH=chamber['effective_gas_nmh'], FOXY=.98, BSLURRY=14)
    cases = [
        ('recover-v2', dict(targets, FOXY=.97, BSLURRY=13.5), 0),
        ('combined', dict(targets, T_CHAMBER_C=1228, EFFECTIVE_GAS_NMH=52000, RSC_MODE=1), 0),
        ('inner_failure', dict(targets, ITMAX=1), 2),
        ('rsc-failure-v2', dict(targets, RSC_MODE=1, T_RSC_OUT_C=401), 2),
        ('high-oxygen-recover', dict(targets, FOXY=1.04, BSLURRY=12,
                                     T_CHAMBER_C=1228, EFFECTIVE_GAS_NMH=49618.46), 0),
        ('lower-load', dict(targets, T_CHAMBER_C=1200, EFFECTIVE_GAS_NMH=42000), 0),
        ('rsc-one', dict(N_RSC=1), 0),
        ('secondary-oxygen', dict(OX_PART=.9), 0),
    ]
    if args.cases:
        cases = [c for c in cases if c[0] in args.cases]
        if len(cases) != len(set(args.cases)):
            parser.error('案例名称不存在')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda args: run_case(*args), cases))
    for report in results:
        if report['name'] == 'recover-v2':
            assert abs(report['feed']['oxygen_coal_ratio'] - .98) < .001
            assert abs(report['feed']['slurry_kg_s'] - 14) < .02
    (DEST / 'summary.json').write_text(json.dumps([base, *results], ensure_ascii=False, indent=2), encoding='utf-8')
