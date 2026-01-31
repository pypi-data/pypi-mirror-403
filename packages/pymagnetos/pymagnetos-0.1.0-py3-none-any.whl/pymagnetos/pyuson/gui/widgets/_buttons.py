"""The widget that hosts the grid with the main action buttons for pyuson."""

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal


class ButtonsWidget(QtWidgets.QWidget):
    """
    The main action buttons.

    pyqtSignals
    -------
    sig_load : emits when the "Load data" button is clicked.
    sig_show : emits when the "Show frames" button is clicked.
    sig_rolling : emits when the "Rolling average" button is clicked.
    sig_refresh : emits when the "Refresh" button is clicked.
    sig_save_csv : emits when the "Export as CSV" button is clicked.
    sig_save_nexus : emits when the "Save as NeXus" button is clicked.
    """

    sig_load = pyqtSignal()
    sig_show = pyqtSignal()
    sig_rolling = pyqtSignal()
    sig_refresh = pyqtSignal()
    sig_save_csv = pyqtSignal()
    sig_save_nexus = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        """Initialize buttons."""
        # Create grid
        grid = QtWidgets.QGridLayout()

        # Create buttons
        # Load data
        self.button_load = QtWidgets.QPushButton("Load data", self)
        # Show some frames
        self.button_show = QtWidgets.QPushButton("Show frames", self)
        # Apply moving mean filter
        self.button_rolling = QtWidgets.QPushButton("Rolling average", self)
        # Trigger computation of attenuation and phase shift
        self.button_refresh = QtWidgets.QPushButton("Refresh", self)
        # Export as CSV
        self.button_save_csv = QtWidgets.QPushButton("Export as CSV", self)
        # Checkbox to convert to dB/cm
        self.checkbox_to_cm = QtWidgets.QCheckBox("Convert to dB/cm in CSV", self)
        self.checkbox_to_cm.setChecked(True)

        # Save as NeXus
        self.button_save_nexus = QtWidgets.QPushButton("Save as NeXus", self)

        # Disable all buttons
        self.disable_buttons()

        # Connect them
        self.connect_buttons()

        # Add buttons to layout
        grid.addWidget(self.button_load, 0, 0)
        grid.addWidget(self.button_show, 0, 1)
        grid.addWidget(self.button_rolling, 1, 0)
        grid.addWidget(self.button_refresh, 1, 1)
        grid.addWidget(self.button_save_csv, 2, 0)
        grid.addWidget(self.button_save_nexus, 2, 1)
        grid.addWidget(self.checkbox_to_cm, 3, 0, Qt.AlignmentFlag.AlignHCenter)

        # Set widget layout
        self.setLayout(grid)

    def connect_buttons(self) -> None:
        """Connect the buttons to their signals."""
        self.button_load.clicked.connect(self.sig_load.emit)
        self.button_show.clicked.connect(self.sig_show.emit)
        self.button_rolling.clicked.connect(self.sig_rolling.emit)
        self.button_refresh.clicked.connect(self.sig_refresh.emit)
        self.button_save_csv.clicked.connect(self.sig_save_csv.emit)
        self.button_save_nexus.clicked.connect(self.sig_save_nexus.emit)

    def disable_buttons(self) -> None:
        """Disable all buttons."""
        self.button_load.setEnabled(False)
        self.button_rolling.setEnabled(False)
        self.button_show.setEnabled(False)
        self.button_refresh.setEnabled(False)
        self.button_save_csv.setEnabled(False)
        self.button_save_nexus.setEnabled(False)

    def enable_buttons(self) -> None:
        """Enable all buttons (except Load data)."""
        self.button_load.setEnabled(False)
        self.button_rolling.setEnabled(True)
        self.button_show.setEnabled(True)
        self.button_refresh.setEnabled(True)
        self.button_save_csv.setEnabled(True)
        self.button_save_nexus.setEnabled(True)
