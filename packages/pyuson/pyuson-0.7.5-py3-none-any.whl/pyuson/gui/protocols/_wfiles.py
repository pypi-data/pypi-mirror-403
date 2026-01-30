from typing import Protocol

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtBoundSignal

from ..widgets import FileBrowser


class FileBrowserProtocol(Protocol):
    sig_file_selected: pyqtBoundSignal
    sig_autoload_changed: pyqtBoundSignal

    file_browser: FileBrowser

    checkbox_autoload_data: QtWidgets.QCheckBox
