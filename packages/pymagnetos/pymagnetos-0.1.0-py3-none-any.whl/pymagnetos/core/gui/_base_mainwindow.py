"""
Generic application oriented toward a configuration > analysis > display workflow.

It consists of a Configuration Panel on the left, a graphs area on the right, some
buttons on the bottom right corner and the application log on the bottom right.
The Configuration Panel is a tab, other tabs are : a file browser and a batch processing
tab.

The BaseMainWindow should be sub-classed to customize buttons and plots, connect the
signals to a worker embeding a Processor object. See example implementations in the
`pyuson` or `pytdo` modules.
"""

import logging
import re
from pathlib import Path

from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from .widgets import TextLoggerWidget

REGEXP_EXPID_SEPARATORS = r"[_-]"
ALLOWED_FORMAT = ("toml", "json", "nx5", "nxs", "h5", "hdf5")


class BaseMainWindow(QtWidgets.QMainWindow):
    """
    A generic graphical user interface application.

    The `MainWindow` class defines the main thread with the front-end user interface.
    It creates the main general layout and include some generic functions related to
    standard analysis processes : generate a PyQtGraph ParameterTree, connect to a
    worker in its own thread, load and plot a magnetic field...

    The main window consists of the following :
    - A left panel with three tabs, the Configuration tab, a file browser and a Batch
    processing tab,
    - A right panel with all the plots. There can be any number of graphs, in any number
    of tabs,
    - A bottom-left box with the main action button,
    - A bottom-right box with the log.

    It is built with pre-defined widgets that must implement a specific interface :
    One should subclass this `BaseMainWindow` class and register those widgets as
    private attributes before calling `super().__init__()`. The widgets' class must be
    registered, not an instance of such, e.g. do `ConfigurationWidget`, not
    `ConfigurationWidget()`. The mandatory widgets to implement and register are :

    - _type_wconfiguration : a configuration widget for the parameter tree
    - _param_content : a simple class that provides the ParameterTree content,
    - _type_wfiles : a file browser widget,
    - _type_wbatch : a batch-processing widget,
    - _type_wgraphs : a graph widget that holds all the plots,
    - _type_wbuttons : a widget with the main action buttons,
    - _type_worker : a worker object.

    Each of thos classes are instantiated here with the `_type_` removed, e.g.
    `_type_wgraphs` is intantiated as `wgraphs`.

    Each of those components exposes signals, to which the main thread connects its own
    methods, instead of connecting directly to the widgets (buttons, checkboxes and the
    like). Those signals are named with a trailing `sig_` so that makes it easy to know
    exactly what should be connected in the main thread.

    When loading a configuration (or a NeXus) file, the main thread creates a worker
    thread. The latter instantiates an Processor object that perform the actual
    analysis.

    pyqtSignals
    -------
    All signals emit in their corresponding methods and are connected to the
    corresponding methods in the worker thread. Any number of supplementary signals can
    be implemented in subclasses.

    `sig_worker_load`
    `sig_worker_batch`
    `sig_worker_save_nexus`
    """

    sig_worker_load = pyqtSignal()
    sig_worker_batch = pyqtSignal()
    sig_worker_save_nexus = pyqtSignal(str)

    _type_wbatch: type
    _type_wbuttons: type
    _type_wconfiguration: type
    _type_wfiles: type
    _type_wgraphs: type
    _param_content: type
    _type_worker: type

    def __init__(self):
        super().__init__()

        # Set flags
        # Check if the ROI change is done by the user or programatically
        self.flag_do_update_roi = True
        # Check if the experiment ID should be reloaded or if the field is just being
        # updated
        self.flag_do_reload_expid = True

        # Initialize components
        self.init_parameter_tree()
        self.init_files()
        self.init_batch_processing()
        self.init_buttons()
        self.init_plots()
        self.init_log()
        self.init_layout()
        self.setCentralWidget(self.splitter0)

        # Setup drag&drop
        self.setAcceptDrops(True)

        # Show window
        self.show()

    def init_parameter_tree(self):
        """
        Create the "Configuration" tab.

        It holds the PyQtGraph parameter tree. Each parameter is synchronised with the
        `Config` object of the Processor worker.
        """
        self.wconfiguration = self._type_wconfiguration(self._param_content)

        # Connect
        self.wconfiguration.sig_file_changed.connect(self.load_file)
        self.wconfiguration.sig_expid_changed.connect(self.reload_expid)
        self.wconfiguration.sig_autoload_changed.connect(
            self.update_autoload_from_config
        )
        self.wconfiguration.sig_reload_config.connect(self.load_file)
        self.wconfiguration.sig_save_config.connect(self.save_config)

    def init_files(self):
        """
        Create the "Files" tab.

        It lists files in a directory, one can double-click a file to load either a
        configuration file or change the experiment ID.
        """
        self.wfiles = self._type_wfiles()

        # Connect
        self.wfiles.sig_file_selected.connect(self.select_file_in_browser)
        self.wfiles.sig_checkbox_changed.connect(self.update_autoload_from_files)

    def init_batch_processing(self):
        """
        Create the "Batch processing tab.

        It's multi-panel file picker, where the user can queue files to be
        batch-processed with the same settings.
        """
        self.wbatch = self._type_wbatch()

        # Connect
        self.wbatch.sig_batch_process.connect(self.batch_process)

    def init_buttons(self):
        """Create the main action buttons."""
        self.wbuttons = self._type_wbuttons()

        # Connect
        self.wbuttons.sig_load.connect(self.load_data)
        self.wbuttons.sig_save_nexus.connect(self.save_nexus)

    def init_plots(self):
        """Create the graph area that holds all the plots."""
        self.wgraphs = self._type_wgraphs()

    def init_log(self):
        """Initiliaze the log, calling the `_init_log()` method."""
        raise NotImplementedError(
            "Subclass must implement this method, using the "
            "_init_log(program_name, log_level) method"
        )

    def _init_log(self, program_name: str, log_level: str = "info"):
        """
        Create the widget where the log will be printed.

        The logger is shared with the package-level logger so stream is also printed in
        stdout and the log file.
        """
        log_handler = TextLoggerWidget(self)

        # Set up the formatter
        log_handler.setFormatter(
            logging.Formatter(
                "{asctime}.{msecs:3g} [{levelname}] : {message}",
                style="{",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        # Set up the logger
        self.logger = logging.getLogger(program_name)
        self.logger.addHandler(log_handler)
        self.logger.setLevel(log_level)

        # Store the logger widget (QPlainTextEdit)
        self.wlog = log_handler.widget

    def init_layout(self):
        """
        Set up the main layout.

        It is composed of a 4 panels seperated with resizable splitters.
        Panel 1 (top left) : Tabs with Configuration, Files and Batch processing
        Panel 2 (bottom left) : Action buttons
        Panel 3 (top right) : Graphs
        Panel 4 (bottom right) : Log
        """
        self.splitter0 = QtWidgets.QSplitter(self)
        splitter1 = QtWidgets.QSplitter(Qt.Orientation.Vertical, self)
        splitter2 = QtWidgets.QSplitter(Qt.Orientation.Vertical, self)

        self.config_tabs = QtWidgets.QTabWidget(self)
        self.config_tabs.addTab(self.wconfiguration, "Configuration")
        self.config_tabs.addTab(self.wfiles, "Files")
        self.config_tabs.addTab(self.wbatch, "Batch processing")

        splitter1.addWidget(self.config_tabs)
        splitter1.addWidget(self.wbuttons)

        splitter2.addWidget(self.wgraphs)
        splitter2.addWidget(self.wlog)

        self.splitter0.addWidget(splitter1)
        self.splitter0.addWidget(splitter2)

    @pyqtSlot()
    def load_file(self):
        """
        Load a configuration or NeXus file and start a worker.

        Callback for when the "File" parameter changes, or a file is drag & dropped in
        the window.
        """
        self.create_worker()
        self.plot_field()

        if self.worker.is_dataloaded:
            # If NeXus file, data is already ready to be shown
            self.load_data_finished()
            if self.check_field_aligned():
                # Allow plotting versus field
                self.align_field_finished()
            else:
                # Force align field
                self.worker.align_field()
        else:
            # Enable the "Load data" button
            self.wbuttons.button_load.setEnabled(True)

        # Set experiment ID read from the configuration, without reloading it
        self.flag_do_reload_expid = False
        self.wconfiguration.files_parameters["expid"] = self.worker.proc.expid
        self.flag_do_reload_expid = True

        # Update file explorer directory
        self.wfiles.file_browser.set_directory(self.worker.proc.cfg.data_directory)
        self.wbatch.current_directory = self.worker.proc.cfg.data_directory
        self.wbatch.prefix = re.split(REGEXP_EXPID_SEPARATORS, self.worker.proc.expid)[
            0
        ]

        # Enable buttons
        self.wconfiguration.button_reload_data.setEnabled(True)
        self.wconfiguration.button_save_config.setEnabled(True)

        # Load data directly if autoload is on
        if self.wconfiguration.files_parameters["autoload"]:
            self.load_data()

    def create_worker(self):
        """Create the Processor object in its own worker thread."""
        # Delete previous instance if any
        if hasattr(self, "worker_thread"):
            self.reset()

        # Create thread
        self.worker_thread = QThread()
        # Create worker
        self.worker = self._type_worker(self.wconfiguration.files_parameters["file"])

        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)

        # Connect signals and slots
        self.connect_worker()

        # Start the thread
        self.worker_thread.start()

        # Read the configuration
        self.set_tree_from_worker()

    def set_tree_from_worker(self):
        """
        Set the parameters in the parameter tree from the worker configuration.

        Loop through all parameter in the "parameters" and "settings" section and set
        them from the `Config` object of the Processor object.
        """
        # In the Parameters section
        for p in self.wconfiguration.param_parameters:
            self.set_param_from_worker(p.name(), context="parameters")
        # In the Settings section
        for p in self.wconfiguration.settings_parameters:
            self.set_param_from_worker(p.name(), context="settings")

    def set_param_from_worker(self, param_name: str, context: str):
        """
        Set a parameter read from the `Config` object of the Processor worker.

        Parameters
        ----------
        param_name : str
            Name of the parameter in the tree and `Config`.
        context : {"parameters", "settings"}
            Configuration file section.
        """
        match context:
            case "parameters":
                if hasattr(self.worker.proc.cfg.parameters, param_name):
                    self.wconfiguration.param_parameters[param_name] = getattr(
                        self.worker.proc.cfg.parameters, param_name
                    )
            case "settings":
                if hasattr(self.worker.proc.cfg.settings, param_name):
                    config_value = getattr(self.worker.proc.cfg.settings, param_name)
                    if param_name in self.wconfiguration.parameters_to_parse:
                        # special case that needs to be converted to string
                        config_value = self.wconfiguration.get_numbers_from_text(
                            config_value
                        )

                    self.wconfiguration.settings_parameters[param_name] = config_value
            case _:
                raise ValueError(f"Error : unknown configuration section : {context}")

    def connect_worker(self):
        """Connect signals from the main thread to tasks in the worker."""
        # Load data and align field
        self.sig_worker_load.connect(self.worker.load_data)
        self.worker.sig_load_finished.connect(self.load_data_finished)
        self.worker.sig_align_finished.connect(self.align_field_finished)

        # Batch process
        self.sig_worker_batch.connect(self.worker.batch_process)
        self.worker.sig_batch_finished.connect(self.batch_process_finished)

        # Save as NeXus
        self.sig_worker_save_nexus.connect(self.worker.save_as_nexus)
        self.worker.sig_save_nexus_finished.connect(self.save_nexus_finished)

        # Watch changes from the parameter tree to update the worker configuration
        self.wconfiguration.sig_parameter_changed.connect(
            self.set_worker_config_from_tree
        )

    @pyqtSlot(str, str)
    def set_worker_config_from_tree(self, param_name: str, context: str):
        """
        Read parameter from the Parameter Tree and set its sibling in the Config object.

        Callback for any change in the the "Parameters", "Settings" sections of the
        parameter tree, the arguments are passed with the signal.

        Parameters
        ----------
        param_name : str
            Name of the parameter in the Parameter Tree.
        context : {"parameters", "settings"}
            Define where the key is stored in the Config object (corresponding to the
            configuration file section).
        """
        match context:
            case "parameters":
                setattr(
                    self.worker.proc.cfg.parameters,
                    param_name,
                    self.wconfiguration.param_parameters[param_name],
                )
            case "settings":
                current_value = self.wconfiguration.settings_parameters[param_name]
                if param_name in self.wconfiguration.parameters_to_parse:
                    # special case that needs to be parsed
                    current_value = self.wconfiguration.get_numbers_from_text(
                        current_value
                    )
                    self.logger.debug(
                        f"[GUI] Setting Config from tree : {param_name} : {current_value}"
                    )
                setattr(self.worker.proc.cfg.settings, param_name, current_value)
            case _:
                raise ValueError(f"Unknown configuration section : {context}")

    @pyqtSlot()
    def reload_expid(self):
        """
        Reload experiment ID, resetting the data via the worker.

        `expid` is a property of the Processor object, when it is changed, it triggers a
        reinitializtion of the object.

        If data autoloading is enabled, the data is reloaded here.

        Callback for a change of the experiment ID in the "Files" section of the
        parameter tree and of the `Reload` button.
        """
        if not self.check_config_loaded():
            self.logger.warning("[GUI] No configuration file loaded.")
            return
        if not self.flag_do_reload_expid:
            # The experiment ID is being changed programatically, do not update
            return
        # Infer experiment ID
        expid = self.infer_expid(self.wconfiguration.files_parameters["expid"])
        # Set it, without reloading since that's we're doing
        self.flag_do_reload_expid = False
        self.wconfiguration.files_parameters["expid"] = expid
        self.flag_do_reload_expid = True

        self.logger.info(
            f"[GUI] Reloading experiment ID, from {self.worker.proc.expid} to {expid}"
        )

        # Set the new experiment ID in the worker
        self.worker.proc.expid = expid
        self.worker.is_dataloaded = False

        # Prepare
        self.disable_buttons()
        self.wgraphs.clear_all_plots()
        self.plot_field()
        self.wconfiguration.button_reload_data.setEnabled(True)
        self.wconfiguration.button_save_config.setEnabled(True)
        self.wbuttons.button_load.setEnabled(True)

        if self.wconfiguration.files_parameters["autoload"]:
            # Autoload data
            self.load_data()

    @pyqtSlot()
    def save_config(self):
        """
        Save current configuration as a TOML file.

        A default file name is generated and a file picker dialog box is openned for the
        user to choose an output file.
        """
        if not self.check_config_loaded():
            return

        cfg_file = Path(self.wconfiguration.files_parameters["file"])
        default_fname = cfg_file.with_stem(cfg_file.stem + "-2")
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save configuration file as...",
            directory=str(default_fname),
            filter="TOML files (*.toml), JSON files (*.json)",
            options=QtWidgets.QFileDialog.Option.DontConfirmOverwrite,
        )
        self.worker.proc.cfg.write(fname)

    @pyqtSlot()
    def load_data(self):
        """
        Load data.

        Send the signal to the worker to load data. Callback for the "Load data" button.
        It's also used whenever a new dataset is loaded, if data auto-loading is
        enabled.
        """
        if not self.check_config_loaded():
            self.logger.warning("[GUI] No configuration file loaded.")
            return

        self.disable_buttons()
        self.sig_worker_load.emit()
        self.logger.debug("emitted signal to load data")

    @pyqtSlot()
    def load_data_finished(self):
        """Callback for when the worker has finished loading data."""
        self.enable_buttons()

    @pyqtSlot()
    def align_field_finished(self):
        """
        Re-plot magnetic field with its new time vector.

        Callback for when the worker has finished loading data. This is re-triggered
        everytime the time vector is susceptible to change (subsampling, ...).
        """
        # Checks
        if not self.check_field_aligned():
            return

        # Re-plot magnetic field
        self.plot_field()

        # Get indexer for field up and field down
        t = self.worker.proc.get_data_processed("time_exp")
        b = self.worker.proc.get_data_processed("magfield")
        self.ind_bup = t <= t[b.argmax()]  # increasing B
        self.ind_bdown = t > t[b.argmax()]  # decreasing B
        self.enable_buttons()

    @pyqtSlot()
    def save_nexus(self):
        """
        Save everything as a NeXus file.

        The output file is self-contained, it saves all parameters, echo indices, raw
        and processed data.

        Generate a default file name and open a file picker dialog for the user to
        choose an output file, and send the signal to the worker to save the results as
        NeXus.
        Callback for the "Save as NeXus" button.
        """
        if not self.check_data_loaded():
            return

        self.disable_buttons()

        default_fname = self.worker.proc.get_nexus_filename()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save NeXus file as...",
            default_fname,
            "NeXus files (*.hdf5, *.h5, *.nxs, *.nx5)",
        )

        if fname:
            self.sig_worker_save_nexus.emit(fname)
        else:
            self.logger.error("[GUI] Invalid output file name for NeXus file.")
            self.save_nexus_finished()

    @pyqtSlot()
    def save_nexus_finished(self):
        """Callback for when the worker has finished saving as NeXus."""
        self.enable_buttons()

    @pyqtSlot(bool, str)
    def select_file_in_browser(self, is_toml: bool, filepath: str):
        """
        Select a file and set it as a configuration file or a new experiment ID.

        Callback for when the user double-click on a file in the "Files" tab.
        """
        if is_toml:
            self.wconfiguration.files_parameters["file"] = filepath
        else:
            self.wconfiguration.files_parameters["expid"] = filepath

    @pyqtSlot()
    def batch_process(self):
        """
        Run batch processing on selected files.

        List files in the queue, determine corresponding experiment IDs, create a
        progress bar and send the signal to the worker to perform the batch-processing.
        Callback for the "Batch process" button in the "Batch processing" tab.
        """
        if not self.check_config_loaded():
            self.logger.warning("[GUI] No configuration was loaded.")
            return

        # List files in the queue
        self.batch_files = self.wbatch.get_files_to_process()

        if len(self.batch_files) == 0:
            self.logger.warning("[GUI] No items in batch processing list.")
            return

        # Infer experiments ID from the file names
        self.batch_expids = []
        for file in self.batch_files:
            self.batch_expids.append(self.infer_expid(file))

    @pyqtSlot(int)
    def batch_process_step_finished(self, idx: int):
        """Track progress of the batch processing."""
        # Move file in the "Done" list
        self.wbatch.move_to_done(self.batch_files[idx])

    @pyqtSlot()
    def batch_process_finished(self):
        """
        Cleanup after batch-processing.

        Callback for when the worker has finished the batch-processing.
        """
        self.worker.sig_batch_progress.disconnect()

        # Set the last experiment ID in the parameter tree, without reloading since it
        # is already the currently loaded dataset
        self.flag_do_reload_expid = False
        self.wconfiguration.files_parameters["expid"] = self.batch_expids[-1]
        self.flag_do_reload_expid = True
        self.batch_files = []
        self.batch_expids = []

    @pyqtSlot()
    def roi_changed(self):
        """
        Trigger averaging and computation of attenuation and phase shift.

        Callback for when the ROI is changed.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @pyqtSlot()
    def update_roi(self):
        """Update the ROI in the graph."""
        raise NotImplementedError("Subclasses must implement this method.")

    def infer_expid(self, expid: str) -> str:
        """
        Determine experiment ID from a file name or path.

        If the input is an existing file, it uses the base file name without extension,
        removes "-pickup" and, for WFM files, the channels number, to build the
        experiment ID. Otherwise, it is used as is.
        """
        file_path = Path(expid)

        if file_path.is_file():
            # Input is a file, get the corresponding experiment ID
            if expid.lower().endswith(".wfm"):
                # Remove the _chX bit for WFM files
                res = re.sub(r"_ch\d+\.wfm$", ".wfm", expid, flags=re.IGNORECASE)
                file_path = Path(res)

            infered_expid = file_path.stem.replace("-pickup", "")

            return infered_expid
        else:
            # Input experiment ID is a proper experiment ID, return as is
            return expid

    def plot_field(self):
        """
        Display magnetic field versus time.

        The pickup coil voltage and the magnetic field are shown. If it is aligned with
        the experiment time vector, a cross-hair tracks the frame number on mouse hover.
        """
        if not self.worker.proc.get_data_processed("magfield", checkonly=True):
            self.worker.proc.compute_field()

            if not self.worker.proc.get_data_processed("magfield", checkonly=True):
                # Still no field to plot, maybe there was no pickup and data was not
                # loaded so the pickup signal could be simulated
                self.logger.warning("[GUI] Field was not computed, not plotting.")
                return

        # B(t)
        self.wgraphs.field.clearPlots()
        self.wgraphs.field.plot(
            self.worker.proc.get_data_processed("magfield_time"),
            self.worker.proc.get_data_processed("magfield"),
            pen=self.wgraphs.pen_field,
        )
        self.wgraphs.field.setTitle(
            "Magnetic field (max. field : "
            f"{self.worker.proc.get_data_processed('magfield').max():2.2f}T)"
        )

        # dB/dt (pickup)
        self.wgraphs.dfield.clearPlots()
        if self.worker.proc.get_data_raw(
            "pickup_time", checkonly=True
        ) and self.worker.proc.get_data_raw("pickup", checkonly=True):
            self.wgraphs.dfield.plot(
                self.worker.proc.get_data_raw("pickup_time"),
                self.worker.proc.get_data_raw("pickup"),
                pen=self.wgraphs.pen_field,
            )

    def plot_var_time(self, pgplot, varname: str, mult: float = 1):
        """
        Plot `varname` versus experiment time.

        Used to plot attenuation and phase-shift versus time.
        """
        pgplot.clearPlots()
        pgplot.plot(
            self.worker.proc.get_data_processed("time_exp"),
            self.worker.proc.get_data_serie(varname) * mult,
        )

    def plot_var_field(self, pgplot, varname: str, mult: float = 1):
        """Plot `varname` versus magnetic field.

        Field rise and decay are distinguished with a different color. Corresponding
        indices should be already available from the `ind_bdown` and `ind_bup`
        attributes, that are created in the `align_field_finished()` method.
        """
        pgplot.clearPlots()
        pgplot.plot(
            self.worker.proc.get_data_processed("magfield")[self.ind_bdown],
            self.worker.proc.get_data_serie(varname)[self.ind_bdown] * mult,
            pen=self.wgraphs.pen_bdown,
            name="B down",
        )
        pgplot.plot(
            self.worker.proc.get_data_processed("magfield")[self.ind_bup],
            self.worker.proc.get_data_serie(varname)[self.ind_bup] * mult,
            pen=self.wgraphs.pen_bup,
            name="B up",
        )

    def disable_buttons(self):
        """Disable all buttons and ROIs."""
        self.wconfiguration.disable_buttons()
        self.wbuttons.disable_buttons()
        self.wbatch.disable_buttons()
        self.wgraphs.disable_rois()

    def enable_buttons(self):
        """Enable all buttons and ROIs."""
        self.wconfiguration.enable_buttons()
        self.wbuttons.enable_buttons()
        self.wbatch.enable_buttons()
        self.wgraphs.enable_rois()

    @pyqtSlot()
    def update_autoload_from_files(self):
        """Update the autoload checkbox in the Configuration when toggled in Files."""
        self.wconfiguration.files_parameters["autoload"] = (
            self.wfiles.checkbox_autoload_data.isChecked()
        )

    @pyqtSlot()
    def update_autoload_from_config(self):
        """Update the autoload checkbox in Files when toggled in the Configuration."""
        self.wfiles.checkbox_autoload_data.setChecked(
            self.wconfiguration.files_parameters["autoload"]
        )

    def check_config_loaded(self) -> bool:
        """Check if a worker was initialized."""
        if hasattr(self, "worker"):
            return True
        else:
            return False

    def check_data_loaded(self) -> bool:
        """Check if data was loaded."""
        if not self.check_config_loaded():
            return False
        else:
            if not self.worker.is_dataloaded:
                return False
            else:
                return True

    def check_field_aligned(self) -> bool:
        """Check if the magnetic field is aligned on the experiment time vector."""
        if not self.worker.proc.get_data_processed("magfield", checkonly=True):
            self.logger.warning("[GUI] Magnetic field was not computed.")
            return False
        if not self.worker.proc.get_data_processed("time_exp", checkonly=True):
            self.logger.warning("[GUI] Experiment time vector was not built.")
            return False
        fieldsize = self.worker.proc.get_data_processed("magfield").size
        timesize = self.worker.proc.get_data_processed("time_exp").size
        if fieldsize != timesize:
            return False
        else:
            return True

    def reset(self):
        """Quit and delete worker and thread, resetting plots and parameters."""
        # Quit thread
        if hasattr(self, "worker_thread"):
            self.worker_thread.quit()
            self.worker_thread.deleteLater()
        if hasattr(self, "worker"):
            self.worker.deleteLater()

        # Clear plots
        self.wgraphs.clear_all_plots()
        # Disable buttons
        self.disable_buttons()

    def dragEnterEvent(self, a0: QtGui.QDropEvent | None = None) -> None:
        """Handle drag&drop configuration or data file."""
        if a0.mimeData().hasText():
            a0.accept()
        else:
            a0.ignore()

    def dropEvent(self, a0: QtGui.QDropEvent | None = None) -> None:
        """
        Set the "File" parameter when a file is dropped in the main window.

        This triggers the `load_file()` method.
        """
        for url in a0.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(ALLOWED_FORMAT):
                self.wconfiguration.files_parameters["file"] = file_path

    def closeEvent(self, a0):
        """Quit."""
        if self.check_config_loaded():
            self.reset()
        print("Bye !")
        return super().closeEvent(a0)
