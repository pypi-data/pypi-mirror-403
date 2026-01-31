"""Application for TDO analysis."""

import importlib.metadata
from pathlib import Path

from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

from pymagnetos.core.gui import BaseMainWindow
from pymagnetos.core.gui.widgets import BatchProcessingWidget, FileBrowserWidget

from . import widgets
from ._worker import DataWorker

ICON_PATH = str(Path(__file__).parent / "assets" / "icon.png")
REGEXP_EXPID_SEPARATORS = r"[_-]"
PROGRAM_NAME = "pymagnetos"
OUT_FORMAT = (".txt", ".csv", ".tsv", ".out")
LOG_LEVEL = "INFO"
VERSION = importlib.metadata.version(PROGRAM_NAME)


class MainWindow(BaseMainWindow):
    """
    A graphical user interface application for TDO analysis.

    The `MainWindow` class defines the main thread with the front-end user interface.

    It is built with the custom components defined in the `widgets` module. Those
    components are referenced in the main thread with a leading `w` :
    `self.wconfiguration` : the "Configuration" tab
    `self.wfiles` : the "Files" tab
    `self.wbatch` : the "Batch processing" tab
    `self.wgraphs` : the widget holding all the graphs
    `self.wbuttons` : the widget holding the main buttons
    `self.wlog` : the widget that streams the log output
    """

    sig_worker_extract = pyqtSignal()
    sig_worker_offset = pyqtSignal()
    sig_worker_analyse = pyqtSignal()
    sig_worker_tdocsv = pyqtSignal(str)
    sig_worker_rescsv = pyqtSignal(str)
    sig_worker_loadcsv = pyqtSignal(str)

    def __init__(self):
        # Register the widgets
        self._type_wbatch = BatchProcessingWidget
        self._type_wbuttons = widgets.ButtonsWidget
        self._type_wconfiguration = widgets.ConfigurationWidget
        self._type_wfiles = FileBrowserWidget
        self._type_wgraphs = widgets.GraphsWidget
        self._param_content = widgets.ParamContent
        self._type_worker = DataWorker

        super().__init__()

        # Initialize window
        self.setGeometry(300, 300, 900, 450)
        self.setWindowTitle("TDO Analyzer")

        self.logger.info(f"Running pytdo v{VERSION}")

    def init_parameter_tree(self):
        """Create the ParameterTree."""
        super().init_parameter_tree()

        # Connect
        self.wconfiguration.sig_syncroi_changed.connect(self.syncroi_changed)
        self.wconfiguration.sig_spectro_nperseg_changed.connect(
            self.update_spectro_time_window
        )
        self.wconfiguration.sig_timeoffset_changed.connect(self.apply_time_offset)
        self.wconfiguration.sig_fitdeg_changed.connect(self.analyse)
        self.wconfiguration.sig_npoints_interp_changed.connect(self.analyse)
        self.wconfiguration.sig_curveoffset_changed.connect(self.plot_tdo_detrended)

    def init_buttons(self):
        """Create the main buttons."""
        super().init_buttons()

        # Connect
        self.wbuttons.sig_extract.connect(self.extract_tdo)
        self.wbuttons.sig_analyse.connect(self.analyse)
        self.wbuttons.sig_tdocsv.connect(self.save_tdo_csv)
        self.wbuttons.sig_rescsv.connect(self.save_results_csv)

    def init_plots(self):
        """Create the graphs area."""
        super().init_plots()

        # Connect ROIs
        self.wgraphs.sig_roi1_changed.connect(self.roi1_changed)
        self.wgraphs.sig_roi2_changed.connect(self.roi2_changed)
        self.wconfiguration.settings_parameters.child(
            "poly_window"
        ).sigValueChanged.connect(self.update_roi_from_poly)
        self.wconfiguration.settings_parameters.child(
            "fft_window"
        ).sigValueChanged.connect(self.update_roi_from_fft)

    def init_log(self):
        """Setup logging."""
        super()._init_log(PROGRAM_NAME, log_level=LOG_LEVEL)

    def connect_worker(self):
        """Connect signals to the worker slots."""
        super().connect_worker()

        # Extract signal
        self.sig_worker_extract.connect(self.worker.extract_tdo)
        self.worker.sig_extract_finished.connect(self.extract_tdo_finished)

        # Time offset
        self.sig_worker_offset.connect(self.worker.time_offset)
        self.worker.sig_offset_finished.connect(self.time_offset_finished)

        # Field aligned
        self.worker.sig_align_finished.connect(self.align_field_finished)

        # Analysis
        self.sig_worker_analyse.connect(self.worker.analyse)
        self.worker.sig_analyse_finished.connect(self.analyse_finished)

        # Save TDO signal as CSV
        self.sig_worker_tdocsv.connect(self.worker.save_tdo_csv)
        self.worker.sig_tdocsv_finished.connect(self.save_tdo_csv_finished)

        # Save results as CSV
        self.sig_worker_rescsv.connect(self.worker.save_results_csv)
        self.worker.sig_rescsv_finished.connect(self.save_results_csv_finished)

        # Load from CSV
        self.sig_worker_loadcsv.connect(self.worker.load_csv_file)
        self.worker.sig_load_csv_finished.connect(self.load_csv_file_finished)

    @pyqtSlot()
    def extract_tdo(self):
        """Extract TDO signal."""
        if not self.check_data_loaded():
            return
        self.disable_buttons()
        self.sig_worker_extract.emit()

    @pyqtSlot()
    def align_field_finished(self):
        """Plot the magnetic field."""
        self.plot_field()
        self.ind_bup = self.worker.proc.inds_inc
        self.ind_bdown = self.worker.proc.inds_dec

    @pyqtSlot()
    def extract_tdo_finished(self):
        """Plot the TDO signal."""
        # Clear plots since source signal was changed
        self.wgraphs.tdo_field.clearPlots()
        self.wgraphs.tdo_inverse_field.clearPlots()
        self.wgraphs.fft.clearPlots()

        self.align_field_finished()
        self.plot_tdo()
        self.enable_buttons()

    @pyqtSlot()
    def apply_time_offset(self):
        """Apply an offset between the pickup and the signal time bases."""
        if not self.check_data_loaded():
            return
        self.disable_buttons()
        self.sig_worker_offset.emit()

    @pyqtSlot()
    def time_offset_finished(self):
        """Re-plot signals after applying the offset."""
        self.align_field_finished()
        self.plot_tdo()
        self.wgraphs.tdo_field.clearPlots()
        self.wgraphs.tdo_inverse_field.clearPlots()
        self.wgraphs.fft.clearPlots()
        self.analyse()

    @pyqtSlot()
    def analyse(self):
        """Fit, detrend, oversample in 1/B and compute the FFT."""
        if not self.check_tdo_extracted():
            self.logger.warning("[GUI] TDO signal was not extracted.")
            return
        self.disable_buttons()
        self.sig_worker_analyse.emit()

    @pyqtSlot()
    def analyse_finished(self):
        """Plot the detrended signals and the FFT after analysis."""
        self.wgraphs.fft.clearPlots()
        self.plot_tdo_detrended()
        self.plot_fft()
        self.enable_buttons()

    @pyqtSlot()
    def save_tdo_csv(self):
        """Save extracted TDO signal as CSV."""
        if not self.check_data_loaded():
            return

        self.disable_buttons()

        default_fname = self.worker.proc.get_csv_filename(suffix="-tdo")
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save TDO signals as...",
            default_fname,
            "Text files (*.txt, *.csv, *.tsv, *.out)",
        )

        if fname:
            self.sig_worker_tdocsv.emit(fname)
        else:
            self.logger.error("[GUI] Invalid output file name for CSV file.")
            self.save_tdo_csv_finished()

    @pyqtSlot()
    def save_tdo_csv_finished(self):
        """Re-enable buttons."""
        self.enable_buttons()

    @pyqtSlot()
    def save_results_csv(self):
        """Save final results as CSV."""
        if not self.check_data_loaded():
            return

        self.disable_buttons()

        default_fname = self.worker.proc.get_csv_filename(suffix="-results")
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save TDO signals as...",
            default_fname,
            "Text files (*.txt, *.csv, *.tsv)",
        )

        if fname:
            self.sig_worker_rescsv.emit(fname)
        else:
            self.logger.error("[GUI] Invalid output file name for CSV file.")
            self.save_tdo_csv_finished()

    @pyqtSlot()
    def save_results_csv_finished(self):
        """Re-enable buttons."""
        self.enable_buttons()

    def load_csv_file(self, file_path: str):
        """Load a CSV file."""
        if not self.check_config_loaded():
            self.logger.error(
                "Can't load a CSV file without loading a configuration file first."
            )
            return

        self.disable_buttons()
        self.sig_worker_loadcsv.emit(file_path)

    @pyqtSlot()
    def load_csv_file_finished(self):
        """Trigger action as if the TDO signal was extracted (but it was loaded)."""
        self.extract_tdo_finished()
        self.analyse_finished()

    @pyqtSlot()
    def batch_process(self):
        """Required for compatibility with the base app, but it is not implemented."""
        self.logger.warning("Not implemented.")

    @pyqtSlot()
    def roi1_changed(self):
        """Trigger analysis when the ROI from the TDO signal moved."""
        # Get time range
        xmin, xmax = self.wgraphs.roi.getRegion()

        # Check the ROI was changed since it was created
        if (xmin, xmax) == (0, 1):
            return

        # Update parameter in the tree if the region was changed from the graph
        if self.flag_do_update_roi:
            self.flag_do_update_roi = False
            self.wconfiguration.settings_parameters["poly_window"] = (
                self.wconfiguration.get_numbers_from_text([xmin, xmax])
            )
            self.flag_do_update_roi = True

        self.analyse()

    @pyqtSlot()
    def roi2_changed(self):
        """Trigger analysis when the ROI from the TDO detrended moved."""
        # Get time range
        xmin, xmax = self.wgraphs.roi2.getRegion()

        # Check the ROI was changed since it was created
        if (xmin, xmax) == (0, 1):
            return

        # Update parameter in the tree if the region was changed from the graph
        if self.flag_do_update_roi:
            self.flag_do_update_roi = False
            self.wconfiguration.settings_parameters["fft_window"] = (
                self.wconfiguration.get_numbers_from_text([xmin, xmax])
            )
            self.flag_do_update_roi = True

        self.analyse()

    @pyqtSlot()
    def update_roi_from_poly(self):
        """
        Update the ROI in the graph from "Fit: field window" in the parameter tree.

        Use `flag_do_update_roi` to check if the change is done programatically or from
        the user.
        In the first case, this function is ignored.
        In the second case, the ROI in the graph is updated and computation is
        triggered.
        """
        if self.flag_do_update_roi:
            # ROI changed from the tree, update the ROI in the graph
            new_region = self.wconfiguration.get_numbers_from_text(
                self.wconfiguration.settings_parameters["poly_window"]
            )
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

    @pyqtSlot()
    def update_roi_from_fft(self):
        """
        Update the ROI in the graph from "FFT: field window" in the parameter tree.

        Use `flag_do_update_roi` to check if the change is done programatically or from
        the user.
        In the first case, this function is ignored.
        In the second case, the ROI in the graph is updated and computation is
        triggered.
        """
        if self.flag_do_update_roi:
            # ROI changed from the tree, update the ROI in the graph
            new_region = self.wconfiguration.get_numbers_from_text(
                self.wconfiguration.settings_parameters["fft_window"]
            )
            if len(new_region) != 2:
                self.logger.error(f"[GUI] Invalid analysis window : {new_region}")
                return
            elif new_region[0] >= new_region[1]:
                self.logger.error(f"[GUI] Invalid analysis window : {new_region}")
                return

            # Update ROI, without recomputing
            self.flag_do_update_roi = False
            self.wgraphs.roi2.setRegion(new_region)
            self.flag_do_update_roi = True
        else:
            return

    def plot_tdo(self):
        """Plot TDO signal versus field and time."""
        if not self.check_field_aligned():
            self.worker.align_field()

        ## TDO signal versus field
        self.wgraphs.sig_field.clearPlots()

        # Decreasing magnetic field
        self.wgraphs.sig_field.plot(
            self.worker.proc.get_data_processed("magfield")[self.ind_bdown],
            self.worker.proc.get_data_processed(self.worker.proc._tdo_name)[
                self.ind_bdown
            ],
            pen=self.wgraphs.pen_bdown,
            name="B down",
        )
        # Increasing magnetic field
        self.wgraphs.sig_field.plot(
            self.worker.proc.get_data_processed("magfield")[self.ind_bup],
            self.worker.proc.get_data_processed(self.worker.proc._tdo_name)[
                self.ind_bup
            ],
            pen=self.wgraphs.pen_bup,
            name="B up",
        )

        ## TDO signal versus time
        self.wgraphs.sig_time.clearPlots()

        # Decreasing magnetic field
        self.wgraphs.sig_time.plot(
            self.worker.proc.get_data_processed("time_exp")[self.ind_bdown],
            self.worker.proc.get_data_processed(self.worker.proc._tdo_name)[
                self.ind_bdown
            ],
            pen=self.wgraphs.pen_bdown,
            name="B down",
        )
        # Increasing magnetic field
        self.wgraphs.sig_time.plot(
            self.worker.proc.get_data_processed("time_exp")[self.ind_bup],
            self.worker.proc.get_data_processed(self.worker.proc._tdo_name)[
                self.ind_bup
            ],
            pen=self.wgraphs.pen_bup,
            name="B up",
        )

    @pyqtSlot()
    def plot_tdo_detrended(self):
        """Plot TDO signal with background removed."""
        if not self.check_tdo_detrended():
            return
        # Get parameters
        offset = self.worker.proc.cfg.settings.offset
        lower_b, upper_b = self.worker.proc.cfg.settings.fft_window

        # Sync fit and FFT windows
        if lower_b == -1:
            lower_b = self.worker.proc.cfg.settings.poly_window[0]
        if upper_b == -1:
            upper_b = self.worker.proc.cfg.settings.poly_window[1]

        ## TDO detrended versus field
        self.wgraphs.tdo_field.clearPlots()
        self.wgraphs.sig_field.clearPlots()
        self.plot_tdo()  # to make sure data shown is synced

        # Decreasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_det_dec_name, checkonly=True
        ):
            self.wgraphs.tdo_field.plot(
                self.worker.proc.get_data_processed("magfield")[self.ind_bdown],
                self.worker.proc.get_data_processed(self.worker.proc._tdo_det_dec_name)
                - offset / 2,
                pen=self.wgraphs.pen_bdown,
                name="B down",
            )
        # Increasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_det_inc_name, checkonly=True
        ):
            self.wgraphs.tdo_field.plot(
                self.worker.proc.get_data_processed("magfield")[self.ind_bup],
                self.worker.proc.get_data_processed(self.worker.proc._tdo_det_inc_name)
                + offset / 2,
                pen=self.wgraphs.pen_bup,
                name="B up",
            )

        # Fit decreasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_name + "_fit_dec", checkonly=True
        ):
            self.wgraphs.sig_field.plot(
                self.worker.proc.get_data_processed("magfield")[self.ind_bdown],
                self.worker.proc.get_data_processed(
                    self.worker.proc._tdo_name + "_fit_dec"
                ),
                pen=self.wgraphs.pen_fitdown,
                name="Fit B down",
            )
        # Fit increasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_name + "_fit_inc", checkonly=True
        ):
            self.wgraphs.sig_field.plot(
                self.worker.proc.get_data_processed("magfield")[self.ind_bup],
                self.worker.proc.get_data_processed(
                    self.worker.proc._tdo_name + "_fit_inc"
                ),
                pen=self.wgraphs.pen_fitbup,
                name="Fit B up",
            )

        ## TDO detrended versus 1/B
        self.wgraphs.tdo_inverse_field.clearPlots()

        # Plot the whole non-interpolated signal
        # Increasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_det_inc_name, checkonly=True
        ):
            self.wgraphs.tdo_inverse_field.plot(
                1 / self.worker.proc.get_data_processed("magfield")[self.ind_bup],
                self.worker.proc.get_data_processed(self.worker.proc._tdo_det_inc_name)
                + offset / 2,
                pen=self.wgraphs.pen_tdo,
            )
        # Decreasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_det_dec_name, checkonly=True
        ):
            self.wgraphs.tdo_inverse_field.plot(
                1 / self.worker.proc.get_data_processed("magfield")[self.ind_bdown],
                self.worker.proc.get_data_processed(self.worker.proc._tdo_det_dec_name)
                - offset / 2,
                pen=self.wgraphs.pen_tdo,
            )

        # Now, the oversampled signal
        # Decreasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_inv_dec_name, checkonly=True
        ):
            p0 = self.wgraphs.tdo_inverse_field.plot(
                self.worker.proc.get_data_processed("magfield_inverse_dec"),
                self.worker.proc.get_data_processed(self.worker.proc._tdo_inv_dec_name)
                - offset / 2,
                pen=self.wgraphs.pen_bdown,
                name="B down",
            )
        # Increasing magnetic field
        if self.worker.proc.get_data_processed(
            self.worker.proc._tdo_inv_inc_name, checkonly=True
        ):
            p1 = self.wgraphs.tdo_inverse_field.plot(
                self.worker.proc.get_data_processed("magfield_inverse_inc"),
                self.worker.proc.get_data_processed(self.worker.proc._tdo_inv_inc_name)
                + offset / 2,
                pen=self.wgraphs.pen_bup,
                name="B up",
            )
        # Adjust limits
        self.wgraphs.tdo_inverse_field.getViewBox().autoRange(
            padding=0.1, items=[p0, p1]
        )

    def plot_fft(self):
        """Plot FFT in 1/B."""
        self.wgraphs.fft.clearPlots()

        # Decreasing magnetic field
        if self.worker.proc.get_data_processed("fft_dec", checkonly=True):
            self.wgraphs.fft.plot(
                self.worker.proc.get_data_processed("bfreq_dec"),
                self.worker.proc.get_data_processed("fft_dec"),
                pen=self.wgraphs.pen_bdown,
                name="B down",
            )
        # Increasing magnetic field
        if self.worker.proc.get_data_processed("fft_inc", checkonly=True):
            self.wgraphs.fft.plot(
                self.worker.proc.get_data_processed("bfreq_inc"),
                self.worker.proc.get_data_processed("fft_inc"),
                pen=self.wgraphs.pen_bup,
                name="B up",
            )

    @pyqtSlot()
    def syncroi_changed(self):
        """Update fit and FFT windows sync. status."""
        self.wgraphs._sync_roi = self.wconfiguration.syncroi_parameter.value()

    @pyqtSlot()
    def update_spectro_time_window(self):
        """Update the spectro. nperseg setting expressed in time."""
        if not self.check_data_loaded():
            return
        if "fs_signal" not in self.worker.proc.metadata:
            return
        else:
            fs = self.worker.proc.metadata["fs_signal"]

        self.wconfiguration.host_parameters["spectro_time_window"] = (
            self.wconfiguration.settings_parameters["spectro_nperseg"] / fs
        )

    @pyqtSlot(bool, str)
    def select_file_in_browser(self, is_toml: bool, filepath: str):
        """
        Select a file and set it as a configuration file or a new experiment ID.

        Callback for when the user double-click on a file in the "Files" tab.
        """
        if filepath.endswith(".csv"):
            self.load_csv_file(filepath)
        else:
            super().select_file_in_browser(is_toml, filepath)

    def check_tdo_extracted(self) -> bool:
        """Check if the TDO signal was extracted."""
        if not self.check_data_loaded():
            return False
        return self.worker.proc._check_barycenters_computed()

    def check_tdo_detrended(self) -> bool:
        """Check if the detrending was performed."""
        if not self.check_tdo_extracted():
            return False
        return self.worker.proc._check_tdo_detrended()

    def dropEvent(self, a0: QtGui.QDropEvent | None = None) -> None:
        """Load a file when it is dropped in the main window."""
        for url in a0.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(OUT_FORMAT):
                self.load_csv_file(file_path)
                return

        super().dropEvent(a0)
