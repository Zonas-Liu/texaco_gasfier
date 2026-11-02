"""求解加速的数值等价性：局部物性、缓存及带状矩阵边界/失败行为。"""
import contextlib
import copy
import io
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import main as solver
from common.common_data import common
from functions.math_utils import solve_banded_blocks
from subroutines.initialization import eingab
from subroutines.output_results import entkol


class SolverPerformanceTests(unittest.TestCase):
    def setUp(self):
        common.reset()

    def initialize(self):
        with contextlib.redirect_stdout(io.StringIO()):
            eingab(str(ROOT / 'data/Datain0.dat'))

    def test_banded_matches_dense_with_upper_lower_and_pivoting(self):
        # 覆盖单块、等温 10 方程、60 格 11 方程和跨块主元交换。
        rng = np.random.default_rng(902)
        for size, cells in ((1, 2), (3, 1), (10, 4), (11, 60)):
            with self.subTest(size=size, cells=cells):
                common.reset()
                dense = np.zeros((size * cells, size * cells))
                rhs = rng.normal(size=(cells, size))
                for i in range(cells):
                    here = slice(i * size, (i + 1) * size)
                    block = 8 * np.eye(size) + rng.normal(size=(size, size))
                    dense[here, here] = block
                    common.BMAT[1:size+1, 1:size+1, i+1] = block
                    common.DMAT[1:size+1, i+1] = rhs[i]
                    if i + 1 < cells:
                        after = slice((i + 1) * size, (i + 2) * size)
                        lower, upper = rng.normal(size=(2, size, size))
                        dense[after, here], dense[here, after] = lower, upper
                        common.AMAT[1:size+1, 1:size+1, i+1] = lower
                        common.CMAT[1:size+1, 1:size+1, i+1] = upper
                if size == 1:
                    dense[0, 0] = common.BMAT[1, 1, 1] = 0
                blocks = [getattr(common, k).copy() for k in ('AMAT', 'BMAT', 'CMAT')]
                solve_banded_blocks(size, cells)
                result = common.DMAT[1:size+1, 1:cells+1].T.ravel()
                np.testing.assert_allclose(result, np.linalg.solve(dense, rhs.ravel()), rtol=1e-11, atol=1e-12)
                np.testing.assert_allclose(dense @ result, rhs.ravel(), rtol=1e-11, atol=1e-12)
                for k, before in zip(('AMAT', 'BMAT', 'CMAT'), blocks):
                    np.testing.assert_array_equal(getattr(common, k), before)

    def test_banded_rejects_singular_and_nonfinite(self):
        with self.assertRaises(np.linalg.LinAlgError):
            solve_banded_blocks(2, 2)
        for field in ('AMAT', 'BMAT', 'CMAT', 'DMAT'):
            with self.subTest(field=field):
                common.reset()
                array = getattr(common, field)
                array[(1,) * array.ndim] = np.nan
                with self.assertRaises(ValueError):
                    solve_banded_blocks(2, 2)

    def test_banded_with_large_equation_unit_differences(self):
        rng = np.random.default_rng(77)
        dense = rng.normal(size=(22, 22)) + 30 * np.eye(22)
        expected = rng.normal(size=22)
        dense *= np.geomspace(1e-12, 1e12, 22)[:, None]
        rhs = dense @ expected
        common.BMAT[1:12, 1:12, 1] = dense[:11, :11]
        common.BMAT[1:12, 1:12, 2] = dense[11:, 11:]
        common.AMAT[1:12, 1:12, 1] = dense[11:, :11]
        common.CMAT[1:12, 1:12, 1] = dense[:11, 11:]
        common.DMAT[1:12, 1:3] = rhs.reshape(2, 11).T
        solve_banded_blocks(11, 2)
        actual = common.DMAT[1:12, 1:3].T.ravel()
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)

    def test_enthalpy_cache_includes_water_solids_temperature_and_pressure(self):
        self.initialize()
        common.T[1:7] = [350, 350, 373.15, 373.1501, 1500, 1500]
        cache = {}
        for pressure in (4e6, 7e6):
            common.PWK = pressure
            entkol()
            expected = common.HENTH.copy(), common.DHDT.copy()
            common.HENTH.fill(0)
            common.DHDT.fill(0)
            entkol(cache=cache)
            np.testing.assert_array_equal(common.HENTH, expected[0])
            np.testing.assert_array_equal(common.DHDT, expected[1])

    def test_local_assembly_matches_full_property_recalculation(self):
        self.initialize()
        # 非均匀温度、残碳和流量，覆盖相邻格依赖及微量残碳。
        common.T[1:61] = np.linspace(1800, 1050, 60)
        common.X[1:61] = np.geomspace(.3, 1e-12, 60)
        common.WE[1:61] = np.linspace(4, 1.26, 60)
        for model in (0, 1):
            with self.subTest(model=model):
                common.KMODEL = model
                saved = copy.deepcopy(vars(common))
                kwargs = dict(xmass_func=solver.xmass, entfed_func=solver.entfed, entkol_func=solver.entkol,
                    xk1_func=solver.xk1, xk2_func=solver.xk2, xk3_func=solver.xk3,
                    xk4_func=solver.xk4, xk5_func=solver.xk5, xk6_func=solver.xk6,
                    a1_func=solver.A1, a2_func=solver.A2, a3_func=solver.A3, a4_func=solver.A4,
                    a5_func=solver.A5, phi_func=solver.PHI, ri_func=solver.RI,
                    enthp_func=solver.ENTHP, wdkr_func=solver.WDKR)
                solver.gasifier(**kwargs)
                matrices = {k: getattr(common, k).copy() for k in ('AMAT', 'BMAT', 'CMAT', 'DMAT')}
                vars(common).clear()
                vars(common).update(copy.deepcopy(saved))
                # 包装回调关闭局部/缓存优化，作为完整物性重算的独立对照。
                kwargs.update(xmass_func=lambda: solver.xmass(), entfed_func=lambda: solver.entfed(),
                              entkol_func=lambda: solver.entkol())
                solver.gasifier(**kwargs)
                for k, optimized in matrices.items():
                    np.testing.assert_array_equal(getattr(common, k), optimized, err_msg=k)


if __name__ == '__main__':
    unittest.main()
