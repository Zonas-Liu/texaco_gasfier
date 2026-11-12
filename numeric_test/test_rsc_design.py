"""目标温度搜索、双出口结果与可选输入的回归；实际全炉复算另见设计验收记录。"""
import contextlib
import io
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from common.common_data import common
from common.input_validation import validate_params
from functions.rsc_design import search_height
from functions.steam_props import steam_production, h_sat_steam, h_feedwater
from subroutines.initialization import eingab
from web_backend import dataparser
from web_backend import app as backend
from unittest.mock import patch


class RscDesignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.input = Path(self.tmp.name) / 'Datain0.dat'
        self.input.write_bytes((ROOT / 'data/Datain0.dat').read_bytes())

    def evaluate(self, height):
        return {'temperature_c': 400 + 900 * math.exp(-height / 30), 'converged': True}

    def test_height_search_both_directions_and_endpoint(self):
        for height in (15, 45, 1, 120):
            target = self.evaluate(height)['temperature_c']
            result = search_height(self.evaluate, target, 30, 1, 120)
            self.assertTrue(result['success'])
            self.assertLessEqual(abs(result['temperature_c'] - target), .5)
            self.assertTrue(all(1 <= t['height_m'] <= 120 for t in result['trials']))

    def test_unreachable_and_failed_inner_solve_are_not_success(self):
        result = search_height(self.evaluate, 300, 30, 1, 120)
        self.assertFalse(result['success'])
        result = search_height(lambda h: {'temperature_c': 780, 'converged': False}, 780, 30, 1, 120)
        self.assertFalse(result['success'])
        self.assertEqual(result['evaluations'], 1)
        with self.assertRaises(ValueError):
            search_height(lambda h: {'temperature_c': math.nan}, 780, 30, 1, 120)

    def test_heat_to_steam_balance_and_feedwater_effect(self):
        q = 13.2e6
        for p, t in ((6.5e6, 423.15), (6.5e6, 473.15), (8e6, 423.15)):
            m = steam_production(q, p, t)
            self.assertAlmostEqual(m * (h_sat_steam(p) - h_feedwater(t, p)) * 1000, q)
        self.assertGreater(steam_production(q, 6.5e6, 473.15), steam_production(q, 6.5e6, 423.15))

    def test_optional_line_roundtrip_and_reset(self):
        original = self.input.read_text().splitlines()
        values = dataparser.parse_datain0(self.input)
        values.update(RSC_MODE=1, T_RSC_OUT_C=800, P_DRUM=8e6)
        dataparser.write_datain0(self.input, values)
        read = dataparser.parse_datain0(self.input)
        self.assertEqual(read['T_RSC_OUT_C'], 800)
        self.assertEqual(read['P_DRUM'], 8e6)
        self.assertEqual(self.input.read_text().splitlines()[12:14], original[12:14])
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(self.input))
        self.assertEqual(common.RSC_MODE, 1)
        self.assertEqual(common.T_RSC_OUT_C, 800)
        # 实际删除可选行，验证缺失第15行时恢复默认模式。
        self.input.write_text('\n'.join(original[:14]))
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(self.input))
        self.assertEqual(common.RSC_MODE, 0)

    def test_input_rejects_incompatible_mode_and_bounds(self):
        values = dataparser.parse_datain0(self.input)
        for updates in ({'RSC_MODE': 1, 'KMODEL': 0}, {'RSC_MODE': 1, 'T_RSC_OUT_C': 300},
                        {'RSC_MODE': 1, 'H_RSC_MIN': 20, 'H_RSC_MAX': 10}, {'RSC_MODE': 1.5}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                validate_params({**values, **updates})

    def test_web_accepts_design_controls_and_rejects_invalid_target(self):
        with patch.object(backend, 'DATA_FILE', self.input), patch.object(backend, '_is_running', return_value=False):
            client = backend.app.test_client()
            response = client.post('/api/params', json={'RSC_MODE': 1, 'T_RSC_OUT_C': 780})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(client.get('/api/params').json['values']['RSC_MODE'], 1)
            self.assertEqual(client.post('/api/params', json={'T_RSC_OUT_C': 300}).status_code, 400)
            self.assertEqual(dataparser.parse_datain0(self.input)['T_RSC_OUT_C'], 780)

    def test_two_outlets_use_same_output_and_correct_basis(self):
        gases = ('O2', 'CH4', 'CO', 'CO2', 'H2S', 'H2', 'N2', 'H2O')
        result = {'gas_composition_profile': [{'I': i, **dict(zip(gases, [0, 1, 30, 10, 1, 35, 3, 20]))} for i in (30, 45)],
                  'internal_profile': [{'I': 30, 'T(C)': 1200}, {'I': 45, 'T(C)': 780}],
                  'heat_recovery': {'steam_rsc_tph': 22}, 'volume_flow': {}, 'syngas_composition': {}}
        text = '各组分流量对比 (Nm3/s):\n' + '\n'.join(f'{g} {j+1} {j+2} 1' for j, g in enumerate(gases)) + '\n总计 36 44 8'
        sections = dataparser.parse_outlet_sections(text, result)
        self.assertEqual([s['cell'] for s in sections], [30, 45])
        self.assertEqual([s['temperature_c'] for s in sections], [1200, 780])
        self.assertEqual(sections[0]['total_dry_nms'], 28)
        self.assertEqual(sections[0]['total_wet_nms'], 36)
        self.assertAlmostEqual(sum(sections[0]['dry_composition'].values()), 100)
        self.assertEqual(sections[1]['volume_flow']['H2O'], 9)
        self.assertNotIn('H2O', sections[0]['dry_composition'])
        result['heat_recovery'] = {}
        self.assertEqual(len(dataparser.parse_outlet_sections('', result)), 1)


if __name__ == '__main__':
    unittest.main()
