"""ParameterTree content for pyuson."""

import numpy as np

from pymagnetos.core.gui.widgets import BaseParamContent


class ParamContent(BaseParamContent):
    # List of parameters that will need to be parsed from string to list
    PARAMS_TO_PARSE = ["frame_indices", "range_baseline", "analysis_window"]

    # Define parameters in the "Parameters" section
    children_parameters = [
        dict(
            name="pickup_surface",
            type="float",
            limits=[0, np.inf],
            value=None,
            suffix="m²",
            siPrefix=False,
            readonly=True,
            title="Pickup surface",
        ),
        dict(
            name="pickup_samplerate",
            type="float",
            limits=[0, np.inf],
            value=250e3,
            step=1e3,
            suffix="Hz",
            siPrefix=True,
            readonly=True,
            title="Pickup sample rate",
        ),
        dict(
            name="sample_length",
            type="float",
            limits=[0, np.inf],
            value=None,
            step=0.5e-3,
            suffix="m",
            siPrefix=True,
            readonly=True,
            title="Sample length",
        ),
        dict(
            name="sample_speed",
            type="float",
            limits=[0, np.inf],
            value=None,
            step=0.5e3,
            suffix="m/s",
            siPrefix=True,
            readonly=True,
            title="Sample speed",
        ),
        dict(
            name="detection_mode",
            type="list",
            limits=["reflection", "transmission"],
            value="reflection",
            readonly=True,
            title="Detection mode",
        ),
    ]

    # Define parameters in the "Settings" section (editable)
    children_settings = [
        dict(
            name="echo_index",
            type="int",
            limits=[1, np.inf],
            step=1,
            value=1,
            title="Echo index",
        ),
        dict(name="frame_indices", type="str", title="Displayed frames"),
        dict(
            name="rolling_mean_wlen",
            type="int",
            limits=[0, np.inf],
            step=1,
            value=0,
            title="Rolling mean window length",
        ),
        dict(
            name="rolling_mean_subsample",
            type="bool",
            limits=[True, False],
            value=False,
            title="Rolling mean subsampling",
        ),
        dict(name="range_baseline", type="str", value="", title="Range baseline"),
        dict(
            name="analysis_window", type="str", value="", title="Analysis time window"
        ),
        dict(
            name="max_phase_jump",
            type="float",
            value=0.5,
            step=0.1,
            limits=[0, np.inf],
            title="Max. phase jump (* π)",
        ),
    ]

    children_demodulation = [
        dict(
            name="f0",
            type="float",
            limits=[0, np.inf],
            step=10e6,
            value=0,
            suffix="Hz",
            siPrefix=True,
            title="f0",
        ),
        dict(
            name="fft_nframes",
            type="int",
            limits=[0, np.inf],
            step=10,
            value=0,
            title="FFT : nframes",
        ),
        dict(
            name="detrend",
            type="bool",
            limits=[False, True],
            value=False,
            title="FFT : detrend",
        ),
        dict(
            name="findsig_nframes",
            type="int",
            limit=[0, np.inf],
            step=10,
            value=0,
            title="Ref. finder : nframes",
        ),
        dict(
            name="findsig_nstd",
            type="float",
            limit=[0, np.inf],
            step=0.1,
            value=1.5,
            title="Ref. finder : nstd",
        ),
        dict(
            name="findsig_extend",
            type="float",
            limit=[-np.inf, np.inf],
            step=0.01,
            value=-0.10,
            title="Ref. finder : ext. frac.",
        ),
        dict(
            name="chunksize",
            type="int",
            limits=[-1, np.inf],
            step=100,
            value=0,
            title="Chunk size",
        ),
        dict(
            name="decimate_factor",
            type="int",
            limits=[0, np.inf],
            step=1,
            value=0,
            title="Decimation factor",
        ),
        dict(
            name="filter_order",
            type="int",
            limits=[1, np.inf],
            step=1,
            value=10,
            title="Filter order",
        ),
        dict(
            name="filter_fc",
            type="float",
            limits=[0, np.inf],
            step=10e6,
            value=300e6,
            suffix="Hz",
            siPrefix=True,
            title="Filter cut-off frequency",
        ),
        dict(name="find_f0", type="action", title="Find f0"),
        dict(name="demodulate", type="action", title="Demodulate"),
    ]
