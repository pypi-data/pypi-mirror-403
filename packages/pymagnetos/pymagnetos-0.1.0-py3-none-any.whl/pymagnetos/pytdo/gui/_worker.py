"""Worker that connects to an TDOProcessor object."""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from pymagnetos.pytdo import TDOProcessor


class DataWorker(QObject):
    """
    Wrapper around the TDOProcessor class.

    It exposes the EchoProcessor methods as slots and emits a signal when the task is
    finished.

    Signals
    -------
    sig_load_finished : emits when loading data is finished.
    sig_extract_finished : emits when extracting the TDO signal is finished.
    sig_offset_finished : emits when the adjusting the pickup/signal offset is finished.
    sig_align_finished : emits when the magnetic field is aligned on the TDO signal.
    sig_analyse_finished : emits when the TDO signal is analysed (detrended and FFT in
        1/B).
    sig_tdocsv_finished : emits when the TDO signal is saved as CSV.
    sig_rescsv_finished : emits when the analysis is saved as CSV.
    sig_save_nexus_finished : emits when saving the NeXus file is finished.
    sig_load_csv_finished : emits when loading a CSV file is finished.
    """

    sig_load_finished = pyqtSignal()
    sig_extract_finished = pyqtSignal()
    sig_offset_finished = pyqtSignal()
    sig_align_finished = pyqtSignal()
    sig_analyse_finished = pyqtSignal()
    sig_batch_progress = pyqtSignal(int)  # required by upstream core.gui lib
    sig_batch_finished = pyqtSignal()  # required by upstream core.gui lib
    sig_tdocsv_finished = pyqtSignal()
    sig_rescsv_finished = pyqtSignal()
    sig_save_nexus_finished = pyqtSignal()
    sig_load_csv_finished = pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

        self.proc = TDOProcessor(*args, **kwargs)
        if self.proc.is_nexus_file:
            self.is_dataloaded = True
        else:
            self.is_dataloaded = False

    @pyqtSlot()
    def load_data(self):
        """Load data."""
        self.proc.load_oscillo()
        self.is_dataloaded = True
        self.sig_load_finished.emit()

    @pyqtSlot()
    def extract_tdo(self):
        """Extract TDO signal."""
        self.proc.extract_tdo()
        self.sig_extract_finished.emit()

    @pyqtSlot()
    def time_offset(self):
        """Apply time offset on experiment time vector."""
        self.proc.apply_time_offset()
        self.sig_offset_finished.emit()

    def align_field(self):
        self.proc.align_field()
        self.sig_align_finished.emit()

    @pyqtSlot()
    def analyse(self):
        """Remove background and oversample in 1/B."""
        self.proc.analyse()
        self.sig_analyse_finished.emit()

    @pyqtSlot()
    def batch_process(self):
        return

    @pyqtSlot(str)
    def save_tdo_csv(self, fname: str | Path):
        """Save TDO signal as CSV."""
        self.proc.save_tdo_csv(filename=fname)
        self.sig_tdocsv_finished.emit()

    @pyqtSlot(str)
    def save_results_csv(self, fname: str | Path):
        """Save results as CSV."""
        self.proc.save_results_csv(filename_prefix=fname)
        self.sig_rescsv_finished.emit()

    @pyqtSlot(str)
    def save_as_nexus(self, fname: str | Path):
        """Save data as NeXus."""
        self.proc.save(filename=fname)
        self.sig_save_nexus_finished.emit()

    @pyqtSlot(str)
    def load_csv_file(self, fname: str):
        self.proc.load_csv(fname)
        self.sig_load_csv_finished.emit()
