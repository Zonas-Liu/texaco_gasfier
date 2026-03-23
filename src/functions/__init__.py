#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
函数模块 - 数学工具和反应速率计算
"""
from .math_utils import (
    gausll, matadd, matsub, matmult, matdiv, matums,
    kolon1, newtra, blktrd
)
from .gas_reactions import (
    xk1, xk2, xk3, xk4, xk5, xk6,
    flucht
)
from .reaction_rates import (
    A1, A2, A3, A4, A5,
    XKC_O2, XKC_H2O, XKC_CO2, XKC_H2,
    PHI, RI, WDKR, FXMUG, TPAR,
    ENTHP, FH2, FSOLID, FH2S, FO2, FC, FN2, FCO2, FCO, FCH4, FH2O,
    CMP, CMPS, CMPT, FPART
)

__all__ = [
    # 数学工具
    'gausll', 'matadd', 'matsub', 'matmult', 'matdiv', 'matums',
    'kolon1', 'newtra', 'blktrd',
    # 气相反应
    'xk1', 'xk2', 'xk3', 'xk4', 'xk5', 'xk6', 'flucht',
    # 碳反应
    'A1', 'A2', 'A3', 'A4', 'A5',
    'XKC_O2', 'XKC_H2O', 'XKC_CO2', 'XKC_H2',
    'PHI', 'RI', 'WDKR', 'FXMUG', 'TPAR',
    # 热力学
    'ENTHP', 'FH2', 'FSOLID', 'FH2S', 'FO2', 'FC', 'FN2', 'FCO2', 'FCO', 'FCH4', 'FH2O',
    'CMP', 'CMPS', 'CMPT', 'FPART'
]
