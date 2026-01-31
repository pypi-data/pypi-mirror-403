"""The processor base class."""

import gc
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, Protocol, Self, runtime_checkable

import matplotlib.pyplot as plt
import nexusformat.nexus as nx
import numpy as np

from . import signal_processing as sp
from ._data import DataProcessed, DataRaw

# Global constants
PROGRAM_NAME = "pymagnetos"  # program name, saved in the NeXus file
RESULTS_NAME = "results"  # name of the main NeXus group
SERIE_NAME = "serie"  # name of the data series group in the NeXus file
NEXUS_EXTENSION = ("nx5", "nxs", "h5", "hdf5")  # NeXus file extension

logger = logging.getLogger(__name__)


@runtime_checkable
class Config(Protocol):
    def loads(): ...


class BaseProcessor:
    """
    Load, analyze and store data acquired during pulsed magnetic field experiment.

    This is a base class meant to be subclassed to create specialized processor objects.

    It provides methods shared between experiments :
    - Load a configuration file (via the Config object),
    - Load binary and text data,
    - Store the data in-memory as NeXus objects (via the Data objects),
    - Compute a magnetic field over time,
    - Save the results as a NeXus file.

    It offers a convenient way to get and set data in a NeXus hierarchy (raw and
    processed data, sorted in different series) and can dump it in a NeXus-compliant
    HDF5 file along with all the metadata required to recreate a Processor object from
    such a file. The file can be optionnaly consolidated by specifying additional NeXus
    fields in the configuration file.

    The `_config_cls` attribute should be a Config class (the type, not an instance) and
    be set by subclasses.
    """

    _config_cls: type[Config]

    def __init__(self, file_path: Path | str | None = None, **kwargs) -> None:
        """
        Load, analyze and store data acquired during pulsed magnetic field experiment.

        Parameters
        ----------
        file_path : Path, str or None, optional
            Full path to the configuration file or a previously saved NeXus file. Can be
            None (default) to instantiate an empty object.
        **kwargs : passed to the `load_file()` method.
        """
        # Prepare internal variables in case it was not set before
        if not hasattr(self, "_results_name"):
            self._results_name = RESULTS_NAME
        if not hasattr(self, "_serie_name"):
            self._serie_name = SERIE_NAME
        if not hasattr(self, "_program_name"):
            self._program_name = PROGRAM_NAME
        if not hasattr(self, "_config_cls"):
            raise AttributeError(
                "No Config class defined, subclasses must set the '_config_cls' "
                "attribute."
            )

        # Load configuration or NeXus and trigger further initializations
        self.load_file(file_path, **kwargs)

    @property
    def idx_serie(self) -> int:
        """
        Current analysis serie index.

        It is a property so that it can be stored and updated in the Config object as
        well.
        """
        return -1

    @idx_serie.setter
    def idx_serie(self, value: int):
        raise NotImplementedError("Subclasses must implement this property setter")

    @property
    def analysis_window(self) -> Sequence[float]:
        """
        Current analysis window.

        It is a property so that it can be stored and updated in the Config object as
        well.
        """
        return [0.0]

    @analysis_window.setter
    def analysis_window(self, value: Sequence[float]):
        raise NotImplementedError("Subclasses must implement this property setter")

    def __repr__(self) -> str:
        return f"{type(self)}\nDataset : {self.cfg.expid}"

    def __str__(self) -> str:
        return f"Dataset : {self.cfg.expid}"

    def load_file(self, filepath: str | Path | None, **kwargs) -> None:
        """
        Load a configuration or NeXus file with the Config class.

        If loading a NeXus file, its extension should be "nx5", "nxs", "h5" or "hdf5" to
        be detected as such.

        Parameters
        ----------
        filepath : str, Path or None
            Full path to the configuration file or NeXus file.
        **kwargs : passed to the Config class.
        """
        if filepath is not None and str(filepath).endswith(NEXUS_EXTENSION):
            # Load the NeXus file instead
            self.is_config_file = False
            self.cfg = self._config_cls(**kwargs)  # initialize Config with defaults
            self._init()  # initialize default Processor
            self.load(filepath)  # load NeXus file
        else:
            # Load the configuration file
            self.is_config_file = True
            self.is_nexus_file = False
            self.cfg = self._config_cls(user_file=filepath, **kwargs)
            self.cfg.resolve_nexus(self._serie_name)
            self._init()  # initialize with Config

    def _init(self) -> None:
        """
        Initialize the object after loading a configuration file.

        This method should be executed either *after* loading the configuration file or
        *before* loading a NeXus file.

        The Data objects from the `data` modules and the NeXus structure are initialized
        here.
        """
        # Get parameters and metadata
        self.measurements = [*self.cfg.measurements.keys()]
        attr_raw = self.cfg.nexus.groups["data"]
        attr_processed = self.cfg.nexus.groups["analysis"]
        name_entry = self.cfg.nexus.groups["root"]["name"]

        # Prepare attributes storing the (meta)data.
        self.metadata = dict()
        self.data_raw = DataRaw(attr=attr_raw)
        self.data_processed = DataProcessed(
            program=self._program_name,
            attr=attr_processed,
            results_name=self._results_name,
            serie_name=self._serie_name,
        )
        # NeXus Entry
        self.nxentry = nx.NXentry(name=name_entry)
        self.nxentry.attrs["default"] = "processed"
        self._fill_nexus_entry()
        # NeXus Root
        self.nxroot = nx.NXroot(self.nxentry)
        self.nxroot.attrs["default"] = name_entry

    def _reinit(self) -> None:
        """Reinitialize the Processor, cleaning up the data."""
        self._init()
        gc.collect()

    @staticmethod
    def load_bin(
        filepath: str | Path,
        precision: int = 8,
        endian: Literal["<", ">"] = "<",
        **kwargs,
    ) -> np.ndarray:
        """
        Read a binary file with the given precision and endian.

        Simple wrapper around `numpy.fromfile()`.

        Parameters
        ----------
        filepath : str or Path
            Full path to the file to read.
        precision : int, optional
            Floating-point precision, by default 8.
        endian : {"<", ">"}, optional
            "<" for little endian, ">" for big endian, by default "<".
        **kwargs : passed to `numpy.fromfile()`.

        Returns
        -------
        data : np.ndarray
            Raw data from binary file.

        """
        with open(filepath, "rb") as fid:
            data = np.fromfile(fid, dtype=f"{endian}f{precision}", **kwargs)

        return data

    def _load_pickup(
        self,
        filename: Path | str,
        precision: int,
        endian: Literal["<", ">"] = "<",
        order: Literal["F", "C"] = "F",
        nseries: int = 1,
        index: int = 0,
    ) -> np.ndarray:
        """
        Load the pickup data from a binary file.

        The array is reshaped given the number series (by default, 1).

        Parameters
        ----------
        filename : Path | str
            Full path to the pickup binary file.
        precision : int
            Byte precision.
        endian : {"<", ">"}, optional
            "<" for little endian, ">" for big endian. Default is "<".
        order : {"F", "C"}, optional
            Array order, "F" for Fortran, "C" for C. Default is "F".
        nseries : int, optional
            Number of pickups time series in the binary file. Default is 1.
        index : int, optional
            Index of the time serie to read, 0-based. Default is 0 (first).

        Returns
        -------
        pickup : np.ndarray
            Pickup voltage time serie.
        """
        # Read data
        data = self.load_bin(filename, precision, endian)

        # Reshape and get required time serie
        data = data.reshape((-1, nseries), order=order)[:, index].astype(float).copy()

        return data

    def load_pickup(self):
        """
        Load the pickup binary file, gathering metadata (if any) and the file.

        Pickup binary file might be different accross experiments, so subclasses must
        implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def compute_field(self, method: str = "trapz") -> Self:
        """
        Compute magnetic field by integrating the pickup signal.

        The details are in the `_compute_field()` method.

        Parameters
        ----------
        method : str, optional
            Method to perform integration, passed to `sp.integrate_pickup()`. Default is
            "trapz" (which is only method currently supported).
        """
        # Checks
        if "pickup" not in self.data_raw:
            self.load_pickup()

        # Get parameters
        surface = self.cfg.parameters.pickup_surface

        # Compute
        self._compute_field(surface=surface, method=method)

        return self

    def _compute_field(
        self,
        surface: float = 1.0,
        method: str = "trapz",
    ) -> Self:
        """
        Compute magnetic field from pickup coil data.

        Wraps the `sp.integrate_pickup()` function. Resulting field is stored as
        `magfield` in `data_processed`, with the corresponding time vector as
        `magfield_time`.

        Requires `pickup` and `pickup_time` in `data_raw`. If pickup signal is empty, a
        synthetic one is generated.

        Parameters
        ----------
        surface : float
            Pickup coil surface in m².
        method : str, optional
            Integration method. Default is "trapz" (which is the only one supported).
        """
        if ("pickup_time" not in self.data_raw) or ("pickup" not in self.data_raw):
            logger.error("Pickup signal was not loaded, can't compute magnetic field.")
            return self

        pu_time = self.get_data_raw("pickup_time")
        pu_signal = self.get_data_raw("pickup")

        # Check if we need to simulate a signal
        if pu_time.shape == (0,) or pu_signal.shape == (0,):
            # We need to simulate a pickup signal
            if self.get_data_processed("time_exp", checkonly=True):
                logger.info("There is no pickup signal, simulating one.")
                self.create_fake_pickup()
                # Reload
                pu_time = self.get_data_raw("pickup_time")
                pu_signal = self.get_data_raw("pickup")
            else:
                # Required data missing
                logger.warning(
                    "There is no pickup signal, main data need to be loaded first to "
                    "simulate a field."
                )
                return self

        # Integrate and store
        logger.info("Computing magnetic field...")
        self.set_data_processed(
            "magfield", sp.integrate_pickup(pu_time, pu_signal, surface, method=method)
        )
        self.set_data_processed("magfield_time", self.get_data_raw("pickup_time"))

        # Verbose
        maxfield = self.get_data_processed("magfield").max()
        logger.info(f"Done, max. field = {maxfield:2.2f}T.")

        return self

    def create_fake_pickup(self) -> Self:
        """
        Create a fake pickup signal and store it in `data_raw`.

        Requires "time_exp" in `data_processed`.
        """
        self.set_data_raw(
            "pickup",
            self._make_fake_pickup(self.get_data_processed("time_exp").shape[0]),
        )
        self.set_data_raw("pickup_time", self.get_data_processed("time_exp"))

        return self

    @staticmethod
    def _make_fake_pickup(npoints: int, start_at: float = 0.0) -> np.ndarray:
        """
        Generate a fake pickup signal.

        The generated signal is a simple linear function.

        Parameters
        ----------
        npoints : int
            Number of data points.
        start_at : float, optional
            Starting point, default is 0.
        """
        return np.linspace(start_at, npoints, npoints, endpoint=False)

    def _fill_nexus_entry(self) -> Self:
        """
        Fill the NXentry with the Data objects.

        'data_processed' and 'data_raw' are added as NXsubentry.
        """
        # Add data
        self.nxentry["processed"] = nx.NXsubentry(self.data_processed)
        self.nxentry["processed"].attrs["default"] = "analysis"
        self.nxentry["raw"] = nx.NXsubentry(self.data_raw)
        self.nxentry["raw"].attrs["default"] = "data"

        return self

    def _set_data(self, where: str, name: str, value: Any) -> None:
        """
        Set data in the DataProcessed object.

        Dataset will be written as an NXfield in `data_processed[where][name]`. If the
        dataset already exists, it is replaced (modifying its type and shape
        accordingly).

        If the group name or the dataset name are present in the 'nexus' section of the
        configuration, the attributes are written as well.

        Parameters
        ----------
        where : str
            Location of the dataset in the DataProcessed object.
        name : str
            Dataset name.
        value : Any
            Dataset.
        """
        # Put data
        if name in self.data_processed[where]:
            self.data_processed[where][name].replace(value)
        else:
            self.data_processed[where][name] = value

        # Set group attributes
        if where in self.cfg.nexus.groups:
            for k, v in self.cfg.nexus.groups[where].items():
                self.data_processed[where].attrs[k] = v
        # Set dataset attributes
        if name in self.cfg.nexus.datasets:
            for k, v in self.cfg.nexus.datasets[name].items():
                self.data_processed[where][name].attrs[k] = v

    def _get_data(self, where: str, name: str, checkonly: bool = False) -> Any:
        """
        Get data from the DataProcessed object.

        The data is pulled from `data_processed[where][name]`. If `checkonly` is True,
        only check if the dataset exists.

        Note : the returned value is a *view*, if it is modified, the underlying data
        is modified as well.

        Parameters
        ----------
        where : str
            Location of the dataset in the DataProcessed object.
        name : str
            Dataset name.
        checkonly : bool, optional
            Perform a key existence check without returning the value. Default is False.
        """
        if not checkonly:
            return self.data_processed[where][name].nxdata
        else:
            if where not in self.data_processed:
                return False
            if name not in self.data_processed[where]:
                return False
            else:
                return True

    def _remove_data(self, where: str, name: str) -> None:
        """
        Remove data from the DataProcessed object.

        Parameters
        ----------
        where : str
            Location of the dataset in the DataProcessed object.
        name : str
            Dataset name.
        """
        if self._get_data(where, name, checkonly=True):
            del self.data_processed[where][name]

    def get_data_raw(self, name: str, checkonly: bool = False) -> Any:
        """
        Retrieve data from `data_raw[name]`.

        Note : the returned value is a *view*, if it is modified, the underlying data
        is modified as well.

        Parameters
        ----------
        name : str
            Dataset name.
        checkonly : bool, optional
            Perform a key existence check without returning the value. Default is False.
        """
        if checkonly:
            return name in self.data_raw
        else:
            return self.data_raw[name].nxdata

    def set_data_raw(self, name: str, value: Any) -> None:
        """
        Put data in `data_raw[name]`.

        Dataset will be written as an NXfield in `data_raw[name]`. If the dataset
        already exists, it is replaced (modifying its type and shape accordingly).

        If the dataset name is present in the 'nexus' section of the configuration, the
        attributes are written as well.

        Parameters
        ----------
        name : str
            Dataset name.
        value : Any
            Dataset.
        """
        if name in self.data_raw:
            self.data_raw[name].replace(value)
        else:
            self.data_raw[name] = value

        # Set dataset attributes
        if name in self.cfg.nexus.datasets:
            for k, v in self.cfg.nexus.datasets[name].items():
                self.data_raw[name].attrs[k] = v

    def get_data_processed(self, name: str, checkonly: bool = False) -> Any:
        """
        Get data from the 'results' group of the DataProcessed object.

        The data is pulled from `data_processed[results][name]`. If `checkonly` is True,
        only check if the dataset exists.

        Note : the returned value is a *view*, if it is modified, the underlying data
        is modified as well.

        Parameters
        ----------
        name : str
            Dataset name.
        checkonly : bool, optional
            Perform a key existence check without returning the value. Default is False.
        """
        where = f"{self._results_name}"
        return self._get_data(where, name, checkonly=checkonly)

    def set_data_processed(self, name: str, value: Any) -> None:
        """
        Set data in the 'results' group of the DataProcessed object.

        Dataset will be written as an NXfield in `data_processed[results][name]`. If the
        dataset already exists, it is replaced (modifying its type and shape
        accordingly).

        If the group name or the dataset name are present in the 'nexus' section of the
        configuration, the attributes are written as well.

        Parameters
        ----------
        name : str
            Dataset name.
        value : Any
            Dataset.
        """
        where = f"{self._results_name}"
        self._set_data(where, name, value)

    def remove_data_processed(self, name: str) -> None:
        """
        Remove dataset from the 'results' group of the DataProcessed object.

        The dataset stored at `data_processed[results][name]` is removed.

        Parameters
        ----------
        name : str
            Dataset name.
        """
        where = f"{self._results_name}"
        self._remove_data(where, name)

    def create_data_serie(self) -> None:
        """
        Check if the dictionnary for serie data exists, if not, create it.

        The group hosting the data for the current `idx_serie` is stored at :
        `data_processed[results_{serie_name}{idx_serie}]`.

        If 'results_{serie_name}' is present in the 'nexus' section of the
        configuration, the attributes are written as well.
        """
        baseloc = f"{self._results_name}_{self._serie_name}"
        loc = f"{baseloc}{self.idx_serie}"
        if loc not in self.data_processed:
            self.data_processed.create_serie(self.idx_serie)

            # Set NeXus attributes
            if baseloc in self.cfg.nexus.groups:
                for k, v in self.cfg.nexus.groups[baseloc].items():
                    self.data_processed[loc].attrs[k] = v

    def get_data_serie(self, name: str, checkonly: bool = False) -> Any:
        """
        Get data from the current 'results_serie' group of the DataProcessed object.

        The data is pulled from `data_processed[results_{serie_name}{idx_serie}][name]`.
        If `checkonly` is True, only check if the dataset exists.

        Note : the returned value is a *view*, if it is modified, the underlying data
        is modified as well.

        Parameters
        ----------
        name : str
            Dataset name.
        checkonly : bool, optional
            Perform a key existence check without returning the value. Default is False.
        """
        where = f"{self._results_name}_{self._serie_name}{self.idx_serie}"
        return self._get_data(where, name, checkonly=checkonly)

    def set_data_serie(self, name: str, value: Any) -> None:
        """
        Set data in the current 'results_serie' group of the DataProcessed object.

        Dataset will be written as an NXfield in
        `data_processed[results_{serie_name}{idx_serie}][name]`. If the dataset already
        exists, it is replaced (modifying its type and shape accordingly).

        If the group name or the dataset name are present in the 'nexus' section of the
        configuration, the attributes are written as well.

        Parameters
        ----------
        name : str
            Dataset name.
        value : Any
            Dataset.
        """
        where = f"{self._results_name}_{self._serie_name}{self.idx_serie}"
        self._set_data(where, name, value)

    def remove_date_serie(self, name: str) -> None:
        """
        Remove data in the current 'results_serie' group of the DataProcessed object.

        The dataset at `data_processed[results_{serie_name}{idx_serie}][name]` is
        removed.

        Parameters
        ----------
        name : str
            Dataset name.
        """
        where = f"{self._results_name}_{self._serie_name}{self.idx_serie}"
        self._remove_data(where, name)

    def set_attr_serie(self, name: str, value: Any) -> None:
        """
        Set attribute for the current 'results_serie' NXdata group in data_processed.

        The attribute will be written for the group at
        `data_processed[results_{serie_name}{idx_serie}][name]`.

        Parameters
        ----------
        name : str
            Attribute name.
        value : Any
            Attribute value to set.
        """
        where = f"{self._results_name}_{self._serie_name}{self.idx_serie}"
        self.data_processed[where].attrs[name] = value

    def plot_field(self) -> plt.Figure | None:
        """
        Plot magnetic field.

        Pull data from `data_processed[results]["magfield"]` and plot it against the
        time vector.
        """
        if not self.get_data_processed(
            "magfield_time", checkonly=True
        ) or not self.get_data_processed("magfield", checkonly=True):
            logger.warning("The magnetic field was not computed yet.")
            return None

        fig = plt.figure()
        plt.plot(
            self.get_data_processed("magfield_time"),
            self.get_data_processed("magfield"),
        )
        plt.xlabel("time (s)")
        plt.ylabel("B (T)")
        plt.show()

        return fig

    def get_nexus_filename(self) -> str:
        """Generate output NeXus full file name."""
        return os.path.join(self.cfg.data_directory, self.cfg.expid + ".nx5")

    def consolidate(self) -> Self:
        """
        Add supplementary NeXus entries from configuration file.

        The "nx" section of the configuration is read to add new groups and datasets to
        provide further details about the sample and experiment.
        """
        for nxk, nxv in self.cfg.nx.items():
            # [nx.xyz] section
            nxclass = "NX" + nxk
            nxgroup = nx.NXgroup(nxclass=nxclass)
            for k, v in nxv.items():
                # write dataset
                nxgroup[k] = v
            if nxk in self.nxentry:
                del self.nxentry[nxk]
            self.nxentry[nxk] = nxgroup

        return self

    def resolve_nexus_links(self, path: str = "/") -> Self:
        """
        Replace placeholders in the NXroot group by actual links to other datasets.

        To enable automatic plotting by NeXus programs (such as `nexpy`), the datasets
        plotted one versus the other need to be in the same groups. Common x-axis, such
        as time or magnetic field, are linked to the actual datasets found in
        `data_processed[results]`.

        In practice, this method recursively scans all datasets to find datasets that
        are strings and contains the pre-defined placeholders formatted like so :

        "!link to:path/to/dataset"

        and are replaced with a NXlink targeting the specified dataset.
        """
        nxgrp = self.nxroot[path]
        for obj in nxgrp.values():
            if isinstance(obj, nx.NXfield):
                # is a dataset, not a group
                if isinstance(obj.nxdata, bytes):
                    # dataset is a string
                    val = obj.nxdata.decode("utf-8")
                elif isinstance(obj.nxdata, str):
                    # dataset is a string
                    val = obj.nxdata
                else:
                    # not a string, continue scanning
                    continue
                if val.startswith("!link to:"):
                    # begins with the placeholder flag, read the target
                    target = val.split("!link to:")[1]
                else:
                    # not beginning with the link placeholder
                    continue
                # replace placeholder with an actual link
                self.nxroot[obj.nxpath] = nx.NXlink(
                    self.nxroot[self.nxentry.nxname][target]
                )

            else:
                # is a group, continue scanning within the group
                self.resolve_nexus_links(path=obj.nxpath)

        return self

    def save(
        self, filename: str | Path | None = None, consolidate: bool = True, **kwargs
    ) -> bool:
        """
        Save object to a NeXus[1] compliant HDF5 file.

        It is written using the `NXFile` object (that is an `h5py.File` subclass).
        If a filename is not specified, the `get_nexus_filename()` is used to get a path
        to the output file.

        The `Config` object and the `metadata` attribute are serialized and stored in
        the file to allow for reconstruction of the processing state.

        [1] https://www.nexusformat.org/

        Parameters
        ----------
        filename : str, Path or None
            Full path to the output file, that should't exist. If None (default), the
            filename is determined with the `get_nexus_filename()` method.
        consolidate : bool, optional
            Whether to consolidate the file to add attributes and groups from the
            configuration file. Default is True.
        **kwargs : passed to `nx.NXFile()`.

        Returns
        -------
        status : bool
            True if the file was saved successfully, False otherwise.
        """
        if not filename:
            filename = self.get_nexus_filename()
        if "mode" not in kwargs:
            kwargs["mode"] = "w-"

        logger.info("Saving...")
        # Consolidation
        if consolidate:
            self.consolidate()
        self.resolve_nexus_links()

        # Specify configuration for the program
        self.data_processed["configuration"] = self.cfg.model_dump_json()
        self.data_processed["configuration"].attrs["format"] = "json"

        # Add metadata
        self.data_processed["metadata"] = json.dumps(self.metadata)
        self.data_processed["metadata"].attrs["format"] = "json"

        # Save
        try:
            with nx.NXFile(filename, **kwargs) as f:
                f.writefile(self.nxroot)
            # release
            self.release_nexus_file()
        except Exception as e:
            logger.error(f"Failed to save: {e}.")
            return False

        logger.info(f"Saved at {filename}.")
        return True

    def load(self, filename: str | Path | None) -> Self:
        """
        Load a previously created NeXus file.

        Note that only the first entry of the `NXroot` object will be loaded.

        Parameters
        ----------
        filename : str
            Full path to the file to load.

        Returns
        -------
        obj : BaseProcessor
            Initialized Processor object ready to carry on analysis.
        """
        # Load file
        logger.info(f"Loading NeXus file at {filename}...")
        try:
            with nx.NXFile(filename, mode="rw", recursive=True) as f:
                nxroot = f.readfile()
        except Exception as e:
            logger.error(f"\nFailed to load: {e}.")
            return self

        # Get first entry
        nxentry = next(iter(nxroot.entries.values()))

        # Re-generate Config object
        if "configuration" in nxentry["processed"]["analysis"]:
            self.cfg = self._config_cls.loads(
                nxentry["processed"]["analysis"]["configuration"].nxdata
            )
        else:
            logger.warning(
                "No configuration found in the NeXus file, features will be limited."
            )

        # Set data
        # Processed data
        for key, value in nxentry["processed"]["analysis"].attrs.items():
            # attributes
            self.data_processed.attrs[key] = value
        for key, value in nxentry["processed"]["analysis"].items():
            # groups and fields
            self.data_processed[key] = value
        # Raw data
        for key, value in nxentry["raw"]["data"].attrs.items():
            # attributes
            self.data_raw.attrs[key] = value
        for key, value in nxentry["raw"]["data"].items():
            # groups and fields
            self.data_raw[key] = value

        # Re-build NX data structure
        name_entry = self.cfg.nexus.groups["root"]["name"]
        self.nxentry.nxname = name_entry
        self.nxroot.attrs["default"] = name_entry

        # Recover metadata
        if "metadata" in self.data_processed:
            self.metadata = json.loads(self.data_processed["metadata"].nxdata)
        else:
            logger.warning(
                "No metadata found in the NeXus file, features will be limited."
            )

        # Update flag
        self.is_nexus_file = True

        logger.info("Done.")

        return self

    def release_nexus_file(self) -> None:
        """
        Uncouple NeXus data structure and the NeXus HDF5 file.

        It *should* prevent changes made to the object be reflected in the file.
        """
        self.nxroot.nxfile.clear_lock()
        self.nxroot.nxfile.close()
        self.nxroot._filename = None
        self.nxroot._file = None
