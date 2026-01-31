"""Pydantic models for the EchoProcessor Config."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..core import config_models


class Parameters(config_models.Parameters):
    """Parameters section, things related to the experiment itself."""

    pickup_samplerate: float
    sample_length: float
    sample_speed: float
    detection_mode: str
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


class EchoConfigurationModel(BaseModel):
    """A Model specialized for ultra-sound echoes experiment."""

    expid: str
    data_directory: Path

    filenames: dict[str, str | Path] = dict()

    files: dict[str, config_models.File]

    measurements: dict[str, int]

    parameters: Parameters
    settings: Settings

    metadata: config_models.Metadata

    nx: dict[str, dict[str, Any]]
    nexus: config_models.Nexus

    demodulation: Demodulation | None = None

    model_config = ConfigDict(validate_assignment=True)
