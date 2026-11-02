"""燃烧室双目标、单位转换和同源出口数据回归。"""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from common.common_data import common
from common.display_units import display_spec, to_display, to_model
from common.input_validation import validate_params
from functions.feed_design import search_feed
from subroutines.initialization import eingab
from subroutines.output_results import kolerg
from web_backend import dataparser, app as backend


class FeedDesignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'Datain0.dat'
        self.path.write_bytes((ROOT / 'data/Datain0.dat').read_bytes())

    @staticmethod
    def plant(oxy, slurry):
        return dict(temperature_c=900 + oxy * 300 + slurry * 2,
                    effective_gas_nmh=slurry * (4000 - oxy * 500), converged=True)

    def test_coupled_targets_and_bounds(self):
        for target_point in ((.98, 14), (.8, 8), (1.2, 25), (.7, 5), (1.3, 30)):
            target = self.plant(*target_point)
            r = search_feed(self.plant, target['temperature_c'], target['effective_gas_nmh'],
                            [1, 12], [.7, 5], [1.3, 30])
            self.assertTrue(r['success'], r['message'])
            self.assertLessEqual(abs(r['temperature_error_c']), .5)
            self.assertLessEqual(abs(r['flow_error_nmh']), r['flow_tolerance_nmh'])
            for t in r['trials']:
                self.assertTrue(.7 - 1e-12 <= t['oxygen_coal_ratio'] <= 1.3 + 1e-12)
                self.assertTrue(5 - 1e-12 <= t['slurry_kg_s'] <= 30 + 1e-12)

    def test_failure_restores_reported_candidate(self):
        calls = []
        def evaluate(o, s):
            calls.append((o, s))
            return self.plant(o, s)
        r = search_feed(evaluate, 2000, 50000, [1, 14], [.95, 13], [1.05, 15])
        self.assertFalse(r['success'])
        self.assertEqual(calls[-1], (r['oxygen_coal_ratio'], r['slurry_kg_s']))
        failed = search_feed(lambda o, s: {**self.plant(o, s), 'converged': False},
                             1228, 49600, [1, 14], [.7, 5], [1.3, 30])
        self.assertFalse(failed['success'])
        self.assertEqual(failed['evaluations'], 1)

    def test_units_roundtrip_and_metadata(self):
        for model, unit, display in ((8.1e6, 'Pa', 7.998675), (6.5e6, 'Pa', 6.398675),
                                     (101325, 'Pa', 0), (318.15, 'K', 45), (273.15, 'K', 0),
                                     (780, '℃', 780)):
            self.assertAlmostEqual(to_display(model, unit), display)
            self.assertAlmostEqual(to_model(display, unit), model)
        for info in dataparser.PARAM_INFO.values():
            if info['unit'] in ('Pa', 'K'):
                self.assertEqual(info['display'], display_spec(info['unit']))

    def test_one_failed_derivative_direction_can_recover(self):
        calls = []
        def evaluate(o, s):
            calls.append((o, s))
            return {**self.plant(o, s), 'converged': len(calls) != 2}
        target = self.plant(.98, 14)
        r = search_feed(evaluate, target['temperature_c'], target['effective_gas_nmh'],
                        [1, 12], [.7, 5], [1.3, 30])
        self.assertTrue(r['success'])
        self.assertFalse(r['trials'][1]['converged'])

    def test_optional_lines_reset_and_rebuild_feed_sources(self):
        original = self.path.read_text()
        p = dataparser.parse_datain0(self.path)
        p.update(FEED_MODE=1, KTRL=0, T_CHAMBER_C=1250, EFFECTIVE_GAS_NMH=52000)
        dataparser.write_datain0(self.path, p)
        self.assertEqual(len(self.path.read_text().splitlines()), 16)
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(self.path), overrides={'FOXY': 1.1, 'BSLURRY': 20})
        self.assertEqual(common.KTRL, 1)
        self.assertEqual(common.BSMS, 12)
        self.assertAlmostEqual(sum(common.FEEDO2), common.BSWAF * 1.1 / 32)
        self.path.write_text(original)
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(self.path))
        self.assertEqual(common.FEED_MODE, 0)
        self.assertEqual(common.FOXY, .98)

    def test_api_validation_and_unit_contract(self):
        with patch.object(backend, 'DATA_FILE', self.path), patch.object(backend, '_is_running', return_value=False):
            c = backend.app.test_client()
            self.assertEqual(c.post('/api/params', json={'FEED_MODE': 1, 'EFFECTIVE_GAS_NMH': 52000}).status_code, 200)
            self.assertEqual(c.get('/api/params').json['values']['PWK'], 6.7e6)
            for updates in ({'FEED_MODE': .5}, {'EFFECTIVE_GAS_NMH': 0}, {'FOXY_MIN': 1.5},
                            {'SLURRY_MAX': 0}, {'SLURRY_MIN': 15}, {'T_CHAMBER_C': -274}):
                self.assertEqual(c.post('/api/params', json=updates).status_code, 400, updates)
            self.assertEqual(dataparser.parse_datain0(self.path)['EFFECTIVE_GAS_NMH'], 52000)

    def test_precise_molar_and_ash_from_same_output(self):
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(self.path))
        common.WE[60], common.X[60] = 2.0, .25
        output = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()):
            kolerg(output, write_restart=False)
        result_file = Path(self.tmp.name) / 'GASTEST.DAT'
        result_file.write_text(output.getvalue(), encoding='utf-8')
        result = dataparser.parse_gastest(result_file)
        final = result['outlet_sections'][-1]
        self.assertEqual(final['ash_kg_h'], 5400)
        self.assertAlmostEqual(final['molar_flow_kmol_h']['CO'], common.FEMF[3, 60] * 3600)
        self.assertAlmostEqual(final['total_molar_kmol_h'] * 22.4 / 3600, final['total_wet_nms'])
        # 删除新结构化块模拟历史文件：气量可换算，灰流量不得用当前输入伪造。
        old = '\n'.join(l for l in output.getvalue().splitlines() if not l.startswith('OUTLET_FLOWS_JSON:'))
        result_file.write_text(old, encoding='utf-8')
        legacy = dataparser.parse_gastest(result_file)['outlet_sections'][-1]
        self.assertIsNone(legacy['ash_kg_h'])
        self.assertAlmostEqual(legacy['molar_flow_kmol_h']['CO'], legacy['volume_flow']['CO'] * 3600 / 22.4)


if __name__ == '__main__':
    unittest.main()
