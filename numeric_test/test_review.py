"""审查回归：输入隔离、求解失败、结果解析与单进程 Web 并发保护。"""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, Mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from common.common_data import common
from common.input_validation import validate_params
from common.result_io import read_result_text, parse_outlet
from functions.math_utils import gausll, kolon1, blktrd
from subroutines.initialization import eingab, _read_start_file
from subroutines.output_results import kolerg, kontr
from web_backend import dataparser
from web_backend import app as backend


class ReviewTests(unittest.TestCase):
    def setUp(self):
        common.reset()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.input = self.directory / 'Datain0.dat'
        self.input.write_bytes((ROOT / 'data/Datain0.dat').read_bytes())

    def initialize(self):
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(self.input))

    def test_repeated_runs_reset_model_and_arrays(self):
        self.initialize()
        self.assertEqual(common.NZRE, 60)
        common.FEEDO2[45] = 12
        self.input.write_text('\n'.join(self.input.read_text().splitlines()[:11]))
        self.initialize()
        self.assertEqual(common.KMODEL, 0)
        self.assertEqual(common.NZRE, 30)
        self.assertEqual(common.FEEDO2[45], 0)

    def test_invalid_core_inputs(self):
        original = self.input.read_text()
        for old, new in [('2.6,30.0,30', '2.6,30.0,31'),
                         ('2.6,30.0,30', '2.6,30.0,1.5'),
                         ('6.5D06', '2.0D06'), ('1773.0', 'nan')]:
            with self.subTest(new=new):
                self.input.write_text(original.replace(old, new))
                with self.assertRaises(ValueError):
                    self.initialize()

    def test_validation_domains(self):
        for params in ({'PURE_O2': 0}, {'DP': -1}, {'BSLURRY': float('inf')},
                       {'ITMAX': 1.5}, {'RATIO_COAL': 60}, {'KTRL': True}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                validate_params(params)

    def test_restart_rejects_missing_truncated_and_wrong_grid(self):
        self.initialize()
        with self.assertRaises(FileNotFoundError):
            _read_start_file(self.directory / 'missing')
        restart = self.directory / 'START.DAT'
        for count in (10, 330, 661):
            restart.write_text('1 ' * count)
            with self.assertRaises(ValueError):
                _read_start_file(restart)

    def test_restart_reads_fortran_exponents(self):
        self.initialize()
        restart = self.directory / 'START.DAT'
        restart.write_text('1D0 ' * 480 + '1500D0 ' * 60 + '.1D0 ' * 60 + '1D0 ' * 60)
        _read_start_file(restart)
        self.assertEqual(common.T[60], 1500)
        self.assertEqual(common.FEMF[8, 60], 1)

    def test_solver_matches_numpy_and_rejects_singular(self):
        a = np.array([[0., 2., 3.], [2., 3., 1.], [4., 1., 2.]])
        rhs = np.array([[2., 4.], [3., 6.], [8., 9.]])
        _, result = gausll(3, 2, np.column_stack((a, rhs)))
        np.testing.assert_allclose(result[:, 3:], np.linalg.solve(a, rhs))
        with self.assertRaises(np.linalg.LinAlgError):
            gausll(2, 1, np.array([[1., 1., 2.], [2., 2., 4.]]))

    def test_nan_cannot_converge(self):
        self.initialize()
        common.DMAT[1, 1] = np.nan
        with self.assertRaises(FloatingPointError):
            kolon1()

    def test_block_solver_matches_dense_system(self):
        rng = np.random.default_rng(42)
        size, cells = 3, 4
        matrix = np.zeros((size * cells, size * cells))
        rhs = rng.normal(size=(cells, size))
        for cell in range(cells):
            span = slice(cell * size, (cell + 1) * size)
            block = np.eye(size) * 10 + rng.normal(size=(size, size))
            matrix[span, span] = block
            common.BMAT[1:4, 1:4, cell + 1] = block
            common.DMAT[1:4, cell + 1] = rhs[cell]
            if cell < cells - 1:
                downstream = slice((cell + 1) * size, (cell + 2) * size)
                lower, upper = rng.normal(size=(2, size, size))
                matrix[downstream, span] = lower
                matrix[span, downstream] = upper
                common.AMAT[1:4, 1:4, cell + 1] = lower
                common.CMAT[1:4, 1:4, cell + 1] = upper
        blktrd(size, cells)
        np.testing.assert_allclose(common.DMAT[1:4, 1:5].T.ravel(),
                                   np.linalg.solve(matrix, rhs.ravel()), atol=1e-14)

    def test_main_exit_status_and_error_progress(self):
        import main as solver
        previous = Path.cwd()
        os.chdir(self.directory)
        self.addCleanup(os.chdir, previous)
        text = self.input.read_text().splitlines()
        text[1] = '1,0.0005,0.0005,0.0005,0.005'
        self.input.write_text('\n'.join(text))
        for flag, code, status in ((1, 2, 'not_converged'), (0, 0, 'completed')):
            with patch.object(solver, 'gasifier'), \
                    patch.object(solver, 'newtra', side_effect=lambda **kw: setattr(common, 'KONVER', flag)), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(solver.main(str(self.input)), code)
            progress = json.loads(Path('simulation_progress.json').read_text())
            self.assertEqual(progress['status'], status)
        with patch.object(solver, 'eingab', side_effect=ValueError('bad input')):
            with self.assertRaises(ValueError):
                solver.main(str(self.input))
        self.assertEqual(json.loads(Path('simulation_progress.json').read_text())['status'], 'error')
        # Windows 上也能重新打开，验证异常路径关闭输出句柄。
        Path('GASTEST.DAT').write_text('closed')

    def test_encoding_and_outlet_after_steam_summary(self):
        text = '出口温度: 756.900 C    碳转化率: 0.9999\n' + '产汽量: 1.050 t/h\n' * 8
        for encoding in ('utf-8', 'gbk'):
            p = self.directory / 'GASTEST.DAT'
            p.write_bytes(text.encode(encoding))
            self.assertEqual(read_result_text(p), text)
            self.assertEqual(parse_outlet(text)['CarbonConversion'], .9999)
            self.assertEqual(dataparser.parse_gastest(p)['outlet']['Temperature(C)'], 756.9)

    def test_gui_preserves_optional_line_positions(self):
        lines = self.input.read_text().splitlines()
        lines[12] = ''
        self.input.write_text('\n'.join(lines) + '\n')
        params = dataparser.parse_datain0(self.input)
        dataparser.write_datain0(self.input, params)
        self.assertEqual(self.input.read_text().splitlines()[11:], lines[11:])
        self.assertEqual(dataparser.PARAM_INFO['BSLURRY']['unit'], 'kg/s')

    def test_web_heat_summary_uses_output_fields(self):
        output = self.directory / 'GASTEST.DAT'
        output.write_text('''出口温度: 756.862 C    碳转化率: 1.0000
      汽包压力: 6.50 MPa
      水冷壁产汽量: 2.129 t/h
      辐射废锅产汽量: 24.318 t/h
      总产汽量: 26.446 t/h
      水冷壁热负荷: 1.266 MW
      辐射废锅热负荷: 14.467 MW
''', encoding='utf-8')
        result = dataparser.parse_gastest(output)
        self.assertEqual(result['heat_recovery'], {
            'drum_pressure_mpa': 6.5, 'steam_wall_tph': 2.129,
            'steam_rsc_tph': 24.318, 'steam_total_tph': 26.446,
            'heat_wall_mw': 1.266, 'heat_rsc_mw': 14.467,
        })
        self.assertEqual(result['outlet']['Temperature(C)'], 756.862)

    def test_web_texaco_does_not_fabricate_heat_summary(self):
        output = self.directory / 'GASTEST.DAT'
        output.write_text('出口温度: 1145.283 C    碳转化率: 1.0000', encoding='utf-8')
        self.assertEqual(dataparser.parse_gastest(output)['heat_recovery'], {})

    def test_output_refresh_and_restart_roundtrip(self):
        self.initialize()
        common.FEM[:] = -1
        original = common.FEMF.copy()
        with patch('subroutines.output_results.os.getcwd', return_value=str(self.directory)):
            output = io.StringIO()
            kolerg(output)
        np.testing.assert_allclose(common.FEM[1:61], common.FEMF[1:9, 1:61].sum(axis=0))
        self.assertIn('各组分流量对比', output.getvalue())
        self.assertIn('Temperature(C)', parse_outlet(output.getvalue()))
        _read_start_file(self.directory / 'START.DAT')
        np.testing.assert_allclose(common.FEMF, original, rtol=1e-6)

    def test_mass_balance_oxygen_units_and_co2_feed(self):
        common.NZRE = common.NZEL2 = 1
        common.NZRA = common.NZEL1 = 1
        common.BSLURRY = 0
        common.FEEDO2[1] = common.FEMF[1, 1] = 1
        common.FEEDN2[1] = common.FEMF[7, 1] = .5
        common.FEDCO2[1] = common.FEMF[4, 1] = 2
        self.assertAlmostEqual(kontr()[3], 0)
        self.assertAlmostEqual(kontr()[4], 32 + 14 + 88)

    def test_api_bad_payload_and_busy_save(self):
        with patch.object(backend, 'DATA_FILE', self.input):
            client = backend.app.test_client()
            for payload in ([], {'ITMAX': 1.2}, {'DP': 'nan'}, {'PURE_O2': 0}, {'BAD': 1}):
                with self.subTest(payload=payload):
                    self.assertEqual(client.post('/api/run', json=payload).status_code, 400)
            with patch.dict(backend._sim_state, process=Mock(poll=lambda: None)):
                self.assertEqual(client.post('/api/params', json={'ITMAX': 10}).status_code, 409)

    def test_api_start_is_atomic(self):
        statuses = []
        def launch(*args, **kwargs):
            time.sleep(.05)
            return Mock(pid=123, poll=lambda: None)
        def request_run():
            with backend.app.test_client() as client:
                statuses.append(client.post('/api/run', json={}).status_code)
        with patch.object(backend, 'ROOT', self.directory), patch.object(backend, 'DATA_FILE', self.input), \
                patch.dict(backend._sim_state, process=None, completed=False), \
                patch.object(backend.subprocess, 'Popen', side_effect=launch) as popen:
            threads = [threading.Thread(target=request_run) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sorted(statuses), [200, 409])
            self.assertEqual(popen.call_count, 1)


if __name__ == '__main__':
    unittest.main()
