"""
Shared Pydantic models for configuration.

Each model corresponds to a section in the configuration file.
"""

from typing import Any, Literal

from pydantic import BaseModel, ValidationInfo, field_validator


class File(BaseModel):
    """Binary or text file."""

    ext: str
    header: int

    # For binary file
    precision: int | None = None
    endian: Literal["<", ">"] | None = None
    order: Literal["C", "F"] | None = None

    # For text file
    delimiter: str | None = None

    @field_validator("precision", "endian", "order", "delimiter")
    @classmethod
    def disallow_none(
        cls,
        value: int | str | Literal["<", ">"] | Literal["C", "F"],
        info: ValidationInfo,
    ):
        """Prevent setting None explicitely."""
        assert value is not None, f"{info.field_name} can't be None"
        return value


class Parameters(BaseModel):
    """Parameters section, things related to the experiment itself."""

    pickup_surface: float
    pickup_number: int
    pickup_index: int


class Metadata(BaseModel):
    """Metadata section, defining how to read the metadata from files."""

    index_map: dict[str, int]
    conversion_map: dict[str, bool]


class Nexus(BaseModel):
    """The NeXus section, that sets the HDF5 group and dataset base names."""

    groups: dict[str, dict[str, Any]]
    datasets: dict[str, dict[str, Any]]
