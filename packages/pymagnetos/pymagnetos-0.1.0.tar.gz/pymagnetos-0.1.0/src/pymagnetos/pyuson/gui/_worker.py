"""Worker that connects to an EchoProcessor object."""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from pymagnetos.pyuson import EchoProcessor


class ProcessorWorker(QObject):
    """
    Wrapper around the EchoProcessor class.

    It exposes the EchoProcessor methods as slots and emits a signal when the task is
    finished.

    pyqtSignals
    -------
    sig_load_finished : emits when loading data is finished.
    sig_align_finished : emits when aligning magnetic field is finished.
    sig_rolling_finished : emits when rolling average is finished.
    sig_find_f0_finished : emits f0 when finding center frequency is finished.
    sig_demodulate_finished : emits when demodulation is finished.
    sig_average_finished : emits when averaging frames and computing is finished.
    sig_batch_finished : emits when batch-processing is finished.

    sig_export_csv_finished : emits when exporting as CSV is finished.
    sig_save_nexus_finished : emits when saving as NeXus file is finished.

    sig_demodulation_progress : emits step index during demodulation.
    sig_batch_process_progress : emits step index during batch-processing.
    """

    sig_load_finished = pyqtSignal()
    sig_align_finished = pyqtSignal()
    sig_rolling_finished = pyqtSignal()
    sig_find_f0_finished = pyqtSignal(float)
    sig_demodulate_finished = pyqtSignal()
    sig_average_finished = pyqtSignal(bool)
    sig_batch_finished = pyqtSignal()

    sig_export_csv_finished = pyqtSignal()
    sig_save_nexus_finished = pyqtSignal()

    sig_demodulation_progress = pyqtSignal(int)
    sig_batch_progress = pyqtSignal(int)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.proc = EchoProcessor(*args, **kwargs)
        if self.proc.is_nexus_file:
            # From file : data should already be loaded and ready to use
            self.is_dataloaded = True
        else:
            self.is_dataloaded = False

    @pyqtSlot()
    def load_data(self) -> None:
        """Load data."""
        self.proc.load_oscillo(scale=True)
        self.is_dataloaded = True
        self.proc.align_field()  # use the Processor method directly to not emit signal
        self.sig_load_finished.emit()

    @pyqtSlot()
    def rolling_average(self) -> None:
        """Apply moving average."""
        self.proc.rolling_average()
        self.sig_rolling_finished.emit()

    def align_field(self) -> None:
        """Align magnetic field on data."""
        self.proc.align_field()
        self.sig_align_finished.emit()

    @pyqtSlot()
    def find_f0(self) -> None:
        """Find F0."""
        self.proc.find_f0()
        self.sig_find_f0_finished.emit(self.proc.metadata["rf_frequency"])

    @pyqtSlot()
    def demodulate(self) -> None:
        """Apply digital demodulation."""
        self.proc.demodulate(progress_emitter=self.sig_demodulation_progress)
        self.sig_demodulate_finished.emit()

    @pyqtSlot()
    def average_frame(self) -> None:
        """Average in the time window, comptue attenuation and phase-shift."""
        self.proc.average_frame_range().compute_attenuation().compute_phase_shift()
        # Check it went fine
        if self.proc.is_averaged:
            self.sig_average_finished.emit(True)
        else:
            self.sig_average_finished.emit(False)

    @pyqtSlot(list, bool, bool, bool, bool)
    def batch_process(
        self,
        expids: list,
        rolling_average: bool,
        save_csv: bool,
        to_cm: bool,
        find_f0: bool,
    ) -> None:
        """Batch-process several datasets."""
        self.proc.batch_process(
            expids,
            rolling_average=rolling_average,
            save_csv=save_csv,
            save_csv_kwargs=dict(to_cm=to_cm),
            find_f0=find_f0,
            batch_progress_emitter=self.sig_batch_progress,
            demodulation_progress_emitter=self.sig_demodulation_progress,
        )

        # Emit signals
        self.sig_load_finished.emit()
        if self.proc.is_digital:
            self.sig_demodulate_finished.emit()
        self.sig_average_finished.emit(True)
        self.sig_batch_finished.emit()

    @pyqtSlot(str, bool)
    def export_as_csv(self, fname: str, to_cm: bool) -> None:
        """Export results as CSV."""
        self.proc.to_csv(fname=fname, to_cm=to_cm)
        self.sig_export_csv_finished.emit()

    @pyqtSlot(str)
    def save_as_nexus(self, fname: str | Path) -> None:
        """Save data as NeXus."""
        self.proc.save(filename=fname)
        self.sig_save_nexus_finished.emit()
