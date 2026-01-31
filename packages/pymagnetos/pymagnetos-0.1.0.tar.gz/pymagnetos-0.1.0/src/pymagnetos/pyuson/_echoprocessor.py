"""The EchoProcessor class for ultra-sound echoes experiments."""

import logging
import os
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Literal, Self

import nexusformat.nexus as nx
import numpy as np
from fftekwfm import TekWFM
from scipy import signal

from ..core import BaseProcessor, sp
from ..log import configure_logger
from ._config import EchoConfig

# Name of the analysis serie, here it correspond to an echo index
SERIE_NAME = "echo"
# Measurements names to use
REFNAME = "reference"
I_NAME_ANALOG = "in_phase"
Q_NAME_ANALOG = "out_phase"
I_NAME_DIGITAL = "in_phase_demod"
Q_NAME_DIGITAL = "out_phase_demod"
# To guess if time is in microseconds, set approx. duration of a frame in seconds
# If the max is found 1000x above, it is guessed that the vector is in microseconds
FRAME_TIMESCALE = 10e-6

logger = logging.getLogger(__name__)


class EchoProcessor(BaseProcessor):
    """Processor class for ultra-sound echoes experiments."""

    def __init__(self, *args, digital: bool | None = None, **kwargs) -> None:
        """
        Processor class for ultra-sound echoes experiments.

        Provide methods for :
        - Loading data and metadata,
        - Reshape and format data,
        - Preprocessing : demodulation, decimation and/or smoothing (with rolling window
            average)
        - Averaging in a time-window,
        - Derive ultra-sound waves attenuation and phase-shift in the sample during a
            magnetic field shot.

        The data can be loaded from both binary files from the LabVIEW program or
        Tektronix WFM files. Digital demodulation is possible when necessary.

        In any case, the raw data is assumed to be in the form of several frames paving
        the experiment duration. Each frame should contain the same number of samples.
        This is all read from the inputs files :

        With the original LabVIEW program :
        - sample.bin : raw binary file from the LabVIEW program with the measured
            channels,
        - sample.txt : frames onsets, with metadata in the header. The header is
            specified in the configuration file,
        - sample-pickup.bin : raw binary file from the LabVIEW program with pickup coil
            voltage.

        With the Tektronix oscilloscope :
        - sample_ch1.wfm, sample_ch2.wfm, ... : Tektronix WFM files with the measured
            channels,
        - sample.txt : metadata only, the frames onsets are read from the WFM file,
        - sample-pickup.bin : see above.

        Parameters
        ----------
        *args : passed to `BaseProcessor()`
        digital : bool or None, optional
            Force digital mode by setting this parameter to True or to analog mode with
            False. None will attempt to determine this automatically from the
            configuration file, this is the default behavior.
        **kwargs : passed to `BaseProcessor()`
        """
        configure_logger(logger, "pyuson.log")

        # Get the Config object
        self._config_cls = EchoConfig

        # Prepare internals names
        self._serie_name = SERIE_NAME

        # Use digital mode or not, or automatically detect it from configuration
        self.is_digital = digital

        # Convenience attributes (might be overidden upon loading)
        self.nframes = 0
        self.npoints = 0

        super().__init__(*args, **kwargs)

        # Initialize flags
        if not self.is_nexus_file:
            self._init_flags()

            # Additional initializations
            if self.is_digital:
                self._init_digital()
            else:
                self._i_name = I_NAME_ANALOG
                self._q_name = Q_NAME_ANALOG

            # Initialize metadata dict for WFM file (will be filled when loading data)
            self.metadata["vscale"] = dict()
            self.metadata["voffset"] = dict()

    @property
    def expid(self) -> str:
        """Experiment ID, linked to the Config object."""
        return self.cfg.expid

    @expid.setter
    def expid(self, value: str):
        """
        Setter for `expid`.

        The `expid` attribute of the configuration is updated. The filenames are
        rebuilt.
        """
        self.cfg.expid = value
        self.cfg.build_filenames()
        self._reinit()

    @property
    def data_directory(self) -> Path:
        """Data directory, linked to the Config object."""
        return self.cfg.data_directory

    @data_directory.setter
    def data_directory(self, value: str | Path):
        """
        Setter for `data_directory`.

        The `data_directory` attribute of the configuration is updated. The filenames
        are rebuilt.
        """
        self.cfg.data_directory = Path(value)
        self.cfg.build_filenames()
        self._reinit()

    @property
    def idx_serie(self) -> int:
        """
        Track the current analyzed echo.

        The returned value is read from the "echo_index" parameter in the "settings"
        section of the configuration.
        """
        return self.cfg.settings.echo_index

    @idx_serie.setter
    def idx_serie(self, value: int):
        """
        Setter for `idx_serie`.

        The "echo_index" parameter in the "settings" section of the configuration is
        updated.
        """
        self.cfg.settings.echo_index = value

    @property
    def analysis_window(self) -> Sequence[float]:
        """
        Time-range in which averaging is performed.

        The returned value is read from the "analysis_window" parameter in the
        "settings" section of the configuration.
        """
        return self.cfg.settings.analysis_window

    @analysis_window.setter
    def analysis_window(self, value: Sequence[float]):
        """
        Setter for `idx_serie`.

        The "analysis_window" parameter in the "settings" section of the configuration
        is updated.
        """
        self.cfg.settings.analysis_window = value

    def _init_flags(self):
        """Set up flags."""
        # Tektronix WFM files or LabVIEW binary file
        self.is_wfm = False
        # Measurement time vector is in microseconds
        self.is_us = False
        # Averaged values were computed or updated
        self.is_averaged = False
        # Where the measurements are stored ('data_raw' or 'data_processed')
        self.is_meas_processed = False
        # Where the corresponding time vector is stored ('data_processed' if decimation
        # is used)
        self.is_decimated = False

        # Determine analog or digital mode, if needed
        if (self.is_digital is None) and self.is_config_file:
            self.is_digital = self._check_digital()

        # Moving mean was performed, if it was, use the smoothed data in data_processed
        self.is_rollmean = {m: False for m in self.measurements}

    def _guess_flags(self):
        """Attempt to guess flags from data after loading a NeXus file."""
        self.is_wfm = None  # no files so irrelevant
        self.is_us = self._check_measurement_time_us()
        self.is_averaged = self._check_averaged()

        if self.is_digital is None:
            # It was not set by the user when initializing the Processor object
            self.is_digital = self._check_digital()

        if self.is_digital:
            self._init_digital()  # fills is_meas_processed
            self._sig_name = self._get_signal_name()
        else:
            self.is_meas_processed = False

        self.is_decimated = self._check_time_subsampled()
        self.is_rollmean = self._check_rollmean()

    def _init_digital(self):
        """Additional initializations for digital mode."""
        # Prepare internal names
        self._ref_name = REFNAME
        self._i_name = I_NAME_DIGITAL
        self._q_name = Q_NAME_DIGITAL
        # Get signal name
        if self.is_config_file:
            # If instantiated with configuration file
            self._sig_name = self._get_signal_name()
        else:
            self._sig_name = "SIG_NAME_NOT_SET"  # might be set later

        # Update flags
        self.is_digital = True

        # Add a seed based on unix time for frame selection
        self._seed = int(time.time())

        # Update measurements names, eg. the actual measurements used in computation and
        # not orignal "signal" and "reference"
        self.measurements = [self._i_name, self._q_name]
        # Update flags
        self.is_rollmean = {m: False for m in self.measurements}  # the keys changed
        self.is_meas_processed = True

    def _reinit(self):
        """Re-initialize data objects."""
        super()._reinit()
        if self.is_digital:
            self._init_digital()

        self.metadata["vscale"] = dict()
        self.metadata["voffset"] = dict()

        logger.info(f"Experiment ID set to '{self.expid}'.")

    def _get_signal_name(self) -> str:
        """Determine signal name from configuration file measurements."""
        signames = [*{*self.cfg.measurements.keys()} - {self._ref_name}]
        if len(signames) != 1:
            raise ValueError(
                "Config file : Measurements should have 2 and only 2 entries."
            )
        return signames[0]

    @staticmethod
    def _load_metadata(
        filename: str | Path,
        header_map: dict[str, int],
        conversion_map: dict[str, bool],
    ) -> dict[str, float | str]:
        """
        Read metadata from the header of the text file with the frames onsets.

        `header_map` is a dict mapping a metadata to a line number in the file
        (0-based).

        `conversion_map` is a dict specifying if those metadata should be
        converted to numerical values.

        Parameters
        ----------
        filename : str | Path
            Full path to the text file with metadata.
        header_map : dict
            Maps a metadata name to a line number in the file (0-based).
        conversion_map : dict
            Maps a metadata name to a booelan, requiring if the metadata should be
            converted to a numerical value or kept as-is.

        Returns
        -------
        metadata : dict
            {metadata name : value}
        """
        # Determine how many lines-long the header is
        nlines_header = max(header_map.values()) + 1

        # Check file exists
        if not os.path.isfile(filename):
            logger.warning(
                f"{os.path.basename(filename)} : metadata file does not exist."
            )
            return {}

        # Read first lines
        with open(filename) as fid:
            header = [next(fid) for _ in range(nlines_header)]

        # Collect
        metadata = {key: header[idx] for key, idx in header_map.items()}

        # Convert numerical values
        metadata = {
            key: float(value) if conversion_map[key] else value.strip("\n")
            for key, value in metadata.items()
        }

        return metadata

    @staticmethod
    def _load_frame_onsets(
        filename: str | Path, nlines_header: int, delimiter: str
    ) -> np.ndarray:
        """
        Read frame onsets in the reference time text file.

        Parameters
        ----------
        filename : str | Path
            Full path to the reference time text file.
        nlines_header : int
            Number of lines to ignore to skip the header.
        delimiter : str
            Delimiter in the text file.

        Returns
        -------
        frames_onsets : np.ndarray
            Vector with frames onsets.
        """
        frame_onsets = np.loadtxt(
            filename,
            skiprows=nlines_header,
            delimiter=delimiter,
            usecols=0,
            dtype=float,
        )
        return frame_onsets

    def _load_oscillo_bin(
        self,
        filename: str | Path,
        nchannels: int,
        precision: int,
        endian: Literal["<", ">"] = "<",
        order: Literal["F", "C"] = "F",
    ) -> np.ndarray:
        """
        Load oscilloscope binary file.

        Loaded data is reshaped and transposed so that time series corresponding to one
        channel correspond to one row (so that it can be easily unpacked). Note that the
        time serie is 1D : all frames are stored one after the other and need to be
        reshaped.

        Parameters
        ----------
        filename : str | Path
            Full path to binary file.
        nchannels : int
            Number of channels.
        precision : int
            Byte precision.
        endian : {"<", ">"}, optional
            "<" for little endian, ">" for big endian. Default is "<".
        order : {"F", "C"}, optional
            Array order, "F" for Fortran, "C" for C. Default is "F".

        Returns
        -------
        oscillo_data np.ndarray
            Shape nchannels * nsamples.

        Raises
        ------
        ValueError
            If it can't be reshaped to the expected shape, raises an error.
        """
        if not isinstance(filename, Path):
            filename = Path(filename)

        # Load data
        data = self.load_bin(filename, precision, endian)

        # Reshape data as an array with a column per channel
        filesize = filename.stat().st_size  # get total size in bytes

        # Normally there are filesize bytes in total in the file, precision bytes per
        # float, so 12 bytes per sample (4 bytes * 3 channels), hence
        # filesize / (nchannels * precision) columns and nchannels lines
        # If the data is correct, it should be possible to reshape like this, as all
        # channels have the same number of time points.
        ncolumns = int(filesize / (nchannels * precision))
        try:
            data = data.reshape((ncolumns, nchannels), order=order).astype(float)
        except ValueError:
            raise ValueError("Missing samples in the oscilloscope binary file.")

        return data.T

    @staticmethod
    def _reshape_frames(
        oscillo_data: np.ndarray,
        nframes: int,
        order: Literal["F", "C"] = "F",
    ) -> np.ndarray:
        """
        Reshape a 1D array into a 2D array.

        Time series will end up on columns.

        Parameters
        ----------
        oscillo_data : np.ndarray
            1D array with time gaps.
        nframes : int
            Number of frames, the resulting array will have `nframes` columns.
        order : {"F", "C"}, optional
            Order, "F" for Fortran, "C" for C. Default is "F".

        Returns
        -------
        oscillo_data : np.ndarray
            Reshaped array.
        """
        nsamples_per_seq = int(oscillo_data.shape[0] // nframes)

        return oscillo_data.reshape((nsamples_per_seq, nframes), order=order)

    @staticmethod
    def _average_frame_range(
        frame: np.ndarray,
        tstart: float,
        tstop: float,
        dt: float,
        toffset: float = 0,
        tunit: str = "us",
    ) -> np.ndarray:
        """
        Average the signal in the `frame` 2D array in the given time window.

        The time window is defined by `tstart` and `tstop` expressed in the frame time
        base (`dt`).

        Parameters
        ----------
        frame : np.ndarray
            Array with time series on columns.
        tstart, tstop : float
            Defines the time window in which the average is computed.
        dt : float
            Time interval between two samples, in seconds.
        toffset : float, optional
            Offset in time, if the measurement time vector does not start at 0, default
            is 0.
        tunit : {"us", "ms", "s"} str, optional
            Units in which tstart and tstop are given, default is "us" (microseconds).

        Returns
        -------
        meas_avg : np.ndarray
            Measurement averaged in-frame, so that the resulting 1D vector is aligned on
            the `time_exp` vector.
        """
        match tunit:
            case "us":
                mult = 1e-6
            case "ms":
                mult = 1e-3
            case "s":
                mult = 1
            case _:
                logger.warning(
                    f"{tunit} is not recognized as a valid unit, assuming it is 'us'."
                )
                mult = 1e-6

        idx_start = int(np.ceil((tstart - toffset) * mult / dt))
        idx_stop = int(np.ceil((tstop - toffset) * mult / dt))

        return frame[idx_start:idx_stop, :].mean(axis=0)

    def _find_signal_in_ref(self) -> Self:
        """
        Find signal in reference time series.

        Wrap the `sp.find_signal()` function, fetching the parameters from the
        configuration.
        """
        if not self.is_digital:
            logger.warning("Can't find reference signal in analog mode.")
            return self
        else:
            # for type checking
            assert self.cfg.demodulation is not None

        # Get parameters
        nframes = self.cfg.demodulation.findsig_nframes
        if nframes > 0:
            rng = np.random.default_rng(self._seed)
            framesid = rng.integers(0, self.nframes, nframes)
            sig = self.get_data_raw(self._ref_name)[:, framesid]
        else:
            sig = self.get_data_raw(self._ref_name)
        std_factor = self.cfg.demodulation.findsig_nstd
        before = self.cfg.demodulation.findsig_extend

        # Detect signal
        logger.info("Detecting signal in reference trace...")
        start, stop = sp.find_signal(sig, std_factor, before=before, after=before)

        # Store
        self.metadata["ref_on"] = start
        self.metadata["ref_off"] = stop

        logger.info(f"Found indices {start, stop}.")

        return self

    def _update_time_subsampled(self, new_npoints: int):
        """
        Update time vector if subsampling was used.

        If decimation was used during demodulation, the corresponding time vector needs
        to be updated and placed in 'data_processed'.
        """
        self.set_data_processed(
            "time_meas",
            np.linspace(
                self.get_data_raw("time_meas")[0],
                self.get_data_raw("time_meas")[-1],
                new_npoints,
            ),
        )

    def load_metadata(self) -> Self:
        """
        Read metadata from the header of the text file with the frames onsets.

        Wrap the `_load_metadata()` method, fetching the parameters from the
        configuration.
        """
        # Get parameters
        filename = self.cfg.filenames["reference_time"]
        header_map = self.cfg.metadata.index_map
        conversion_map = self.cfg.metadata.conversion_map

        # Read metadata
        logger.info(f"Reading metadata from {os.path.basename(filename)}...")
        metadata = self._load_metadata(filename, header_map, conversion_map)

        # Remove unused metadata for WFM files
        if self.is_wfm:
            metadata.pop("dt_acq", None)  # will be read from the WFM file directly

        # Store (add freshly loaded metadata)
        self.metadata = self.metadata | metadata

        if self.is_digital:
            if "rf_frequency" in self.metadata:
                # Frequency used for demoduation will be read from configuration instead
                self.metadata["rf_frequency"] = 0
        else:
            logger.info(
                f"RF: {self.metadata['rf_frequency'] / 1e6:3.3f} MHz read from file."
            )

        # Verbose
        logger.info("Done.")

        return self

    def load_frame_onsets(self) -> Self:
        """
        Read frames onsets in the reference time text file.

        For LabVIEW binary files only. For WFM files, frame onsets are read from the
        file.

        Wrap the `_load_frame_onsets()` method, fetching the parameters from the
        configuration.
        """
        if self.is_wfm:
            # This will be read from the WFM file header.
            return self

        # Get parameters
        filename = self.cfg.filenames["reference_time"]
        nlines_header = self.cfg.files["reference_time"].header
        delimiter = self.cfg.files["reference_time"].delimiter

        # Read and store frames onsets
        if not Path(filename).is_file():
            logger.error(
                f"{Path(filename).name} does not exist, check your configuration file."
            )
            return self

        logger.info(f"Reading frame onsets from {os.path.basename(filename)}...")
        self.set_data_raw(
            "frame_onsets", self._load_frame_onsets(filename, nlines_header, delimiter)
        )
        self.nframes = self.data_raw["frame_onsets"].shape[0]

        # Verbose
        logger.info("Done.")

        return self

    def load_oscillo(self, **kwargs) -> Self:
        """
        Load oscilloscope data.

        Arguments are passed to the loader method, either `load_oscillo_wfm()` for WFM
        files, or `load_oscillo_bin()` for LabVIEW binary files.

        The frames are reshaped if needed and the time vector for both the measurement
        and the experiment are built and stored in `data_raw[results]`.

        Parameters
        ----------
        **kwargs : passed to `load_oscillo_wfm()`.
        """
        filename = Path(self.cfg.filenames["oscillo"])

        # Attempt to load metadata first
        try:
            self.load_metadata()
        except Exception:
            logger.warning("Metadata could not be loaded.")
            pass

        if filename.suffix.endswith("wfm"):
            self.is_wfm = True
            self.load_oscillo_wfm(**kwargs)
            self.metadata["toffset_meas"] = self.get_data_raw("time_meas")[0]
        elif filename.suffix.endswith("bin"):
            self.is_wfm = False
            self.load_oscillo_bin()
            self.reshape_frames()
        else:
            logger.warning(
                f"{os.path.basename(filename)} : extension not recognized, "
                "assuming LabVIEW binary file."
            )
            self.is_wfm = False
            self.load_oscillo_bin()

        # Load experiment time vector
        self.get_time_exp()

        return self

    def load_oscillo_bin(self) -> Self:
        """Load oscilloscope binary data from LabVIEW binary files."""
        # Get parameters
        filename = Path(self.cfg.filenames["oscillo"])
        nchannels = len(self.cfg.measurements)
        precision = self.cfg.files["oscillo"].precision
        endian = self.cfg.files["oscillo"].endian
        order = self.cfg.files["oscillo"].order

        # Check file exists
        if not filename.is_file():
            logger.error(
                f"{filename.name} does not exist, check your configuration file."
            )
            return self

        # Read data
        logger.info(f"Loading oscilloscope data from {filename.name}...")
        res = self._load_oscillo_bin(filename, nchannels, precision, endian, order)

        # Store
        for meas_name, meas_index in self.cfg.measurements.items():
            self.set_data_raw(meas_name, res[meas_index])
            # Add rolling average flag
            self.is_rollmean[meas_name] = False
            # Add dummy voltage scaling for compatibility with WFM files
            self.metadata["vscale"][meas_name] = 1
            self.metadata["voffset"][meas_name] = 0

        # Verbose
        logger.info(f"{', '.join(x for x in self.cfg.measurements.keys())} loaded.")

        return self

    def load_oscillo_wfm(self, scale: bool = False, microseconds: bool = True) -> Self:
        """
        Load oscilloscope data from Tektronix WFM files.

        Parameters
        ----------
        scale : bool, optional
            Whether to rescale loaded data to real units (e.g. volts) or keep it in
            int16. Default is False.
        microseconds : bool, optional
            Whether to convert the measurement time vector `time_meas`, to microseconds.
            Default is True.
        """
        # Get parameters
        filename_base = self.cfg.filenames["oscillo"]

        for meas_name, meas_index in self.cfg.measurements.items():
            filename = Path(
                str(filename_base).replace("_!CHANNELID", f"_ch{meas_index}")
            )

            if not filename.is_file():
                # try uppercase extension
                filename = filename.with_suffix(".WFM")
                if not filename.is_file():
                    logger.error(
                        f"{filename.name} doesn't exist, check your configuration file."
                    )
                    return self

            logger.info(
                f"Loading oscilloscope data from {os.path.basename(filename)}..."
            )
            # Load data
            tek = TekWFM(filename).load_frames().get_time_frame()

            # Store data and metadata
            if scale:
                self.set_data_raw(meas_name, tek.scale_data(tek.frames))
            else:
                self.set_data_raw(meas_name, tek.frames)

            self.metadata["vscale"][meas_name] = tek.vscale
            self.metadata["voffset"][meas_name] = tek.voffset

            logger.info(f"{meas_name} loaded.")

        # Store (meta)data
        self.set_data_raw("time_meas", tek.time_frame)
        if microseconds:
            self.is_us = True
            self.data_raw["time_meas"] *= 1e6
        else:
            self.is_us = False
        self.set_data_raw("frame_onsets", tek.frame_onsets)
        self.metadata["dt_acq"] = tek.tscale
        self.metadata["frame_duration"] = tek.npoints * tek.tscale
        self.nframes = tek.nframes
        self.npoints = tek.npoints

        return self

    def load_pickup(self) -> Self:
        """
        Load pickup coil binary data and create the corresponding time vector.

        Wrap the `_load_pickup()` method, fetching the parameters from the
        configuration.
        """
        # Get parameters
        filename = Path(self.cfg.filenames["pickup"])
        precision = self.cfg.files["pickup"].precision
        endian = self.cfg.files["pickup"].endian
        order = self.cfg.files["pickup"].order
        npickups = self.cfg.parameters.pickup_number
        pickup_index = self.cfg.parameters.pickup_index
        samplerate = self.cfg.parameters.pickup_samplerate

        # Read and store pickup coil voltage
        logger.info(f"Loading pickup data from from {filename.name}...")
        if Path(filename).is_file():
            self.set_data_raw(
                "pickup",
                self._load_pickup(
                    filename,
                    precision,
                    endian,
                    order=order,
                    nseries=npickups,
                    index=pickup_index,
                ),
            )
            # Create and store corresponding time vector
            nsamples = self.data_raw["pickup"].shape[0]
            self.set_data_raw(
                "pickup_time", np.linspace(0, (nsamples - 1) / samplerate, nsamples)
            )

            # Verbose
            logger.info("Done.")
        else:
            logger.info(f"{filename.name} not found, skipping.")
            # Create empty data that will be created when we'll know how long is the
            # experiment
            self.set_data_raw("pickup", np.array([]))
            self.set_data_raw("pickup_time", np.array([]))

        return self

    def compute_field(self, method: str = "trapz") -> Self:
        """
        Compute magnetic field from pickup coil data.

        Wraps the `sp.integrate_pickup()` function.

        Parameters
        ----------
        method : str, optional
            Integration method. Default is "trapz" (which is the only one supported).

        """
        # Checks
        if "pickup" not in self.data_raw:
            self.load_pickup()

        # Get parameters
        surface = self.cfg.parameters.pickup_surface

        # Integrate and store
        return self._compute_field(surface=surface, method=method)

    def reshape_frames(
        self, microseconds: bool = True, meas_names: None | str | Iterable[str] = None
    ) -> Self:
        """
        Reshape oscillo channels array to get a column per frame.

        Each measurement yields a 2D array with time series on columns, thus an array
        with sahep (npoints, nframes).

        Also build the corresponding measurement time vector.

        Parameters
        ----------
        microseconds : bool, optional
            Convert the time vector from seconds to microseconds. Default is True.
        meas_names : None or Sequence, optional
            If None (default), uses all available measurement names.

        """
        # Checks
        if self.is_wfm:
            return self

        if "frame_onsets" not in self.data_raw:
            self.load_frame_onsets()

        # Get list of arrays to reshape
        if not meas_names:
            measurements = self.measurements
        elif isinstance(meas_names, str):
            measurements = [meas_names]
        else:
            measurements = meas_names

        # Reshape frames in-place
        reshaped = False
        for measurement in measurements:
            logger.info(f"Reshaping {measurement}...\t")
            # check if it was loaded
            if measurement not in self.data_raw:
                logger.warning(f"{measurement} was not loaded, skipping.")
                continue

            if self._check_frames_2d(measurement, reshape=False):
                # check if it makes sense to reshape the data
                logger.warning(
                    f"{measurement} is not 1D and has probably been already reshaped."
                )
                reshaped = True
            else:
                # Reshape
                self.set_data_raw(
                    measurement,
                    self._reshape_frames(
                        self.get_data_raw(measurement),
                        self.nframes,  # number of frames
                        order=self.cfg.files["oscillo"].order,
                    ),
                )
                newshape = self.data_raw[measurement].shape
                logger.info(f"Reshaped to {newshape}.")
                reshaped = True

        if reshaped:
            if "dt_acq" not in self.metadata:
                if not self.is_digital:
                    self.load_metadata()
                else:
                    logger.error(
                        "Oscilloscope data was not loaded, could not get acquisition "
                        "sampling rate. Load the data then re-run reshape_frames()."
                    )
            # Number of time points in a frame
            nsamples_per_seq = self.data_raw[measurement].shape[0]
            # Duration of a frame
            frame_duration = nsamples_per_seq * self.metadata["dt_acq"]
            self.metadata["frame_duration"] = frame_duration  # store it as metadata
            # Build time vector
            measurement_time = np.linspace(
                0, frame_duration - self.metadata["dt_acq"], nsamples_per_seq
            )
            if microseconds:
                # convert to microseconds
                measurement_time *= 1e6
                self.is_us = True
            else:
                self.is_us = False
            # Store
            self.set_data_raw("time_meas", measurement_time)
            self.metadata["toffset_meas"] = self.get_data_raw("time_meas")[0]

        return self

    def get_time_exp(self) -> Self:
        """
        Build the experiment time vector from frame onsets.

        The time point associated to a frame is assumed to be at the middle of the
        duration of a frame. The resulting vector has a shape of (nframes,) and is
        stored in `data_processed[results]`.
        """
        logger.info("Building the experiment time vector...")
        # Checks
        if "frame_duration" not in self.metadata:
            # we don't know how long a frame is, attempt to get through reshape
            self.reshape_frames()
            # won't do anything if oscilloscope data not loaded so we need to recheck
            if "frame_duration" not in self.metadata:
                logger.error(
                    "Oscilloscope data not loaded, can't determine frame duration."
                )
                return self

        # Get parameters
        seq_onsets = self.get_data_raw("frame_onsets")
        seq_duration = self.metadata["frame_duration"]

        # Build the the time vector : attribute a point to the middle of its frame
        # time range
        self.set_data_processed("time_exp", seq_onsets + seq_duration / 2)

        # Add time interval in metadata
        self.metadata["dt_exp"] = np.mean(np.diff(self.get_data_processed("time_exp")))

        # Verbose
        logger.info("Done.")

        return self

    def align_field(self) -> Self:
        """
        Align magnetic field time serie on the experiment time vector.

        The pickup-coil sampling rate is much higher than the frames sampling rate. In
        order to plot the different resulting metrics against the magnetic field instead
        of the time, it needs to be aligned on the same time base using linear
        interpolation.

        Note that the magnetic field serie is overwritten with the aligned version.
        """
        # Checks
        if not self.get_data_processed("time_exp", checkonly=True):
            self.get_time_exp()
            # maybe it was still not computed, we need to recheck
            if not self.get_data_processed("time_exp", checkonly=True):
                logger.error("Time vector could not be built, exiting.")
                return self

        # We need to re-compute the field from scratch in case it was downsampled with
        # rolling average to make sure we're not upscaling it. This could be smarter (
        # by tracking the switches between rolling-average/no-rolling-average) but the
        # computation is cheap
        self.compute_field()

        # Collect data
        exptime = self.get_data_processed("time_exp")
        magtime = self.get_data_processed("magfield_time")
        magfield = self.get_data_processed("magfield")

        # Interpolate and store
        logger.info("Aligning magnetic field on experiment time base...")
        self.set_data_processed(
            "magfield", np.interp(exptime, magtime, magfield, left=0, right=0)
        )
        # overwrite the field time vector as well
        self.set_data_processed("magfield_time", self.get_data_processed("time_exp"))

        # Verbose
        logger.info("Done.")

        return self

    def average_frame_range(
        self, tstart: None | float = None, tstop: None | float = None, **kwargs
    ) -> Self:
        """
        Average signal in the given frame time range.

        `tstart` and `tstop` are expressed in unit of time (s). If they are not
        provided, they are read from the Config settings ('analysis_window').

        If the averaging is successful :
        1. The corresponding serie NXgroup is created as
            `data_processed[results_{serie_name}{serie_idx}]`,
        2. The analysis window is set as an attribute,
        3. The mean signal amplitude and phase are derived from the I and Q components
            and stored in this serie group.
        """
        # Reset averaging success flag
        self.is_averaged = False
        # Get parameters
        measurements = self.measurements  # list of arrays to average
        if not tstart:
            if len(self.analysis_window) == 2:
                tstart = self.analysis_window[0]
            else:
                tstart = np.inf
        if not tstop:
            if len(self.analysis_window) == 2:
                tstop = self.analysis_window[1]
            else:
                tstop = -np.inf
        if not self.is_us:
            # analysis_window should be in microseconds
            toffset = self.metadata["toffset_meas"] * 1e6
        else:
            toffset = self.metadata["toffset_meas"]

        # Check the range
        if tstop < tstart:
            logger.error(f"Invalid time range : {[tstart, tstop]}")
            return self

        # Prepare storage
        self.create_data_serie()

        # Perform average
        for measurement in measurements:
            # Check it was loaded
            if self.is_meas_processed and not self.get_data_processed(
                measurement, checkonly=True
            ):
                logger.warning(f"{measurement} was not computed, skipping...")
                continue
            elif not self.is_meas_processed and (measurement not in self.data_raw):
                logger.warning(f"{measurement} was not loaded, skipping...")
                continue

            logger.info(f"Averaging {measurement}")
            # Determine what data to use
            if self.is_rollmean[measurement]:
                # Moving mean filter was applied
                meas_name = f"s{measurement}"
                # Check it actually exists
                if not self.get_data_processed(meas_name, checkonly=True):
                    logger.warning(
                        f"{meas_name} not found in data_processed, skipping..."
                    )
                    continue
                logger.info("Using smoothed trace...")
                data = self.get_data_processed(meas_name)

            elif self.is_meas_processed:
                # Use 'raw' data found in 'data_processed' (e.g. demodulated)
                logger.info("Using demodulated trace...")
                meas_name = measurement

                # Check if it is 2D
                if not self._check_frames_2d(
                    meas_name, where="processed", reshape=False
                ):
                    # check if the data was reshaped
                    logger.error(f"{meas_name} is still 1D, skipping...")
                    continue

                data = self.get_data_processed(meas_name)

            else:
                # Use raw raw data
                logger.info("using raw trace...")
                meas_name = measurement

                # Check if it is 2D
                if not self._check_frames_2d(meas_name, reshape=True):
                    # check if it the data was reshaped
                    logger.error(f"{meas_name} is still 1D, skipping...")
                    continue

                data = self.get_data_raw(meas_name)

            # Determine time interval
            if self.is_decimated:
                # Decimation was applied
                dt = np.mean(np.diff(self.get_data_processed("time_meas")))
                if self.is_us:
                    # Convert to seconds
                    dt *= 1e-6
            else:
                # Original time interval
                dt = self.metadata["dt_acq"]
            # Average & store (keep the original measurement name)
            self.set_data_serie(
                measurement + "_avg",
                self._average_frame_range(
                    data, tstart, tstop, dt, toffset=toffset, **kwargs
                ),
            )
            self.is_averaged = True  # averaging worked
            logger.info("Done.")

        # Compute phase from I and Q
        if self.is_averaged:
            # If averaging worked, we can compute amplitude and phase on the average
            logger.info("Computing amplitude...")
            self.compute_amplitude_avg()
            logger.info("Done.")
            logger.info("Computing phase...")
            self.compute_phase_avg()
            logger.info("Done.")

            # Store analysis window
            self.metadata["last_analysis_window"] = [tstart, tstop]
            self.set_attr_serie("analysis_window", [tstart, tstop])
            self.set_attr_serie("analysis_window_unit", "µs")

            # Get time vector in case it was not computed before
            if not self.get_data_processed("time_exp", checkonly=True):
                self.get_time_exp()
            # Get magnetic field
            if not self.get_data_processed("magfield", checkonly=True):
                self.compute_field().align_field()
            # Prepare placeholders that will be replaced by actual NXlink when the
            # object has a NXroot entry
            phtime = f"!link to:processed/analysis/{self._results_name}/time_exp"
            phmagfield = f"!link to:processed/analysis/{self._results_name}/magfield"
            # Store the link in the 'serie' group
            self.set_data_serie("time_exp", phtime)
            self.set_data_serie("magfield", phmagfield)

        return self

    def average_frame(self, **kwargs) -> Self:
        """Alias for the `average_frame_range()` method."""
        return self.average_frame_range(**kwargs)

    def _compute_amplitude_avg(self):
        """
        Compute amplitude from averaged I and Q.

        They are read from `data_processed[results][results_{serie_name}{idx_name}]`,
        and the results is stored as "amplitude_avg".
        """
        # Get names
        iname = self._i_name + "_avg"
        qname = self._q_name + "_avg"

        # Get data
        if not self.get_data_serie(iname, checkonly=True) or not self.get_data_serie(
            qname, checkonly=True
        ):
            logger.warning(
                f"'{iname}' or '{qname} not found, was the signal demodulated before "
                "averaging ?"
            )
            self.is_averaged = False
            return

        i = self.get_data_serie(iname)
        q = self.get_data_serie(qname)

        # Compute averaged amplitude
        self.set_data_serie("amplitude_avg", sp.compute_amp_iq(i, q))

        # Mark for success
        self.is_averaged = True

    def compute_amplitude(self) -> np.ndarray:
        """
        Compute amplitude from raw or demodulated data (not averaged).

        Either return directly amplitude from 'data_raw' in analog mode, or derive it
        from I and Q in digital mode.
        The returned array has shape (nframes, npoints).
        """
        if self.is_digital:
            amp = sp.compute_amp_iq(
                self.get_data_processed(self._i_name),
                self.get_data_processed(self._q_name),
            )
        else:
            amp = self.get_data_raw("amplitude")

        return amp

    def compute_phase(self) -> np.ndarray:
        """
        Compute phase from raw or demodulated data (not averaged).

        Phase is the arctan of the I and Q components, corrected for pi-jumps.
        The returned array has shape (nframes, npoints).
        """
        if self.is_digital:
            phase = sp.compute_phase_iq(
                self.get_data_processed(self._i_name),
                self.get_data_processed(self._q_name),
            )
        else:
            phase = sp.compute_phase_iq(
                self.get_data_raw(self._i_name), self.get_data_raw(self._q_name)
            )

        return phase

    def compute_amplitude_avg(self) -> None:
        """
        Compute amplitude of averaged time series.

        In analog mode, amplitude is directly an oscilloscope channel, in digital mode,
        it needs to be derived from I and Q.
        """
        if self.is_digital:
            self._compute_amplitude_avg()
        else:
            self.is_averaged = True
        return

    def compute_phase_avg(self):
        """Compute phase from I and Q and correct for pi jumps."""
        # Get names
        iname = self._i_name + "_avg"
        qname = self._q_name + "_avg"

        # Get data
        i = self.get_data_serie(iname)
        q = self.get_data_serie(qname)

        # Compute phase
        res = sp.compute_phase_iq(
            i,
            q,
            unwrap=True,
            period=self.cfg.settings.max_phase_jump * 2 * np.pi,
            axis=0,
        )

        # Store
        self.set_data_serie("phase_avg", res)

        # Mark for success
        self.is_averaged = True

    def compute_attenuation(self) -> Self:
        """
        Compute attenuation from amplitude average for the current echo.

        It is computed with the `sp.compute_attenuation()` function from the
        averaged amplitude and stored in the current serie group.
        """
        # Get parameters
        if "dt_exp" not in self.metadata:
            self.get_time_exp()
        if not self.is_averaged:
            logger.warning("Averaging amplitude or phase (or both) failed.")
            return self

        # Get data
        amp_avg = self.get_data_serie("amplitude_avg")

        # Get baseline
        wbline = self.cfg.settings.range_baseline
        dt = self.metadata["dt_exp"]
        idx_start = int(np.ceil(wbline[0] / dt))
        idx_stop = int(np.ceil(wbline[1] / dt))
        amp0 = amp_avg[idx_start:idx_stop].mean()

        # Compute
        logger.info(f"Computing attenuation for echo index {self.idx_serie}...")
        self.set_data_serie(
            "attenuation",
            sp.compute_attenuation(
                amp_avg,
                amp0,
                self.idx_serie,
                self.cfg.parameters.sample_length,
                mode=self.cfg.parameters.detection_mode,
                corr=self.cfg.parameters.logamp_slope,
            ),
        )
        logger.info("Done.")

        return self

    def compute_phase_shift(self):
        """
        Compute relative phase shift given the phase average for the current echo.

        It is computed with the `sp.compute_phase_shift()` function from the
        averaged phase and stored in the current serie group.
        """
        # Get parameters
        if "dt_exp" not in self.metadata:
            self.get_time_exp()
        if not self.is_averaged:
            logger.warning("Averaging amplitude or phase (or both) failed.")
            return self

        # Get data
        phi_avg = self.get_data_serie("phase_avg")

        # Get baseline
        wbline = self.cfg.settings.range_baseline
        dt = self.metadata["dt_exp"]
        idx_start = int(np.ceil(wbline[0] / dt))
        idx_stop = int(np.ceil(wbline[1] / dt))
        phi0 = phi_avg[idx_start:idx_stop].mean()

        # Compute
        logger.info(f"Computing phase shift for echo index {self.idx_serie}...")
        self.set_data_serie(
            "phaseshift",
            sp.compute_phase_shift(
                phi_avg,
                phi0,
                self.idx_serie,
                self.cfg.parameters.sample_speed,
                self.metadata["rf_frequency"],
                self.cfg.parameters.sample_length,
                mode=self.cfg.parameters.detection_mode,
            ),
        )
        logger.info("Done.")

        return self

    def rolling_average(self) -> Self:
        """
        Perform a rolling average on raw data measurements.

        Store the smoothed arrays in `data_processed[results]` with a leading "s".

        The data can optionnally be sub-sampled, given the parameters defined in the
        settings section of the configuration file, in that case the corresponding time
        vector is subsampled as well and store in `data_processed[results]`.

        Uses the `sp.rolling_average()` function.
        """
        # Collect parameters
        wlen = self.cfg.settings.rolling_mean_wlen
        subsample = self.cfg.settings.rolling_mean_subsample

        # Check if there is something to do
        if wlen < 2:
            # wlen = 1 or 0 means no rolling average
            logger.warning(f"Time window set to {wlen}, no rolling average.")

            # Re-generate time vector in case subsampling was applied before
            self.get_time_exp()
            self.align_field()

            # Set flags
            self.is_rollmean.update({m: False for m in self.measurements})
            return self

        for measurement in self.measurements:
            # Get data
            if self.is_meas_processed:
                if not self.get_data_processed(measurement, checkonly=True):
                    logger.warning(f"{measurement} was not computed, skipping.")
                    continue

                data = self.get_data_processed(measurement)
                where = "processed"
                reshape = False
            else:
                if measurement not in self.data_raw:
                    logger.warning(f"{measurement} was not loaded, skipping.")
                    continue
                data = self.get_data_raw(measurement)
                where = "raw"
                reshape = False

            # Check data is 2D
            if self._check_frames_2d(measurement, where=where, reshape=reshape):
                # Yup, apply moving mean
                logger.info(f"Applying rolling average to {measurement}...")
                self.set_data_processed(
                    f"s{measurement}",
                    sp.rolling_average(data, wlen, subsample=subsample, axis=1),
                )
                self.is_rollmean[measurement] = True
                logger.info("Done.")

                # Re-generate time vector in case of subsampling
                self.get_time_exp()

                # If subsampling is on, we need to update the experiment time vector
                if subsample:
                    logger.info(
                        "Subsampling is on, updating time and magnetic field..."
                    )
                    self.set_data_processed(
                        "time_exp",
                        sp.subsample_array(
                            self.get_data_processed("time_exp"), wlen - 1
                        ),
                    )

                # Re-align magnetic field
                self.align_field()

            else:
                # Nope and reshape did not work somehow
                logger.error(
                    f"{measurement} is not 2D and couldn't be reshaped, exiting..."
                )
                continue

        return self

    def find_f0(self) -> Self:
        """
        Find center frequency in reference signal.

        The resulting frequency will be used to build the continuous reference wave used
        for demodulating the signal.

        If it is not set in the "demodulation" section of the configuration (set to 0),
        it will be detected automatically using the `sp.find_f0()` function that relies
        on RFFT.

        Only the part of the reference signal where there is an actual signal (as found
        by `_find_signal_in_ref()`) will be used to find f0. Optionally, detrending can
        be applied for better results of the FFT. This is controlled with the "detrend"
        parameter in the configuration.
        """
        # Check there is something to do
        if not self.is_digital:
            logger.warning("Can't find center frequency in analog mode.")
            return self
        else:
            # for type checking
            assert self.cfg.demodulation is not None

        if self.cfg.demodulation.f0 > 0:
            self.metadata["rf_frequency"] = self.cfg.demodulation.f0
            logger.info(
                "Read f0 set in configuration : "
                f"{self.metadata['rf_frequency'] / 1e6:3.3f}MHz."
            )
            return self

        # Get parameters
        if self._ref_name not in self.data_raw:
            logger.error("Reference signal was not loaded.")
            return self

        if "ref_on" not in self.metadata:
            # find reference signal onset and offset
            self._find_signal_in_ref()

        tstart = self.metadata["ref_on"]
        tstop = self.metadata["ref_off"]
        nframes = self.cfg.demodulation.fft_nframes
        if nframes > 0:
            # get random frames
            rng = np.random.default_rng(self._seed)
            framesid = rng.integers(0, self.nframes, nframes)
            sig = self.get_data_raw(self._ref_name)[tstart:tstop, framesid]
        else:
            # take all frames
            sig = self.get_data_raw(self._ref_name)[tstart:tstop, :]

        # Optional detrending
        if self.cfg.demodulation.detrend:
            logger.info("Detrending signal...")
            sig = signal.detrend(sig, axis=0)

        logger.info("Finding center frequency in reference signal...")
        self.metadata["rf_frequency"] = sp.find_f0(
            sig, 1 / self.metadata["dt_acq"]
        ).mean()

        logger.info(f"Found {self.metadata['rf_frequency'] / 1e6:3.3f}MHz.")

        return self

    def demodulate(self, **kwargs) -> Self:
        """
        Digital demodulation : frequency-shifting followed by a low-pass filter.

        A reference signal and a measurement signal are required, as well as a center
        frequency (f0, see the `find_f0()` method).

        The reference signal is fitted to extract the phase (when there is signal, see
        the `_find_signal_in_ref()` method) and build a continuous, mono-frequency
        signal. The measurement signal is frequency-shifted (multiplied by cos(phi_ref)
        and sin(phi_ref)), then a low-pass filter is applied. Optionally, the frequency-
        shifted signal can be decimated before applying the filter. The filter
        properties are set in the configuration.

        The demodulation is done in chunks to not saturate memory (chunks size is set in
        the configuration).

        The I and Q components are stored in the `data_processed[results]`. If
        decimation is used, the corresponding time vector is updated accordingly and
        stored there as well.

        Uses the `sp.demodulate_chunks()` function.
        """
        if not self.is_digital:
            logger.warning("Can't perform demodulation in analog mode.")
            return self
        else:
            # for type checking
            assert self.cfg.demodulation is not None

        # Check data is loaded
        if "ref_on" not in self.metadata:
            self._find_signal_in_ref()
        if ("rf_frequency" not in self.metadata) or self.metadata["rf_frequency"] == 0:
            self.find_f0()
        if "time_meas" not in self.data_raw:
            logger.error("Data was not loaded, exiting.")
            return self
        else:
            if self.is_us:
                tmeas = self.get_data_raw("time_meas") * 1e-6  # convert back to seconds
            else:
                tmeas = self.get_data_raw("time_meas")

        # Get parameters for reference fitting range
        istart = self.metadata["ref_on"]
        istop = self.metadata["ref_off"]

        logger.info("Demodulation...")
        in_phase, out_phase = sp.demodulate_chunks(
            tmeas[istart:istop],
            self.get_data_raw(self._ref_name)[istart:istop, :],
            tmeas,
            self.get_data_raw(self._sig_name),
            f0=self.metadata["rf_frequency"],
            filter_order=self.cfg.demodulation.filter_order,
            filter_fc=self.cfg.demodulation.filter_fc,
            decimate_factor=self.cfg.demodulation.decimate_factor,
            chunksize=self.cfg.demodulation.chunksize,
            **kwargs,
        )
        logger.info("Done.")

        # Store
        self.set_data_processed(self._i_name, in_phase)  # I
        self.set_data_processed(self._q_name, out_phase)  # Q

        # In case of decimation, the time vector needs to be updated
        if self.cfg.demodulation.decimate_factor > 1:
            # Get new number of points and create new time vector
            self._update_time_subsampled(in_phase.shape[0])
            # Update flag
            self.is_decimated = True
        else:
            # Remove decimated time vector
            self.remove_data_processed("time_meas")
            self.is_decimated = False

        # Removed rolling-averaged data and update flags
        self.is_rollmean.update({m: False for m in self.measurements})
        for meas in self.measurements:
            self.remove_data_processed(f"s{meas}")
        # Update time vector that was maybe subsampled because of rolling average
        self.get_time_exp()
        self.align_field()

        return self

    def get_csv_filename(self) -> str:
        """
        Generate output CSV file name for the current echo.

        The file is placed in the data directory set in the configuration. Its name
        contains the analysis time window and the echo number.
        """
        fout = os.path.join(self.cfg.data_directory, self.cfg.expid + "-results")
        echo_index = self.idx_serie
        tstart = self.metadata["last_analysis_window"][0]
        tstop = self.metadata["last_analysis_window"][1]
        return f"{fout}_{tstart:.3f}-{tstop:.3f}_echo{echo_index}.csv"

    def to_csv(
        self, fname: None | str | Path = None, sep: str = "\t", to_cm: bool = False
    ):
        r"""
        Export attenuation and phase shift data as a CSV file.

        Columns names are written on the first line. The current echo index is used to
        select which data to save.

        Parameters
        ----------
        fname : str, Path or None, optional
            Full path to the output file. If None, the name is generated automatically.
            This is the default behavior.
        sep : str, optional
            Separator in the file, usually "," (csv) or "\t" (tsv, default).
        to_cm : bool, optional
            Convert attenuation from dB/m to dB/cm. Default is False.
        """
        # Create output file name
        if not fname:
            fname = self.get_csv_filename()

        logger.info(f"Saving at {fname}...")

        # Collect data to be saved
        attenuation = self.get_data_serie("attenuation")[..., np.newaxis]
        data = np.concatenate(
            (
                self.get_data_processed("time_exp")[..., np.newaxis],
                self.get_data_processed("magfield")[..., np.newaxis],
                self.get_data_serie("phase_avg")[..., np.newaxis],
                self.get_data_serie("amplitude_avg")[..., np.newaxis],
                attenuation / 100 if to_cm else attenuation,
                self.get_data_serie("phaseshift")[..., np.newaxis],
            ),
            axis=1,
        )
        # Configure output file
        header = sep.join(
            ("time", "field", "phase", "amplitude", "attenuation", "dphase")
        )

        # Save CSV file
        np.savetxt(fname, data, delimiter=sep, header=header, comments="")

        logger.info("Done.")

    def _check_frames_2d(
        self, meas_name: str, where: str = "raw", reshape: bool = True
    ) -> bool:
        """
        Check if the array corresponding to `meas_name` is 1 or 2D.

        The data is looked up in 'data_raw' if `where` is "raw", and in 'data_processed'
        if `where` is "processed".
        If the former and `reshape` is True, call the `reshape_frame()` method on that
        measurement. This option is valid only for `where` = "raw".

        Parameters
        ----------
        meas_name : str
            Name of some measurement in `data_raw`.
        where : {"raw", "processed"}, optional
            Whether to look up the data in 'data_raw' (default) or in 'data_processed'.
        reshape : bool, optional
            Whether to attempt to reshape frames through the `reshape_frame()` method.
            Default is True.

        Returns
        -------
        res : bool
            Returns true if the array is 2D, or if `reshape_frame()` was called.
        """
        match where:
            case "raw":
                data = self.get_data_raw(meas_name)
            case "processed":
                data = self.get_data_processed(meas_name)
                reshape = False  # disable reshape that works only on raw data
            case _:
                logger.warning(
                    f"{where} is not recognized as a valid data location, assuming it "
                    "is 'raw'."
                )
                where = "raw"
                data = self.get_data_raw(meas_name)
        if data.ndim < 2:
            # Not 2D
            if reshape:
                # Reshape
                self.reshape_frames(meas_names=[meas_name])

                # Check if it worked
                data = self.get_data_raw(meas_name)
                if data.ndim < 2:
                    # Still not 2D
                    return False
                else:
                    # Yup
                    return True
            else:
                # Don't try to reshape, just return Nope
                return False
        else:
            # Yup
            return True

    def _check_measurement_time_us(self) -> bool:
        """
        Check if the measurement time is in microseconds.

        Read the `time_meas` dataset attribute "units", if it does not exist, look at
        the order of magnitude of values in the vector and compare to the
        `EXP_TIMESCALE` global variable. If the maximum is 1000 times higher, it is
        assumed the vector is in microseconds.

        If the measurement time vector is not found, issue a warning and return True as
        it should be the default.
        """
        if "time_meas" in self.data_raw:
            if "units" in self.data_raw["time_meas"].attrs:
                # Check attribute
                if self.data_raw["time_meas"].attrs["units"] in ("us", "µs"):
                    return True
                else:
                    return False
            else:
                if self.data_raw["time_meas"].max() > 1e3 * FRAME_TIMESCALE:
                    # Check numbers scale
                    return True
        logger.warning("Could not determine 'time_meas' units, guessing µs (default).")
        return True

    def _check_averaged(self) -> bool:
        """
        Check if data was averaged.

        This is done by checking if any dataset name in `data_processed[results]` ends
        with "_avg" as written by the `average_frame_range()` method.
        """
        pattern = "_avg"
        for item in self.data_processed.values():
            if isinstance(item, nx.NXdata):
                for key in item:
                    if key.endswith(pattern):
                        return True

        return False

    def _check_digital(self) -> bool:
        """
        Check if the input should be treated as analog or digital.

        This is done by checking if the configuration has a "demodulation" section. Note
        that even if this section is empty, True will be returned.
        """
        # Check if the Config object has a non-None 'demodulation' attribute
        res = getattr(self.cfg, "demodulation", None)
        if res is None:
            return False
        else:
            return True

    def _check_rollmean(self) -> dict[str, bool]:
        """
        Check if rolling average was applied for each measurement.

        This is done by checking if measurements datasets are found in
        `data_processed[results]` with a name with a leading "s", as written by the
        `rolling_average()` method.
        """
        is_rollmean = dict()
        for meas in self.measurements:
            if self.get_data_processed(f"s{meas}", checkonly=True):
                is_rollmean[meas] = True
            else:
                is_rollmean[meas] = False
        return is_rollmean

    def _check_time_subsampled(self):
        """
        Check if measurement time vector was subsampled.

        Happens when decimation is used during demodulation. This is done by checking
        if there is a "time_meas" dataset in `data_processed[results]` as this indicates
        some processing was applied to this vector.
        """
        return self.get_data_processed("time_meas", checkonly=True)

    def load(self, filename: str | Path | None) -> Self:
        """
        Load a previously created NeXus file.

        Use `BaseProcessor.save()` method, with additionnal steps : guess the internal
        flags and add convenience attributes. The returned `EchoProcessor` object can be
        used to resume analysis where it was left off.

        Parameters
        ----------
        filename : str
            Full path to the file to load.
        """
        super().load(filename)

        # Set measurements names
        self.measurements = [*self.cfg.measurements.keys()]

        # Update flags
        self._guess_flags()

        # Update convenience attributes
        if not self.is_digital:
            self._i_name = I_NAME_ANALOG
            self._q_name = Q_NAME_ANALOG
        if "frame_onsets" in self.data_raw:
            self.nframes = self.data_raw["frame_onsets"].shape[0]
        else:
            logger.warning("Could not read number of frames, features will be limited.")
            print("You can set it manually with 'd.nframes = 16000'")
        if "time_meas" in self.data_raw:
            self.npoints = self.data_raw["time_meas"].shape[0]
        else:
            logger.warning(
                "Could not read number of measurement time points, features will be"
                "limited."
            )
            print("You can set it manually with 'd.npoints = 5000'")

        return self

    def batch_process(
        self,
        expids: Sequence,
        rolling_average: bool = False,
        save_csv: bool = False,
        save_csv_kwargs: dict = {},
        find_f0: bool = False,
        batch_progress_emitter: Any = None,
        demodulation_progress_emitter: Any = None,
    ) -> Self:
        """
        Batch-process a list of experiment IDs, keeping current parameters.

        Only supports datasets present in the current `data_directory`. Optionally,
        export the results as a CSV file for each dataset.

        Parameters
        ----------
        expids : Sequence
            List of experiment ID to process.
        rolling_average : bool, optional
            Whether to apply rolling average in the process. Default is False.
        save_csv : bool, optional
            Whether to export results as a CSV file. Default is False.
        save_csv_kwargs : dict, optional
            Used only when `save_csv` is True. Specify arguments for the `to_csv()`
            method. Default is an empty dict (default arguments will be used).
        find_f0 : bool, optional
            Force finding f0 in digital mode, whatever the value of `f0` in the
            demodulation section of the current configuration. Default is False.
        batch_progress_emitter : Any, optional
            An object with an `emit()` method, such as a pyqtpyqtSignal. The loop index is
            emitted at each iteration of the main loop. Default is None.
        demodulation_progress_emitter : Any, optional
            An object with an `emit()` method, such as a pyqtpyqtSignal. The loop index is
            emitted at each iteration of the demodulation loop. Default is None.
        """
        for idx, expid in enumerate(expids):
            # Set the experiment ID (will reinitialize data but not configuration)
            self.expid = expid

            # Load data
            self.load_oscillo(scale=True)
            # Load and align magnetic field
            self.align_field()

            # Demodulate
            if self.is_digital:
                if find_f0 and self.cfg.demodulation is not None:
                    self.cfg.demodulation.f0 = 0
                self.demodulate(progress_emitter=demodulation_progress_emitter)

            # Rolling average
            if rolling_average:
                self.rolling_average()

            # Average frames and compute
            self.average_frame_range().compute_attenuation().compute_phase_shift()

            # Export as CSV
            if save_csv:
                self.to_csv(**save_csv_kwargs)

            # Emit progress
            if batch_progress_emitter is not None:
                batch_progress_emitter.emit(idx)

        return self
