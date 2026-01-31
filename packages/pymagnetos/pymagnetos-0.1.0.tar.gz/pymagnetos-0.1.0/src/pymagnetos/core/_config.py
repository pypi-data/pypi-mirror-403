"""A generic Config base class to load TOML configuration file, using Pydantic."""

import logging
import tomllib
from pathlib import Path
from typing import Any, Literal

import tomlkit
from pydantic import BaseModel

from .config_models import File
from .utils import merge_dict_nested, strip_none_dict

# Only attributes than can be set for the Config class, otherwise they're set in the
# underlying Pydantic model
SELF_ATTRIBUTES = ("_cfg", "_model", "_user_file", "_default_file", "_overrides")

logger = logging.getLogger(__name__)


class BaseConfig:
    """
    Load and store parameters from user-defined configuration TOML file.

    It uses an underlying Pydantic model stored in the `_cfg` attribute. Setting an
    attribute will actually set it in the underlying model (raising an error if it is
    not defined).
    """

    def __init__(
        self,
        model: type[BaseModel],
        user_file: str | Path | None = None,
        default_file: str | Path | None = None,
        no_config: bool = False,
        **overrides: Any,
    ) -> None:
        """
        Load and store parameters from user-defined configuration TOML file.

        It requires a fully-defined Pydantic model.

        If `user_file` is a JSON file, the file is read and given to the Pydantic
        `model_validate_json()` method and the default file and overrides are ignored as
        it is assumed that a JSON configuration file comes from a previously serialized
        Config object.

        Otherwise, the configuration is set from, in this order of preference :
        1. **overrides
        2. Configuration file (`user_file`)
        3. Default configuration file (`default_file`). If not provided, the one bundled
        with the package is used.

        To load a JSON string (not a file), use the `loads()` class method.

        Parameters
        ----------
        model : pydantic.BaseModel
            A fully-defined (custom) Pydantic BaseModel.
        user_file : str or Path or None
            Path to a user configuration file.
        default_file : str, Path or None
            Path to the default configuration file used as fallback for missing
            parameters in the user file.
        no_config : bool, optional
            Initialize an empty Config object, with just the Pydantic model. Default is
            False.
        **overrides : overriding keyword arguments
            Keyword arguments that overwrite parameters from other sources.
        """
        self._model = model

        if no_config:
            self._default_file = None
            self._user_file = None
            self._overrides = overrides
        else:
            self._default_file = Path(default_file) if default_file else None
            self._user_file = Path(user_file) if user_file else None
            self._overrides = overrides
            self.load()
            self._patch_old_version()
            self._resolve_data_directory()
            self.build_filenames()
            self._greeting()

    def __getattr__(self, name: str, /) -> Any:
        """
        Return `name` from the underlying Pydantic model.

        This magic method is called only when an attribute is not found.
        """
        return getattr(self._cfg, name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        """
        Set `name` to `value` in the underlying Pydantic model.

        Only a restricted list of attributes can be set in the Config object itself (see
        `SELF_ATTRIBUTES`).
        """
        if name in SELF_ATTRIBUTES:
            super().__setattr__(name, value)
        else:
            setattr(self._cfg, name, value)

    def load(self) -> None:
        """Load a configuration file."""
        if self._default_file:
            default_config = tomllib.loads(self._default_file.read_text())
        else:
            default_config = dict()

        if self._user_file:
            if self._user_file.suffix == ".json":
                # Use Pydantic built-in method for JSON
                self._cfg = self._model.model_validate_json(self._user_file.read_text())
                return

            # Do not use tomlkit as it does not play nicely with Pydantic
            user_config = tomllib.loads(self._user_file.read_text())
            new_values = merge_dict_nested(user_config, default_config)
            # Restore the measurement section if it exists and not empty, because the
            # default names were merged
            if len(user_config.get("measurements", [])):
                new_values["measurements"] = user_config["measurements"]

        else:
            new_values = default_config

        if len(self._overrides) > 0:
            newer_values = merge_dict_nested(self._overrides, new_values)
        else:
            newer_values = new_values

        self._cfg = self._model(**newer_values)

    def _model_validate_json(self, json_data: str | bytes, **kwargs):
        """Read and set the configuration from a JSON string."""
        self._cfg = self._model.model_validate_json(json_data, **kwargs)
        self._greeting()

    def _greeting(self):
        logger.info(
            f"Configuration loaded for experiment: '{self.expid}'."
            f" Data directory: {self.data_directory}"
        )

    @classmethod
    def loads(cls, json_data: str | bytes, **kwargs):
        """
        Load a JSON-formatted string as the Config.
        
        Subclasses must implement this with the `_loads()` method and the relevant
        Pydantic model.
        """
        raise NotImplementedError(
            "Subclasses must implement this method with Pydantic model."
        )

    @classmethod
    def _loads(cls, model: type[BaseModel], json_data: str | bytes, **kwargs):
        """Create a Config object from a JSON string."""
        cfg = cls(model, no_config=True)
        cfg._model_validate_json(json_data, **kwargs)
        return cfg

    def build_filenames(self):
        """
        Build data file paths with the parameters found in `files`.

        Files names are built like this :
        {data_directory}/{expid}{ext}
        For oscilloscope data saved as Tektronix WFM files :
        + {data_directory}/{expid}_ch{n}{ext}
        """
        self.filenames = self._build_filenames(self.files)

    def resolve_nexus(self, serie_name: str):
        """
        Patch the `[nexus.groups]` section of the configuration.

        Replace "serie" in keys with `serie_name`, and if no name is specified for the
        main NXentry, set it to the dataset name.

        Parameters
        ----------
        serie_name : str
            Name of the series.
        """
        # Set the NXroot object name if not specified
        if not self.nexus.groups["root"]["name"]:
            self.nexus.groups["root"]["name"] = self.expid

        # Replace "serie" in key names with `serie_name`
        groups = self.nexus.groups.copy()
        for key in groups:
            self.nexus.groups[key.replace("serie", serie_name)] = self.nexus.groups.pop(
                key
            )

    def write(
        self,
        output_file: str | Path,
        format: Literal["guess", "toml", "json"] = "guess",
        overwrite: bool = False,
    ) -> bool:
        """
        Save current configuration to file.

        If the target file exists and `overwrite` is False (default), the file is not
        written. By default, the write mode is guessed from the file extension (json or
        toml), to force a mode, use the `format` keyword argument.

        Parameters
        ----------
        output_file : str or Path
            Path to the output file.
        format : {"guess", "json", "toml"}, optional
            Output file format. `"guess"` infers from file extension, this is the
            default.
        overwrite: bool, optional
            Whether to overwrite the output file if it exists. Default is False.
        """
        output_file = Path(output_file)
        # Check there is something to do
        if output_file.is_file() and not overwrite:
            logger.warning(f"{output_file.name} already exists, not saving.")
            return False
        if format not in ("guess", "toml", "json"):
            logger.error("File format not allowed, choose 'guess', 'toml' or 'json'.")
            return False

        # Determine file format
        if format == "guess":
            if output_file.suffix.endswith(".toml"):
                format = "toml"
            elif output_file.suffix.endswith(".json"):
                format = "json"
            else:
                logger.error(
                    f"Couldn't infer file format from file name: {output_file.name}"
                )
                return False

        try:
            if format == "toml":
                self._save_toml(output_file)
            elif format == "json":
                self._save_json(output_file)
            logger.info(f"Configuration saved at {output_file}.")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration file ({e}).")
            return False

    def model_dump_json(self, *args, **kwargs) -> str:
        """
        Dump the model in a JSON string.

        Just a wrapper for the underlying Pydantic model `model_dump_json()` method.
        Because of the `__getattr()__` magic method, this method is not mandatory. It is
        still implemented for clarity.
        """
        return self._cfg.model_dump_json(*args, **kwargs)

    def _patch_old_version(self):
        """
        Further adjustments to adapt to previous configuration file version.

        The 'filenames' section should be used to specify direct path to the data files.
        + 'base' is replaced by a more explicit 'expid' and set at the root of the file,
            outside of any section.
        + 'data_directory' should be set at the root of the file outside of any section.
        """
        if "base" in self.filenames:
            logger.warning(
                "Setting 'base' in the 'filenames' section is deprecated. "
                "Set the 'expid' parameter at the top of the file instead."
            )
            self.expid = str(self.filenames.pop("base"))
        if "data_directory" in self.filenames:
            logger.warning(
                "Setting 'data_directory' in the 'filenames' section is deprecated. "
                "Set the 'data_directory' parameter at the top of the file instead."
            )
            self.data_directory = Path(self.filenames.pop("data_directory"))

    def _resolve_data_directory(self):
        """
        Resolve the data directory entry from the configuration file.

        If it is "." or omitted, the directory where the file is is used. Otherwise,
        the location specified by the user is used.
        """
        if self.data_directory in (None, Path(".")) and self._user_file is not None:
            self.data_directory = self._user_file.parent
        elif isinstance(self.data_directory, str):
            self.data_directory = Path(self.data_directory)

    def _build_filenames(
        self, files_dic: dict[str, File]
    ) -> dict[str, Path]:
        """
        Build file names based on configuration.

        Files names are built like this :
        {data_directory}/{expid}{ext}
        For oscilloscope data saved as Tektronix WFM files :
        + {data_directory}/{expid}_ch{n}{ext}

        Parameters
        ----------
        files_dic : dict
        """
        # Resolve the various files that should be entries in the [files] section
        datadir = Path(self.data_directory)  # for convenience in this function
        filenames_dic = dict()
        for entry in files_dic:
            # Get file extension
            ext = files_dic[entry].ext
            if ext.endswith("wfm"):
                # Special case for oscilloscope : one file per channel, add a keyword
                filenames_dic[entry] = datadir / f"{self.expid}_!CHANNELID{ext}"

            else:
                filenames_dic[entry] = datadir / f"{self.expid}{ext}"

        return filenames_dic

    def _save_json(self, output_file: Path):
        """Save current configuration to a JSON file."""
        output_file.write_text(self.model_dump_json(), encoding="utf8")

    def _save_toml(self, output_file: Path):
        """Save current configuration to a TOML file."""
        output_file.write_text(
            tomlkit.dumps(strip_none_dict(self._cfg.model_dump(mode="json"))),
            encoding="utf8",
        )
