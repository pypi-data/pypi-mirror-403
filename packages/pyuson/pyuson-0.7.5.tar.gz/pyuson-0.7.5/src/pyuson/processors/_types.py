"""Define Processor classes attribute types for type hints."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypedDict

import nexusformat.nexus as nx

from ..config import BaseConfig, Config


class BaseMetadataProcessor(TypedDict, total=False):
    """Base class to provide type hints for the metadata dict."""


class MetadataProcessor(TypedDict, total=False):
    """Base class to provide type hints for the metadata dict."""

    dt_acq: float
    dt_exp: float
    frame_duration: float
    last_analysis_window: Sequence[float]
    polarisation: str
    ref_off: int
    ref_on: int
    rf_frequency: float
    sample_angle: str
    sample_name: str
    temperature: float
    timestamp: str
    toffset_meas: float
    voffset: dict[str, float]
    vscale: dict[str, float]


class tBaseProcessor:
    """Base class to provide type hints for the BaseProcessor class."""

    _config_cls: Any
    _program_name: str
    _results_name: str
    _seed: int
    _serie_name: str

    cfg: BaseConfig
    data_directory: Path
    data_processed: nx.NXprocess
    data_raw: nx.NXdata
    expid: str
    idx_serie: int
    is_config_file: bool
    is_nexus_file: bool
    measurements: list[str]
    nxentry: nx.NXentry
    nxroot: nx.NXroot


class tEchoProcessor(tBaseProcessor):
    """Base class to provide type hints for the EchoProcessor class."""

    _config_cls: type[Config]
    _i_name: str
    _q_name: str

    analysis_window: Sequence[float]
    cfg: Config
    is_averaged: bool
    is_decimated: bool
    is_digital: bool | None
    is_meas_processed: bool
    is_rollmean: dict[str, bool]
    is_us: bool
    is_wfm: bool | None
    metadata: MetadataProcessor
    nframes: int
    npoints: int
    refname: str
    signame: str
