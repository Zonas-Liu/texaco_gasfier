"""界面单位与 Fortran 输入单位之间的转换；不改变历史文件的绝压/K 口径。"""
from common.physical_constants import ATM_PA


def display_spec(unit):
    """display = model * scale + offset。"""
    if unit == 'Pa':
        return {'unit': 'MPaG', 'scale': 1e-6, 'offset': -ATM_PA / 1e6}
    if unit == 'K':
        return {'unit': '℃', 'scale': 1.0, 'offset': -273.15}
    return {'unit': '℃' if unit in ('°C', 'C') else unit, 'scale': 1.0, 'offset': 0.0}


def to_display(value, unit):
    spec = display_spec(unit)
    return value * spec['scale'] + spec['offset']


def to_model(value, unit):
    spec = display_spec(unit)
    return (value - spec['offset']) / spec['scale']
