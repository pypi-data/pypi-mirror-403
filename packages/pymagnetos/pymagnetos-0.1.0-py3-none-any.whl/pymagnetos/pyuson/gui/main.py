"""
Application for ultra-sound echoes analysis.

This is the main window definition, built with the custom widgets found in the widgets
folder.
"""

import importlib.metadata
from pathlib import Path

import pyqtgraph as pg
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

from pymagnetos import sp
from pymagnetos.core.gui import BaseMainWindow, widgets

from ._worker import ProcessorWorker
from .widgets import ButtonsWidget, ConfigurationWidget, GraphsWidget, ParamContent

ICON_PATH = str(Path(__file__).parent / "assets" / "icon.png")
REGEXP_EXPID_SEPARATORS = r"[_-]"
PROGRAM_NAME = "pymagnetos"
ALLOWED_FORMAT = ("toml", "json", "nx5", "nxs", "h5", "hdf5")
LOG_LEVEL = "INFO"
VERSION = importlib.metadata.version(PROGRAM_NAME)


class MainWindow(BaseMainWindow):
    """
    A graphical user interface application for ultra-sound echoes analysis.

    The `MainWindow` class defines the main thread with the front-end user interface.

    It is built with the custom components defined in the `widgets` module. Those
    components are referenced in the main thread with a leading `w` :
    `self.wconfiguration` : the "Configuration" tab
    `self.wfiles` : the "Files" tab
    `self.wbatch` : the "Batch processing" tab
    `self.wgraphs` : the widget holding all the graphs
    `self.wbuttons` : the widget holding the main buttons
    `self.wlog` : the widget that streams the log output

    Each of those components exposes signals, to which the main thread connects its own
    methods, instead of connecting directly to the widgets (buttons, checkboxes and the
    like). Those signals are named with a trailing `sig_` so that makes it easy to know
    exactly what should be connected in the main thread.

    When loading a configuration (or a NeXus) file, the main threads creates a worker
    thread (`DataWorker`). The latter instantiates an `EchoProcessor` object that
    perform the actual analysis.

    pyqtSignals
    -------
    All signals emit in their corresponding methods and are connected to the
    corresponding methods in the worker thread.

    `sig_worker_load`
    `sig_worker_rolling`
    `sig_worker_find_f0`
    `sig_worker_demodulate`
    `sig_worker_average`
    `sig_worker_batch`
    `sig_worker_export_csv`
    `sig_worker_save_nexus`
    """

    sig_worker_rolling = pyqtSignal()
    sig_worker_find_f0 = pyqtSignal()
    sig_worker_demodulate = pyqtSignal()
    sig_worker_average = pyqtSignal()
    sig_worker_batch = pyqtSignal(list, bool, bool, bool, bool)
    sig_worker_export_csv = pyqtSignal(str, bool)

    worker: ProcessorWorker

    _window_icon = ICON_PATH

    def __init__(self):
        # Register the widgets to use
        self._type_wbatch = widgets.BatchProcessingWidget
        self._type_wbuttons = ButtonsWidget
        self._type_wconfiguration = ConfigurationWidget
        self._type_wfiles = widgets.FileBrowserWidget
        self._type_wgraphs = GraphsWidget
        self._param_content = ParamContent
        self._type_worker = ProcessorWorker

        super().__init__()

        # Initialize window
        self.setGeometry(300, 300, 900, 450)
        self.setWindowTitle("EchoAnalyzer")
        self.setWindowIcon(QtGui.QIcon(self._window_icon))

        self.logger.info(f"Running pyuson v{VERSION}")

    def init_parameter_tree(self):
        """
        Create the "Configuration" tab.

        It holds the PyQtGraph parameter tree. Each parameter is synchronised with the
        `Configuration` object of the `EchoProcess` worker.
        """
        super().init_parameter_tree()

        # Connect
        self.wconfiguration.sig_echo_index_changed.connect(
            self.update_echo_index_from_settings
        )

    def init_demodulation(self):
        """
        Additionnal initializations for digital demodulation mode.

        Add the Demodulation section in the parameter tree and the frame reference plot.

        It happens only when a worker is created so we can connect its signals as well,
        instead of in `connect_worker()` for the other buttons.
        """
        # Add the Demodulation section to ParameterTree
        self.wconfiguration.init_demodulation_tree()

        # Update the files filter suffix in the batch processing panel
        self.wbatch.line_suffix.setText(".wfm")
        self.wbatch.add_findf0_checkbox()

        # Fill the demodulation parameters from the worker
        for p in self.wconfiguration.demodulation_parameters:
            self.set_param_from_worker(p.name(), context="demodulation")

        # Add the frame reference signal plot tab
        self.wgraphs.add_reference_in_frame_tab()

        # Connect
        self.wconfiguration.sig_find_f0.connect(self.find_f0)
        self.sig_worker_find_f0.connect(self.worker.find_f0)
        self.worker.sig_find_f0_finished.connect(self.find_f0_finished)
        self.wconfiguration.sig_demodulate.connect(self.demodulate)
        self.sig_worker_demodulate.connect(self.worker.demodulate)
        self.worker.sig_demodulate_finished.connect(self.demodulate_finished)

    def init_batch_processing(self):
        """
        Create the "Batch processing tab.

        It's multi-panel file picker, where the user can queue files to be
        batch-processed with the same settings.
        """
        super().init_batch_processing()

        # Connect
        self.wbatch.sig_echo_index_changed.connect(self.update_echo_index_from_batch)

    def init_buttons(self):
        """
        Create and connect the main action buttons.

        The created buttons and their functions are :
        Load Data : load raw data
        Show Frames : display raw data from frames specified in the settings
        Rolling average : apply rolling average
        Refresh : re-compute the average, attenuation and phase-shift
        Export as CSV : export the results for the current echo index as a CSV file
        Save as NeXus : export all data as a single NeXus (hdf5) file
        """
        super().init_buttons()

        # Connect
        self.wbuttons.sig_show.connect(self.show_frames)
        self.wbuttons.sig_rolling.connect(self.rolling_average)
        self.wbuttons.sig_refresh.connect(self.roi_changed)
        self.wbuttons.sig_save_csv.connect(self.export_csv)
        self.wbuttons.sig_save_nexus.connect(self.save_nexus)

    def init_plots(self):
        """
        Create the graph area that holds all the plots.

        The user-draggable ROI defining the time window in which the data is averaged is
        connected here.
        """
        super().init_plots()

        # Connect
        self.wgraphs.sig_roi_changed.connect(self.roi_changed)

        # Connect ROI changed from the tree
        self.wconfiguration.settings_parameters.child(
            "analysis_window"
        ).sigValueChanged.connect(self.update_roi)

    def init_log(self):
        """
        Create the widget where the log will be printed.

        The logger is shared with the `pyuson` package-level logger so stream is also
        printed in stdout and the log file.
        """
        super()._init_log(PROGRAM_NAME, log_level=LOG_LEVEL)

    @pyqtSlot()
    def load_file(self):
        """
        Load a configuration or NeXus file and start a worker.

        Callback for when the "File" parameter changes, or a file is drag & dropped in
        the window.
        """
        super().load_file()
        if self.worker.proc.is_digital:
            self.init_demodulation()

    def set_param_from_worker(self, param_name: str, context: str):
        """
        Set a parameter read from the `Config` object of the `EchoProcessor` worker.

        Parameters
        ----------
        param_name : str
            Name of the parameter in the tree and `Config`.
        context : {"parameters", "settings", "demodulation"}
            Configuration file section.
        """
        if context == "demodulation":
            if hasattr(self.worker.proc.cfg.demodulation, param_name):
                config_value = getattr(self.worker.proc.cfg.demodulation, param_name)
                if param_name in self.wconfiguration.parameters_to_parse:
                    # special case that needs to be converted to string
                    config_value = self.wconfiguration.get_numbers_from_text(
                        config_value
                    )

                self.wconfiguration.demodulation_parameters[param_name] = config_value
        else:
            super().set_param_from_worker(param_name, context)

    def connect_worker(self):
        """
        Connect signals from the main thread to tasks in the worker.

        Note that the demodulation tasks are initialized in the
        `init_parameter_tree_demodulation()` method instead.
        """
        super().connect_worker()

        # Rolling average
        self.sig_worker_rolling.connect(self.worker.rolling_average)
        self.worker.sig_rolling_finished.connect(self.rolling_average_finished)

        # Average frames and computation
        self.sig_worker_average.connect(self.worker.average_frame)
        self.worker.sig_average_finished.connect(self.average_frame_finished)

        # Export as CSV
        self.sig_worker_export_csv.connect(self.worker.export_as_csv)
        self.worker.sig_export_csv_finished.connect(self.export_csv_finished)

    @pyqtSlot(str, str)
    def set_worker_config_from_tree(self, param_name: str, context: str):
        """
        Read parameter from the Parameter Tree and set its sibling in the Config object.

        Callback for any change in the the "Parameters", "Settings" and "Demodulation"
        sections of the parameter tree, the arguments are passed with the signal.

        Parameters
        ----------
        param_name : str
            Name of the parameter in the Parameter Tree.
        context : {"parameters", "settings", "demodulation"}
            Define where the key is stored in the Config object (corresponding to the
            configuration file section).
        """
        if context == "demodulation":
            current_value = self.wconfiguration.demodulation_parameters[param_name]
            if param_name in self.wconfiguration.parameters_to_parse:
                # special case that needs to be parsed
                current_value = self.wconfiguration.get_numbers_from_text(current_value)
            setattr(self.worker.proc.cfg.demodulation, param_name, current_value)
        else:
            super().set_worker_config_from_tree(param_name, context)

    @pyqtSlot()
    def load_data_finished(self):
        """
        Show frames after data is loaded.

        Callback for when the worker has finished loading data.
        """
        self.show_frames()
        self.align_field_finished()
        self.roi_changed()
        super().load_data_finished()

    @pyqtSlot()
    def align_field_finished(self):
        """
        Re-plot magnetic field with its new time vector.

        Set the crosshair that tracks frames in the plot on mouse hover, and store
        increasing and decreasing magnetic field indices to plot them in different
        colors.

        Callback for when the worker has finished loading data. This is re-triggered
        everytime the time vector is susceptible to change (subsampling, ...).
        """
        # Update field plot axis label
        self.wgraphs.field.setLabel("top", "frame (#)")

        super().align_field_finished()

    @pyqtSlot()
    def find_f0(self):
        """
        Find center frequency.

        Send the signal to the worker to find the radio-frequency from the signal (or
        the configuration file). Callback for the "Find f0" button in the demodulation
        section of the parameter tree.
        """
        if not self.check_data_loaded():
            return
        self.disable_buttons()
        self.sig_worker_find_f0.emit()

    @pyqtSlot(float)
    def find_f0_finished(self, f0: float):
        """
        Update f0 in the parameter tree.

        Callback for when the worker has finished the frequency detection. `f0` is
        passed with the signal.
        """
        self.wconfiguration.demodulation_parameters["f0"] = f0

        self.enable_buttons()

    @pyqtSlot()
    def demodulate(self):
        """
        Run the digital demodulation.

        Create a progress bar and send the signal to the worker to perform the digital
        demodulation. Callback for the "Demodulate" button in the "Demodulation" section
        of the parameter tree.
        """
        if not self.check_data_loaded():
            return
        self.disable_buttons()

        # Create the progress bar
        nchunks = self.worker.proc.nframes
        self.pbar_demodulation = widgets.PopupProgressBar(
            min=0, max=nchunks, title="Digital demodulation"
        )
        self.worker.sig_demodulation_progress.connect(
            self.pbar_demodulation.update_progress
        )
        self.pbar_demodulation.start_progress()

        self.sig_worker_demodulate.emit()

    @pyqtSlot()
    def demodulate_finished(self):
        """
        Show the frames demodulated signal and run computations after demodulation.

        Callback for when the worker has finished the digital demodulation.
        """
        self.pbar_demodulation.close()
        self.worker.sig_demodulation_progress.disconnect()

        # Rolling average is resetted and signal might be subsampled
        self.align_field_finished()
        self.show_frames()
        self.roi_changed()

        self.enable_buttons()

    @pyqtSlot()
    def show_frames(self):
        """
        Show some frames echoes, in amplitude and phase.

        Only the data for the frames specified in the settings are shown. It might seem
        convoluted because it is needed to fetch the correct dataset names, depending on
        whether we're in analog or digital mode.

        Callback for the "Show frames" button, also triggered whenever new data is
        loaded (raw or demodulated).
        """
        if not self.check_data_loaded():
            return
        elif "time_meas" not in self.worker.proc.data_raw:
            self.logger.warning(
                "[GUI] Data was not properly loaded, check messages above."
            )
            return

        # Clear existing traces
        self.wgraphs.amp_frame.clearPlots()
        self.wgraphs.phase_frame.clearPlots()
        if self.worker.proc.is_digital:
            self.wgraphs.reference_frame.clearPlots()

        frame_indices = self.worker.proc.cfg.settings.frame_indices
        for ind in frame_indices:
            idx = int(ind)

            # Set the curve legend only for the last one
            if idx == frame_indices[-1]:
                legend_flag = True
            else:
                legend_flag = False

            if self.worker.proc.is_digital:
                # Plot raw trace
                self.wgraphs.amp_frame.plot(
                    self.worker.proc.get_data_raw("time_meas"),
                    self.worker.proc.get_data_raw(self.worker.proc._sig_name)[:, idx],
                    pen=self.wgraphs.pen_amp,
                )
                # Plot demodulated results if it exists
                iname = self.worker.proc.measurements[0]
                qname = self.worker.proc.measurements[1]
                if self.worker.proc.get_data_processed(
                    iname, checkonly=True
                ) and self.worker.proc.get_data_processed(qname, checkonly=True):
                    self.show_frames_demodulated()
                # Plot reference trace
                self.wgraphs.reference_frame.plot(
                    self.worker.proc.get_data_raw("time_meas"),
                    self.worker.proc.get_data_raw("reference")[:, idx],
                    pen=pg.mkPen(color=pg.intColor(idx), hues=len(frame_indices)),
                )
            else:
                # Analog mode
                aname = self.worker.proc.measurements[0]
                self.wgraphs.amp_frame.plot(
                    self.worker.proc.get_data_raw("time_meas"),
                    self.worker.proc.get_data_raw(aname)[:, idx],
                    pen=self.wgraphs.pen_amp,
                )
                iname = self.worker.proc.measurements[1]
                self.wgraphs.phase_frame.plot(
                    self.worker.proc.get_data_raw("time_meas"),
                    self.worker.proc.get_data_raw(iname)[:, idx],
                    pen=self.wgraphs.pen_in_phase,
                    name="in-phase" if legend_flag else None,
                )
                qname = self.worker.proc.measurements[2]
                self.wgraphs.phase_frame.plot(
                    self.worker.proc.get_data_raw("time_meas"),
                    self.worker.proc.get_data_raw(qname)[:, idx],
                    pen=self.wgraphs.pen_out_phase,
                    name="out-of-phase" if legend_flag else None,
                )

    def show_frames_demodulated(self):
        """Overlay demodulation result on raw frames."""
        # Get measurements names
        iname = self.worker.proc.measurements[0]
        qname = self.worker.proc.measurements[1]

        # Get correct time vector if decimation was used
        if self.worker.proc.is_decimated:
            xt = self.worker.proc.get_data_processed("time_meas")
        else:
            xt = self.worker.proc.get_data_raw("time_meas")

        # Change labels
        self.wgraphs.phase_frame.setLabel("left", "phase (rad)")

        # Compute amplitude and phase of demodulated signal
        frames_ind = [int(ind) for ind in self.worker.proc.cfg.settings.frame_indices]
        amplitude = sp.compute_amp_iq(
            self.worker.proc.get_data_processed(iname)[:, frames_ind],
            self.worker.proc.get_data_processed(qname)[:, frames_ind],
        )
        phase = sp.compute_phase_iq(
            self.worker.proc.get_data_processed(iname)[:, frames_ind],
            self.worker.proc.get_data_processed(qname)[:, frames_ind],
        )

        # Rescale amplitude to show it with the raw trace on the same scale
        amplitude = sp.rescale_a2b(
            amplitude,
            self.worker.proc.get_data_raw(self.worker.proc._sig_name)[:, frames_ind],
        )

        for ind in range(len(frames_ind)):
            idx = int(ind)
            self.wgraphs.amp_frame.plot(
                xt,
                amplitude[:, idx],
                pen=self.wgraphs.pen_amp_demod,
            )
            self.wgraphs.phase_frame.plot(
                xt,
                phase[:, idx],
                pen=self.wgraphs.pen_phase_demod,
            )

    @pyqtSlot()
    def rolling_average(self):
        """
        Perform rolling average.

        Send the signal to the worker to perform the rolling average. Callback for the
        "Rolling average" button.
        """
        if not self.check_data_loaded():
            return
        self.disable_buttons()
        self.sig_worker_rolling.emit()

    @pyqtSlot()
    def rolling_average_finished(self):
        """
        Plot magnetic field in case it was subsampled and retrigger computations.

        Callback for the when the worker has finished the rolling average.
        """
        self.align_field_finished()
        self.roi_changed()
        self.enable_buttons()

    @pyqtSlot()
    def export_csv(self):
        """
        Export results for the current echo index as CSV.

        Generate a default file name and open a file picker dialog for the user to
        choose an output file. Determine if the attenuation should be converted to
        dB/cm, and send the signal to the worker to save the results as CSV.
        Callback for the "Export as CSV" button.
        """
        if not self.check_data_loaded():
            return

        self.disable_buttons()

        default_fname = self.worker.proc.get_csv_filename()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save current echo index as...",
            default_fname,
            "Text files (*.txt, *.csv, *.tsv)",
        )

        if fname:
            self.sig_worker_export_csv.emit(
                fname, self.wbuttons.checkbox_to_cm.isChecked()
            )
        else:
            self.logger.error("[GUI] Invalid output file name for CSV file.")
            self.export_csv_finished()

    @pyqtSlot()
    def export_csv_finished(self):
        """Callback for when the worker has finished exporting as CSV."""
        self.enable_buttons()

    @pyqtSlot()
    def batch_process(self):
        """
        Run batch processing on selected files.

        List files in the queue, determine corresponding experiment IDs, create a
        progress bar and send the signal to the worker to perform the batch-processing.
        Callback for the "Batch process" button in the "Batch processing" tab.
        """
        super().batch_process()

        # Get settings
        rolling_average = self.wbatch.checkbox_rolling_average.isChecked()
        to_csv = self.wbatch.checkbox_save_as_csv.isChecked()
        to_cm = self.wbuttons.checkbox_to_cm.isChecked()
        if hasattr(self.wbatch, "checkbox_find_f0"):
            find_f0 = self.wbatch.checkbox_find_f0.isChecked()
        else:
            find_f0 = False

        # Set up progress bar
        self.pbar_batch = widgets.PopupProgressBar(
            min=0, max=len(self.batch_expids), title="Batch processing"
        )
        self.worker.sig_batch_progress.connect(self.batch_process_step_finished)
        self.pbar_batch.start_progress()

        # Run the batch processing
        self.disable_buttons()
        self.sig_worker_batch.emit(
            self.batch_expids, rolling_average, to_csv, to_cm, find_f0
        )

    @pyqtSlot(int)
    def batch_process_step_finished(self, idx: int):
        """Track progress of the batch processing."""
        self.pbar_batch.update_progress(idx)
        super().batch_process_step_finished(idx)

    @pyqtSlot()
    def batch_process_finished(self):
        """
        Cleanup after batch-processing.

        Callback for when the worker has finished the batch-processing.
        """
        self.pbar_batch.close()
        super().batch_process_finished()

    @pyqtSlot()
    def roi_changed(self):
        """
        Trigger averaging and computation of attenuation and phase shift.

        Callback for when the ROI is changed.
        """
        # Get time range
        xmin, xmax = self.wgraphs.roi.getRegion()

        # Check the ROI was changed since it was created
        if (xmin, xmax) == (0, 1):
            return

        # Update parameter in the tree if the region was changed from the graph
        if self.flag_do_update_roi:
            self.flag_do_update_roi = False
            self.wconfiguration.settings_parameters["analysis_window"] = (
                self.wconfiguration.get_numbers_from_text([xmin, xmax])
            )
            self.flag_do_update_roi = True

        self.logger.info(f"[GUI] Analysis window set to : {xmin, xmax}")

        if not self.check_data_loaded():
            return

        self.average_frame()

    @pyqtSlot()
    def update_roi(self):
        """
        Update the ROI in the graph from "Analysis time window" in the parameter tree.

        Use `flag_do_update_roi` to check if the change is done programatically or from
        the user.
        In the first case, this function is ignored.
        In the second case, the ROI in the graph is updated and computation is
        triggered.
        """
        if self.flag_do_update_roi:
            # ROI changed from the tree, update the ROI in the graph
            new_region = self.wconfiguration.get_numbers_from_text(
                self.wconfiguration.settings_parameters["analysis_window"]
            )
            if not isinstance(new_region, list):
                # for type checking
                return
            if len(new_region) != 2:
                self.logger.error(f"[GUI] Invalid analysis window : {new_region}")
                return
            elif new_region[0] >= new_region[1]:
                self.logger.error(f"[GUI] Invalid analysis window : {new_region}")
                return

            # Update ROI, without recomputing
            self.flag_do_update_roi = False
            self.wgraphs.roi.setRegion(new_region)
            self.flag_do_update_roi = True
        else:
            return

    def average_frame(self):
        """
        Average frame and compute attenuation and phase-shift.

        The current analysis window and echo index are used. Send the signal to the
        worker to perform the average and the computation. This happens everytime the
        ROI is changed.
        """
        if not self.check_data_loaded():
            return
        self.disable_buttons()
        self.sig_worker_average.emit()

    @pyqtSlot(bool)
    def average_frame_finished(self, status: bool):
        """
        Update the plots with the new attenuation and phase-shift.

        Callback for when the worker has finished averaging and computing. `status` is
        passed with the pyqtSignal, it tells if the averaging was successful.
        """
        if not status:
            self.enable_buttons()
            self.logger.error(
                "[GUI] Averaging frames failed, check the messages above."
            )
            return

        # Check the magnetic field is aligned
        if not self.check_field_aligned():
            # Force align
            self.worker.align_field()

        # Plot results
        # Attenuation
        # Versus magnetic field (dB/cm)
        self.plot_var_field(self.wgraphs.amp_field, "attenuation", mult=1e-2)
        # Versus time (dB/cm)
        self.plot_var_time(self.wgraphs.amp_time, "attenuation", mult=1e-2)

        # Phase-shift
        # Versus magnetic field
        self.plot_var_field(self.wgraphs.phase_field, "phaseshift")
        # Versus time
        self.plot_var_time(self.wgraphs.phase_time, "phaseshift")

        self.enable_buttons()

    def plot_field(self):
        """
        Display magnetic field versus time.

        The pickup coil voltage and the magnetic field are shown. If it is aligned with
        the experiment time vector, a cross-hair tracks the frame number on mouse hover.
        """
        super().plot_field()

        # If data was loaded, we can show frames indices on top with a crosshair
        if self.check_data_loaded():
            self.wgraphs.time2frame_scale = (
                self.worker.proc.get_data_processed("time_exp").size
                / self.worker.proc.get_data_processed("magfield_time")[-1]
            )

            # Create the crosshair if it does not exist yet
            if not hasattr(self.wgraphs, "field_vline"):
                self.wgraphs.init_field_crosshair()

    @pyqtSlot()
    def update_echo_index_from_batch(self):
        """Update echo index in the parameter tree when changed from the Batch tab."""
        self.wconfiguration.settings_parameters["echo_index"] = self.wbatch.echo_index

    @pyqtSlot()
    def update_echo_index_from_settings(self):
        """Update echo index in the Batch tab when changed from the parameter tree."""
        self.wbatch.echo_index = self.wconfiguration.settings_parameters["echo_index"]

    def reset(self):
        """Quit and delete worker and thread, resetting plots and parameters."""
        # Quit thread
        super().reset()

        # Reset demodulation parameter section
        if (
            hasattr(self.wconfiguration, "demodulation_parameters")
            and self.wconfiguration.demodulation_parameters is not None
        ):
            self.wconfiguration.host_parameters.removeChild(
                self.wconfiguration.demodulation_parameters
            )
            self.wconfiguration.demodulation_parameters = None
