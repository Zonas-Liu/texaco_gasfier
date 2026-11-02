"""可追溯的物理常数与摩尔质量（kg/kmol），见 docs/PHYSICAL_CONSTANTS.md。

CIAAW 2024 abridged standard atomic weights，天然同位素组成存在范围，不能任意补位。
NIST/CODATA 2022；标方明确为理想气体273.15 K、101325 Pa，不采用1 bar标态。
TEXACO 原Fortran对照使用独立 legacy 配置，禁止把两套质量基准混在一次运行中。
"""
import math
import numpy as np

ATOMIC_WEIGHTS = {'H': 1.0080, 'C': 12.011, 'N': 14.007, 'O': 15.999,
                  'S': 32.06, 'Si': 28.085}
LEGACY_ATOMIC_WEIGHTS = {'H': 1.0, 'C': 12.0, 'N': 14.0, 'O': 16.0,
                         'S': 32.0, 'Si': 28.0}
GAS_SPECIES = ('O2', 'CH4', 'CO', 'CO2', 'H2S', 'H2', 'N2', 'H2O')
FORMULAS = {'O2': {'O': 2}, 'CH4': {'C': 1, 'H': 4}, 'CO': {'C': 1, 'O': 1},
    'CO2': {'C': 1, 'O': 2}, 'H2S': {'H': 2, 'S': 1}, 'H2': {'H': 2},
    'N2': {'N': 2}, 'H2O': {'H': 2, 'O': 1}, 'C': {'C': 1},
    'SiO2': {'Si': 1, 'O': 2}, 'TAR': {'C': 1, 'H': .689, 'O': .014}}
BOLTZMANN = 1.380649e-23  # J/K，SI定义值
AVOGADRO = 6.02214076e23  # 1/mol，SI定义值
PLANCK = 6.62607015e-34  # J s，SI定义值
LIGHT_SPEED = 299792458.0  # m/s，SI定义值
R_MOLAR = BOLTZMANN * AVOGADRO  # J/(mol K)
R_KMOL = R_MOLAR * 1000
ATM_PA = 101325.0  # 标准大气压，精确
NORMAL_T_K = 273.15  # 摄氏/开氏零点差，精确
STANDARD_GRAVITY = 9.80665  # m/s²，约定标准重力，不表示当地实测值
NORMAL_MOLAR_VOLUME = R_KMOL * NORMAL_T_K / ATM_PA  # Nm³/kmol
STEFAN_BOLTZMANN = 2 * math.pi**5 * BOLTZMANN**4 / (15 * PLANCK**3 * LIGHT_SPEED**2)
THERMOCHEMICAL_CALORIE = 4.184  # J/cal_th，精确
# 原热容系数的cal定义未有完整出处，不将4.186擅改为另一种cal制。
LEGACY_HEAT_CAPACITY_CAL_FACTOR = 4.186


def molar_masses(legacy=False):
    atoms = LEGACY_ATOMIC_WEIGHTS if legacy else ATOMIC_WEIGHTS
    masses = {name: sum(atoms[e] * n for e, n in formula.items()) for name, formula in FORMULAS.items()}
    if legacy:
        masses['TAR'] = 12.913
    return masses


def configure(common):
    """解析KMODEL后、计算进料源项之前统一选择常数；保留1-based气体数组约定。"""
    legacy = getattr(common, 'KMODEL', 0) == 0
    atoms = LEGACY_ATOMIC_WEIGHTS if legacy else ATOMIC_WEIGHTS
    masses = molar_masses(legacy)
    for element, value in atoms.items():
        setattr(common, 'M' + element.upper(), value)
    for species in GAS_SPECIES:
        setattr(common, 'M' + species, masses[species])
    common.MASH = masses['SiO2']  # 仅灰比焓的SiO2代理；不是实际灰平均分子量
    common.XMTAR = masses['TAR']  # 伪组分CH0.689O0.014，非实测焦油分子量
    common.XMOL = np.array([masses[g] for g in GAS_SPECIES] + [masses['C'], common.MASH])
    common.G = 9.801 if legacy else STANDARD_GRAVITY
    common.RAG = 8314.3 if legacy else R_KMOL
    common.RM = 8.3143 if legacy else R_MOLAR
    common.RCAL = 1.987 if legacy else R_MOLAR / THERMOCHEMICAL_CALORIE
    common.PI = 3.1415926 if legacy else math.pi
    common.P0 = ATM_PA
    common.SIGMA_SB = 5.672e-8 if legacy else STEFAN_BOLTZMANN
    common.VM_NORMAL = 22.4 if legacy else NORMAL_MOLAR_VOLUME
    common.CONSTANTS_BASIS = 'fortran-legacy' if legacy else 'CIAAW-2024-CODATA-2022'
