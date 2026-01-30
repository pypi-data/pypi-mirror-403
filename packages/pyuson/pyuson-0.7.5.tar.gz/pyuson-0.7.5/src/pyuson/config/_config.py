from pathlib import Path
from typing import Any

from ._base import BaseConfig
from ._types import tConfig
from .models import EchoConfiguration

CONFIG_DEFAULT = Path(__file__).parent.parent / "assets" / "config_default.toml"


class Config(tConfig, BaseConfig):
    def __init__(
        self,
        user_file: str | Path | None = None,
        default_file: str | Path | None = None,
        **overrides: Any,
    ) -> None:
        if not default_file:
            default_file = CONFIG_DEFAULT

        super().__init__(EchoConfiguration, user_file, default_file, **overrides)

    @classmethod
    def loads(cls, json_data: str | bytes, **kwargs) -> "Config":
        return super()._loads(EchoConfiguration, json_data, **kwargs)
