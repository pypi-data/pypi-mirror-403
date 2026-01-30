from pathlib import Path
from typing import Protocol

from PyQt6.QtCore import QThread, pyqtBoundSignal

from ...processors import BaseProcessor


class DataWorkerProtocol(Protocol):
    is_dataloaded: bool

    sig_load_finished: pyqtBoundSignal
    sig_align_finished: pyqtBoundSignal
    sig_batch_progress: pyqtBoundSignal
    sig_batch_finished: pyqtBoundSignal
    sig_save_nexus_finished: pyqtBoundSignal

    proc: BaseProcessor

    def align_field(self): ...
    def load_data(self): ...
    def batch_process(self, *args): ...
    def save_as_nexus(self, fname: str | Path): ...

    def moveToThread(self, thread: QThread | None): ...
    def deleteLater(self): ...
