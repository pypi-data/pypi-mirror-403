"""Protocols defining the requirements for the GUI components."""

from ._wbatch import BatchProcessingProtocol
from ._wbuttons import MainButtonsProtocol
from ._wconfiguration import ConfigurationProtocol
from ._wfiles import FileBrowserProtocol
from ._worker import DataWorkerProtocol
from ._wplots import GraphsProtocol

__all__ = [
    "BatchProcessingProtocol",
    "DataWorkerProtocol",
    "MainButtonsProtocol",
    "ConfigurationProtocol",
    "FileBrowserProtocol",
    "GraphsProtocol",
]
