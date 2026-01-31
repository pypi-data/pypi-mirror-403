"""
A simple file browser with a folder selection button and a checkbox.

Files can be selected, when they are, a signal is emitted.

This module includes the QTreeView itself (FileBrowser), and the host widget that adds
the folder selection button (FileBrowserWidget).
"""

from pathlib import Path

from PyQt6 import QtWidgets
from PyQt6.QtCore import QSortFilterProxyModel, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFileSystemModel


class FileBrowser(QtWidgets.QTreeView):
    """File browser and picker."""

    def __init__(self, startDir: str | Path = "") -> None:
        super().__init__()

        self.fsModel = QFileSystemModel()
        self.fsModel.setRootPath("")

        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.fsModel)

        self.setModel(self.proxyModel)

        start_dir = Path(startDir)
        if start_dir.is_file():
            start_dir = str(start_dir.parent)
        elif start_dir.is_dir():
            start_dir = str(start_dir)
        else:
            start_dir = ""

        index = self.fsModel.index(start_dir)
        proxyIndex = self.proxyModel.mapFromSource(index)
        self.setRootIndex(proxyIndex)

    def set_directory(self, dirname: str | Path) -> None:
        """Set the current folder in the tree view."""
        dirname = str(dirname)

        index = self.fsModel.index(dirname)
        proxyIndex = self.proxyModel.mapFromSource(index)
        self.setRootIndex(proxyIndex)

    def get_current_file(self) -> str:
        """Return the currently selected file."""
        index = self.currentIndex()
        sourceIndex = self.proxyModel.mapToSource(index)

        return self.fsModel.filePath(sourceIndex)


class FileBrowserWidget(QtWidgets.QWidget):
    """
    File browser and picker with a folder selection button and a checkbox.

    pyqtSignals
    -------
    sig_file_selected : emits when an item is double-clicked. Emits True if the file is
        a TOML file, False otherwise, and the file path.
    sig_checkbox_changed : emits when the checkbox is changed.
    """

    sig_file_selected = pyqtSignal(bool, str)
    sig_checkbox_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        # Build the push button
        self.button_open_folder = QtWidgets.QPushButton("Open Folder...", self)
        self.button_open_folder.clicked.connect(self.open_folder)

        # Build the load data checkbox
        self.checkbox_autoload_data = QtWidgets.QCheckBox(
            "Load data automatically", self
        )
        self.checkbox_autoload_data.setChecked(True)
        self.checkbox_autoload_data.stateChanged.connect(self.sig_checkbox_changed)

        # Build the file browser tree view
        self.file_browser = FileBrowser()
        self.file_browser.doubleClicked.connect(self.select_file)

        # Define layout
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.button_open_folder, 0, 0)
        grid.addWidget(self.checkbox_autoload_data, 0, 1)
        grid.addWidget(self.file_browser, 1, 0, -1, 2)

        # Create widget
        self.setLayout(grid)

    @pyqtSlot()
    def open_folder(self) -> None:
        """
        Open a folder picker.

        Callback for the "Open Folder" button in the file browser.
        """
        dirname = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open folder...",
        )
        if dirname:
            self.file_browser.set_directory(dirname)

    @pyqtSlot()
    def select_file(self) -> None:
        """
        Load the file selected in the file browser tab.

        Callback for when a file is double-clicked in the file browser tab.
        """
        filepath = self.file_browser.get_current_file()

        if filepath.endswith(".toml"):
            # This is a configuration file
            self.sig_file_selected.emit(True, filepath)
        else:
            # Not really sure but let's assume it is a data file used to change the
            # experiment ID
            self.sig_file_selected.emit(False, filepath)
