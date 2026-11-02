"""CIAAW/CODATA/IAPWS数值校核及实际方程源项的原子守恒回归。"""
import contextlib
import io
from pathlib import Path
import sys
import unittest

import numpy as np
from iapws import IAPWS97

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from common.common_data import common
from common.physical_constants import configure, molar_masses, NORMAL_MOLAR_VOLUME, R_MOLAR, STEFAN_BOLTZMANN
from subroutines.initialization import eingab
from subroutines.gasifier_main import _calculate_dmat_for_cell
from functions import reaction_rates as rates
from functions.steam_props import h_feedwater, h_sat_steam, latent_heat, steam_production, tsat_water
import main as solver
from web_backend.dataparser import parse_outlet_sections


class PhysicalConstantsTests(unittest.TestCase):
    def setUp(self):
        common.reset()

    def initialize(self):
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(ROOT/'data/Datain0.dat'))

    def test_reference_values_and_derived_molecular_masses(self):
        expected = {'O2':31.998, 'CH4':16.043, 'CO':28.010, 'CO2':44.009,
                    'H2S':34.076, 'H2':2.016, 'N2':28.014, 'H2O':18.015,
                    'C':12.011, 'SiO2':60.083, 'TAR':12.929498}
        for name, value in expected.items():
            self.assertAlmostEqual(molar_masses()[name], value, places=10)
        self.assertAlmostEqual(R_MOLAR, 8.31446261815324, places=13)
        self.assertAlmostEqual(NORMAL_MOLAR_VOLUME, 22.413969545014, places=10)
        self.assertAlmostEqual(STEFAN_BOLTZMANN, 5.670374419184e-8, delta=1e-19)

    def test_profiles_reset_and_property_functions_use_same_masses(self):
        self.initialize()
        for name, f in [('H2',rates.FH2),('N2',rates.FN2),('O2',rates.FO2),('CO',rates.FCO),
                        ('CO2',rates.FCO2),('CH4',rates.FCH4),('H2S',rates.FH2S),('H2O',rates.FH2O)]:
            self.assertAlmostEqual(f(800,6.7e6,-1,'G','MOLG'), molar_masses()[name])
        common.KMODEL = 0
        configure(common)
        self.assertEqual(common.VM_NORMAL,22.4)
        self.assertEqual(common.RAG,8314.3)
        np.testing.assert_array_equal(common.XMOL,[32,16,28,44,34,2,28,18,12,60])
        self.initialize()
        self.assertAlmostEqual(common.MH2,2.016)

    def test_rsc_source_in_actual_equations_conserves_atoms(self):
        self.initialize()
        common.KTRLR = 0
        names = dict(xmass='xmass',entfed='entfed',entkol='entkol',phi='PHI',ri='RI',enthp='ENTHP',wdkr='WDKR')
        names.update({f'xk{i}':f'xk{i}' for i in range(1,7)})
        names.update({f'a{i}':f'A{i}' for i in range(1,6)})
        kwargs = {f'{k}_func':getattr(solver,v) for k,v in names.items()}
        _calculate_dmat_for_cell(31, **kwargs)
        with_reactions = common.DMAT[1:9,31].copy()
        common.KRELAX_WGS = common.KRELAX_METH = 0
        _calculate_dmat_for_cell(31, **kwargs)
        delta = with_reactions - common.DMAT[1:9,31]
        delta[3] *= 1.2
        delta[5] /= 1.02
        c = common.MC * (delta[1]+delta[2]+delta[3])
        h = common.MH * (4*delta[1]+2*delta[4]+2*delta[5]+2*delta[7])
        o = common.MO * (2*delta[0]+delta[2]+2*delta[3]+delta[7])
        np.testing.assert_allclose([c,h,o],0,atol=1e-13)

    def test_if97_official_check_points(self):
        # IAPWS R7-97(2012), Tables 5, 15, 36；独立发表的校核值。
        for t,p,h in [(300,3,115.331273),(300,80,184.142828),(500,3,975.542239),
                      (300,.0035,2549.91145),(700,.0035,3335.68375),(700,30,2631.49474)]:
            self.assertAlmostEqual(IAPWS97(T=t,P=p).h,h,delta=5e-6)
        self.assertAlmostEqual(tsat_water(10e6),584.149488,delta=5e-7)
        for p in (4e6,6.5e6,10e6):
            self.assertGreater(latent_heat(p),0)
            self.assertGreater(h_feedwater(423.15,p),600)
            self.assertAlmostEqual(steam_production(1e7,p,423.15)*(h_sat_steam(p)-h_feedwater(423.15,p))*1000,1e7)
        for p in (0,3e6,11e6,float('nan')):
            with self.assertRaises(ValueError): tsat_water(p)
        with self.assertRaises(ValueError): h_feedwater(600,6.5e6)

    def test_output_volume_basis_is_saved_with_result(self):
        self.initialize()
        import json
        from subroutines.output_results import kolerg
        from web_backend.dataparser import parse_gastest
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'GASTEST.DAT'
            with path.open('w',encoding='utf-8') as output:
                kolerg(output,write_restart=False)
            text=path.read_text(encoding='utf-8')
            section=parse_gastest(path)['outlet_sections'][-1]
            self.assertAlmostEqual(section['normal_molar_volume_nm3_kmol'],NORMAL_MOLAR_VOLUME)
            self.assertAlmostEqual(section['total_wet_nms'],section['total_molar_kmol_h']*NORMAL_MOLAR_VOLUME/3600)
            # 移除新增元数据模拟历史文件；必须回到22.4，而不是读取当前common值。
            line=next(s for s in text.splitlines() if s.startswith('OUTLET_FLOWS_JSON: '))
            points=json.loads(line.split(': ',1)[1])
            for point in points.values():point.pop('normal_molar_volume_nm3_kmol')
            path.write_text(text.replace(line,'OUTLET_FLOWS_JSON: '+json.dumps(points)),encoding='utf-8')
            old=parse_gastest(path)['outlet_sections'][-1]
            self.assertEqual(old['normal_molar_volume_nm3_kmol'],22.4)

    def test_methane_viscosity_uses_correct_species_slot(self):
        self.initialize()
        y=np.zeros(9);y[2]=1
        expected=9.80665*1.06e-6*(400/273.15)**.760
        self.assertAlmostEqual(rates.FXMUG(y,400),expected,places=14)
        with self.assertRaises(ValueError):rates.FXMUG(np.zeros(9),400)

    def test_zero_volatiles_source_preserves_all_coal_elements(self):
        # 独立检查源项；不以此代替 XVM=0 全炉的收敛验收。
        self.initialize()
        from functions.gas_reactions import flucht
        common.XVM = 0
        flucht()
        actual = [common.WFC.sum(),
                  (common.RH2.sum() + common.RH2S.sum()) * common.MH2,
                  common.RO2.sum() * common.MO2, common.REN2.sum() * common.MN2,
                  common.RH2S.sum() * common.MS]
        expected = common.BSMS * np.array([common.ELC, common.ELH, common.ELO, common.ELN, common.ELS])
        np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-14)


if __name__ == '__main__':
    unittest.main()
