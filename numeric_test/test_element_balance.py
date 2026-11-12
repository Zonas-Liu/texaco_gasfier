"""独立元素核算口径测试，不将待审模型自身的输出用作真值。"""
import json
import unittest

import numpy as np

from check_element_balance import ELEMENT_MATRIX, elemental_stream, inlet_components, total_mass_ledger


class ElementBalanceTests(unittest.TestCase):
    def test_species_and_solid_mass_partition(self):
        # 每种气体各1 kmol/h；残碳2 kg/h、灰3 kg/h。
        result = elemental_stream(np.ones(8)/3600, 5/3600, .4)
        np.testing.assert_allclose(result, [38, 10, 96, 28, 32, 3])
        self.assertAlmostEqual(result.sum(), sum([32,16,28,44,34,2,28,18])+5)

    def test_reactions_conserve_elements_before_equation_scaling(self):
        wgs = np.array([0, 0, -1, 1, 0, 1, 0, -1])
        meth = np.array([0, 1, -1, 0, 0, -3, 0, 1])
        np.testing.assert_array_equal(ELEMENT_MATRIX @ wgs, np.zeros(6))
        np.testing.assert_array_equal(ELEMENT_MATRIX @ meth, np.zeros(6))
        # 原实现的行缩放不一致，产生可独立推导的元素缺口。
        effective_wgs = wgs.astype(float)
        effective_wgs[3] *= 1.2
        effective_wgs[5] /= 1.02
        np.testing.assert_allclose(ELEMENT_MATRIX @ effective_wgs,
            [2.4, 2*(1/1.02-1), 6.4, 0, 0, 0], atol=1e-14)

    def test_coal_moisture_water_and_impure_oxygen_basis(self):
        state = dict(BSLURRY=10, RATIO_COAL=.5, ELC=.6, ELH=.04, ELO=.08,
            ELN=.02, ELS=.01, ELAS=.15, ELH2O=.10, FOXY=1, PURE_O2=.8, RATIO_CO2=.2)
        parts = inlet_components(state)
        np.testing.assert_allclose(parts['coal']/3600, [3,.2,.4,.1,.05,.75])
        np.testing.assert_allclose(parts['water']/3600, [0,5.5*2/18,5.5*16/18,0,0,0])
        # 无水无灰煤3.75 kg/s，纯氧3.75 kg/s，氧流杂质按N2计，另加CO2。
        total_oxygen_stream = 3.75/32/.8
        n2 = total_oxygen_stream*.2
        co2 = total_oxygen_stream*.2
        np.testing.assert_allclose(parts['oxidant_and_co2']/3600,
            [co2*12, 0, 3.75+co2*32, n2*28, 0, 0])

    def test_total_mass_is_independent_of_coal_element_sum(self):
        state = dict(BSLURRY=10, RATIO_COAL=.5, ELC=.6, ELH=.04, ELO=.08,
            ELN=.02, ELS=.01, ELAS=.15, ELH2O=.10, FOXY=1, PURE_O2=.8, RATIO_CO2=.2,
            NZRC=1, NZRE=2, XMOL=np.array([32, 16, 28, 44, 34, 2, 28, 18]),
            FEMF=np.zeros((9, 3)), WE=np.zeros(3), X=np.zeros(3))
        # 工业氧3.75 kg/s O2，加0.8203125 kg/s N2及1.2890625 kg/s CO2。
        expected = (10 + 3.75 + .8203125 + 1.2890625) * 3600
        state['FEMF'][8, 1:] = (expected / 3600 - 2) / 18
        state['WE'][1:] = 2
        state['X'][1:] = .25
        result = total_mass_ledger(state)
        self.assertAlmostEqual(result['total_mass_kg_h']['inlet'], expected)
        self.assertTrue(all(c['passed'] for c in result['mass_comparisons'].values()))
        self.assertEqual(result['outlet_mass_components_kg_h']['rsc']['residual_carbon'], 1800)
        self.assertEqual(result['outlet_mass_components_kg_h']['rsc']['ash'], 5400)
        self.assertTrue(result['coal_analysis']['passed'])
        self.assertTrue(result['molar_mass_check']['passed'])
        json.dumps(result)  # 审计证据必须可以直接输出JSON，包括NumPy状态导出的布尔值。
        # 元素分析少报1%不会降低实际煤浆进口质量，须单独报告分析基准缺口。
        state['ELC'] -= .01
        incomplete = total_mass_ledger(state)
        self.assertEqual(incomplete['total_mass_kg_h'], result['total_mass_kg_h'])
        self.assertFalse(incomplete['coal_analysis']['passed'])
        self.assertAlmostEqual(incomplete['coal_analysis']['mass_gap_kg_h'], -180)
        self.assertAlmostEqual(sum(inlet_components(state).values()).sum(), expected-180)
        # 出口遗漏一股固体，即使气体不变，总质量检查也必须失败。
        state['WE'][2] = 0
        missing_solid = total_mass_ledger(state)
        self.assertFalse(missing_solid['mass_comparisons']['inlet_to_rsc']['passed'])
        self.assertAlmostEqual(missing_solid['mass_comparisons']['inlet_to_rsc']['delta_kg_h'], -7200)

    def test_total_mass_detects_inconsistent_molar_masses(self):
        state = dict(BSLURRY=1, RATIO_COAL=.5, ELC=.85, ELH=0, ELO=0,
            ELN=0, ELS=0, ELAS=.15, ELH2O=0, FOXY=1, PURE_O2=1, RATIO_CO2=0,
            NZRC=1, NZRE=1, XMOL=np.array([32, 16, 28, 44, 34, 2, 28, 18]),
            MC=12.011, MH=1.008, MO=15.999, MN=14.007, MS=32.06,
            FEMF=np.zeros((9, 2)), WE=np.zeros(2), X=np.zeros(2))
        self.assertFalse(total_mass_ledger(state)['molar_mass_check']['passed'])


if __name__ == '__main__':
    unittest.main()
