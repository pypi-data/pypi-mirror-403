from typing import Protocol

import pyqtgraph as pg
from PyQt6.QtGui import QPen


class GraphsProtocol(Protocol):
    _mouse_pan_mode: bool
    field: pg.PlotWidget
    dfield: pg.PlotWidget

    pen_field: QPen
    pen_bdown: QPen
    pen_bup: QPen

    def clear_all_plots(self): ...
    def disable_rois(self): ...
    def enable_rois(self): ...
