#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-28
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : plotLP

"""
A library wrapper around matplotlib for custom plots.
"""



# %% Source code
sources = {
'StyledAxes': 'plotlp.modules.StyledAxes_LP.StyledAxes',
'StyledFigure': 'plotlp.modules.StyledFigure_LP.StyledFigure',
'cmap': 'plotlp.modules.cmap_LP.cmap',
'color': 'plotlp.modules.color_LP.color',
'figure': 'plotlp.modules.figure_LP.figure',
'imgfigure': 'plotlp.modules.imgfigure_LP.imgfigure',
'plt': 'plotlp.modules.plt_LP.plt',
'style': 'plotlp.modules.style_LP.style',
'subplots': 'plotlp.modules.subplots_LP.subplots'
}



# %% Lazy imports
from corelp import getmodule
__getattr__, __all__ = getmodule(sources)