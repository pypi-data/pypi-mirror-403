"""Pydantic models for the TDOProcessor Config."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..core.config_models import File, Metadata, Nexus, Parameters


class Settings(BaseModel):
    """Settings for signal extraction, analysis and plotting."""

    # Extraction
    max_time: float

    spectro_nperseg: int
    spectro_win_size: int
    spectro_noverlap: int

    barycenters_fwindow: float
    barycenters_fast: bool

    time_offset: float

    # Analysis
    poly_window: Sequence[float]
    poly_deg: int
    npoints_interp_inverse: int
    fft_window: Sequence[float]
    fft_pad_mult: int
    max_bfreq: float

    # Display
    offset: float


class TDOConfiguration(BaseModel):
    """A model specialized for TDO experiments."""

    expid: str
    data_directory: Path

    filenames: dict[str, str | Path] = dict()

    files: dict[str, File]

    measurements: dict[str, int]

    parameters: Parameters
    settings: Settings

    metadata: Metadata

    nx: dict[str, dict[str, Any]]
    nexus: Nexus

    model_config = ConfigDict(validate_assignment=True)
