"""
Graphical user interface module.

It is not imported with the main `pyuson` package by default.
"""

from PyQt6 import QtWidgets

from . import protocols, widgets
from ._base import BaseMainWindow
from ._core import MainWindow

__all__ = ["BaseMainWindow", "MainWindow", "widgets", "protocols"]


def run(exec: bool = True):
    """
    Build and run the GUI.

    Set `exec=False` in an interactive prompt to interact with the GUI from the shell.
    """
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    if exec:
        app.exec()
    else:
        return win
