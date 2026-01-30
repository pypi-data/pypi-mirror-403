from typing import Protocol

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtBoundSignal


class MainButtonsProtocol(Protocol):
    sig_load: pyqtBoundSignal
    sig_save_nexus: pyqtBoundSignal
    button_load: QtWidgets.QPushButton

    def disable_buttons(self): ...
    def enable_buttons(self): ...
