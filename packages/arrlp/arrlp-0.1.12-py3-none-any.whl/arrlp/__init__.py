#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-28
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : arrLP

"""
A library providing custom functions for arrays.
"""



# %% Source import
sources = {
'compress': 'arrlp.modules.compress_LP.compress',
'convolve': 'arrlp.modules.convolve_LP.convolve',
'coordinates': 'arrlp.modules.coordinates_LP.coordinates',
'correlate': 'arrlp.modules.correlate_LP.correlate',
'kernel': 'arrlp.modules.kernel_LP.kernel',
'relabel': 'arrlp.modules.relabel_LP.relabel',
'xp': 'arrlp.modules.xp_LP.xp'
}



# %% Hidden imports
if False :
    import arrlp.modules.compress_LP.compress
    import arrlp.modules.convolve_LP.convolve
    import arrlp.modules.coordinates_LP.coordinates
    import arrlp.modules.correlate_LP.correlate
    import arrlp.modules.kernel_LP.kernel
    import arrlp.modules.relabel_LP.relabel
    import arrlp.modules.xp_LP.xp



# %% Lazy imports
from corelp import getmodule
__getattr__, __all__ = getmodule(sources)