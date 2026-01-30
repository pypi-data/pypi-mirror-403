"""Define Config classes attribute types for type hints."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import (
    BinaryFile,
    Demodulation,
    Metadata,
    Nexus,
    Parameters,
    Settings,
    TextFile,
)


class tBaseConfig:
    """Base class to provide type hints for the BaseConfig class."""

    _cfg: BaseModel
    _default_file: Path | None
    _model: type[BaseModel]
    _overrides: dict[str, Any]
    _user_file: Path | None

    expid: str
    data_directory: Path

    filenames: dict[str, str | Path]
    measurements: dict[str, int]
    nx: dict[str, dict[str, Any]]
    nexus: Nexus

    def loads(cls, json_data: str | bytes, **kwargs): ...


class tConfig:
    """Base class to provide type hints for the Config class."""

    files: dict[str, BinaryFile | TextFile]
    parameters: Parameters
    settings: Settings
    metadata: Metadata
    demodulation: Demodulation | None
