"""A standalone progress bar window that emits its progress."""

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSlot


class PopupProgressBar(QtWidgets.QWidget):
    """Pop-up progress bar."""

    def __init__(self, min: int = 0, max: int = 100, title: str = ""):
        # Setup window
        super().__init__()
        self.pbar = QtWidgets.QProgressBar(self)
        self.pbar.setGeometry(30, 40, 500, 75)
        self.pbar.setMinimum(min)
        self.pbar.setMaximum(max)

        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.pbar)
        self.setLayout(vlayout)
        self.setGeometry(300, 300, 550, 100)
        self.setWindowTitle(title)

    def start_progress(self):
        self.show()

    @pyqtSlot(int)
    def update_progress(self, idx: int):
        self.pbar.setValue(idx + 1)
