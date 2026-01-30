"""
The pyuson package.

Implements classes and functions to process raw data generated during high magnetic
field experiments.

This packages aims at laying the groundwork for data management and storage as well as
analysis routine structure.

Data management
---------------
Datasets are stored as Data objects defined in the `data` module. They are thin wrapper
around the NeXus objects provided by the `nexusformat` package. It results in standard
HDF5 files following the NeXus specification for interoperability.

Processors
----------
The `processor` module provides a base class `BaseProcessor`. It is used to provide a
bare processing structure and contains methods to load, process and write commonly used
data such as pickup-coil voltage from binary files. It also defines how to interact with
Data objects with getter- and setter-like methods. It is meant to be subclassed to build
specialized Processors.

A Processor dedicated to ultra-sound echoes experiments is implemented in the
`EchoProcessor()` class.

Config object
-------------
Processors are meant to be configured with human-readable TOML configuration file. The
`Config` class provides the means to load such files. It's in the `config` module. It
uses Pydantic models internally to handle data validation and (de)serialization.

Graphical User Interface
------------------------
A GUI built with Qt allows to interact with an `EchoProcessor` object interactively.

The package documentation page : https://himagnetos.pages.in2p3.fr/pyuson/index.html
See also : docstrings for modules, methods and functions.
"""

import logging
from pathlib import Path

import nexusformat.nexus as nx
from rich.logging import RichHandler

from . import config, data, sp, utils
from .processors import BaseProcessor, EchoProcessor

__all__ = [
    "BaseProcessor",
    "EchoProcessor",
    "config",
    "data",
    "utils",
    "sp",
]


# Setup logging
APPDIR = Path.home() / ".pyuson"
APPDIR.mkdir(parents=True, exist_ok=True)

fmt = "{asctime}.{msecs:3g} [{levelname}] : {message}"
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

console_handler = RichHandler(log_time_format="%H:%M:%S.%f")
console_handler.setLevel("DEBUG")

file_handler = logging.FileHandler(
    APPDIR / "processors.log", mode="a", encoding="utf-8"
)
file_handler.setLevel("INFO")

file_formatter = logging.Formatter(
    fmt,
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Configure NeXus
nx.nxsetconfig(compression=None, encoding="utf-8", lock=0, memory=8000, recursive=True)
