"""Pydantic models for configuration."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class BinaryFile(BaseModel):
    """Binary files (.bin, for pickup and Lecroy oscilloscope)."""

    ext: str
    header: int
    precision: int
    endian: Literal["<", ">"]
    order: Literal["C", "F"]


class TextFile(BaseModel):
    """For text file (.txt, for metadata and frame onsets for Lecroy oscilloscope)."""

    ext: str
    header: int
    delimiter: str


class Parameters(BaseModel):
    """Parameters section, things related to the experiment itself."""

    pickup_surface: float
    pickup_samplerate: float
    sample_length: float
    sample_speed: float
    detection_mode: str
    pickup_number: int
    pickup_index: int
    logamp_slope: float


class Settings(BaseModel):
    """Settings section, things related to the analysis."""

    echo_index: int
    frame_indices: Sequence[int]
    rolling_mean_wlen: int
    rolling_mean_subsample: bool
    range_baseline: Sequence[float]
    analysis_window: Sequence[float]
    max_phase_jump: float


class Metadata(BaseModel):
    """Metadata section, defining how to read the metadata from files."""

    index_map: dict[str, int]
    conversion_map: dict[str, bool]


class Demodulation(BaseModel):
    """Demodulation section, things related to the digital demodulation process."""

    f0: float
    fft_nframes: int
    detrend: bool
    findsig_nframes: int
    findsig_nstd: float
    findsig_extend: float
    chunksize: int
    decimate_factor: int
    filter_order: int
    filter_fc: float


class Nexus(BaseModel):
    """The NeXus section, that sets the HDF5 group and dataset base names."""

    groups: dict[str, dict[str, Any]]
    datasets: dict[str, dict[str, Any]]


class EchoConfiguration(BaseModel):
    """A Model specialized for ultra-sound echoes experiment."""

    expid: str
    data_directory: Path

    filenames: dict[str, str | Path] = dict()

    files: dict[str, BinaryFile | TextFile]

    measurements: dict[str, int]

    parameters: Parameters
    settings: Settings

    metadata: Metadata

    nx: dict[str, dict[str, Any]]
    nexus: Nexus

    demodulation: Demodulation | None = None

    model_config = ConfigDict(validate_assignment=True)
