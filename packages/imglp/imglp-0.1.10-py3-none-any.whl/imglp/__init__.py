#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-28
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : imgLP

"""
A library that provides tools for image processing.
"""



# %% Source code
sources = {
'crosscorrelate': 'imglp.modules.crosscorrelate_LP.crosscorrelate',
'drift': 'imglp.modules.drift_LP.drift'
}



# %% Lazy imports
from corelp import getmodule
__getattr__, __all__ = getmodule(sources)