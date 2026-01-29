#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-28
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : plotLP

"""
A library wrapper around matplotlib for custom plots.
"""



# %% Source import
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



# %% Hidden imports
if False :
    import plotlp.modules.StyledAxes_LP.StyledAxes
    import plotlp.modules.StyledFigure_LP.StyledFigure
    import plotlp.modules.cmap_LP.cmap
    import plotlp.modules.color_LP.color
    import plotlp.modules.figure_LP.figure
    import plotlp.modules.imgfigure_LP.imgfigure
    import plotlp.modules.plt_LP.plt
    import plotlp.modules.style_LP.style
    import plotlp.modules.subplots_LP.subplots



# %% Lazy imports
from corelp import getmodule
__getattr__, __all__ = getmodule(sources)