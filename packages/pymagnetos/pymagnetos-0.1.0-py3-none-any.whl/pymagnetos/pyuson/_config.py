"""Config class for the EchoProcessor object."""

from pathlib import Path
from typing import Any

from ..core import BaseConfig
from ._config_models import EchoConfigurationModel

CONFIG_DEFAULT = Path(__file__).parent / "assets" / "config_default.toml"


class EchoConfig(BaseConfig):
    def __init__(
        self,
        user_file: str | Path | None = None,
        default_file: str | Path | None = None,
        **overrides: Any,
    ) -> None:
        if not default_file:
            default_file = CONFIG_DEFAULT

        super().__init__(EchoConfigurationModel, user_file, default_file, **overrides)

    @classmethod
    def loads(cls, json_data: str | bytes, **kwargs) -> "EchoConfig":
        return super()._loads(EchoConfigurationModel, json_data, **kwargs)
