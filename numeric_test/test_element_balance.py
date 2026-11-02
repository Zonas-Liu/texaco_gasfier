"""独立元素核算口径测试，不将待审模型自身的输出用作真值。"""
import unittest

import numpy as np

from check_element_balance import ELEMENT_MATRIX, elemental_stream, inlet_components


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


if __name__ == '__main__':
    unittest.main()
