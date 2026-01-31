"""
A widget for batch-processing.

It includes a 3 lists of files:
- a "available" list,
- a "todo" list,
- a "done" list.
Items can be moved across the three lists. Text fields allow to filter available files.
Those lists are DropListWidget defined in this module.

Some buttons are still specific to the `pyuson` module, but it will be made more generic
in the future.
"""

import glob
import os
from pathlib import Path

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot


class DropListWidget(QtWidgets.QListWidget):
    """A list widget with drag & drop."""

    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSortingEnabled(True)

    def move_item_from_other(
        self, item: QtWidgets.QListWidgetItem, otherList: QtWidgets.QListWidget
    ):
        """Move `item` from `otherList` to this list."""
        if not self.findItems(item.text(), Qt.MatchFlag.MatchExactly):
            otherList.takeItem(otherList.indexFromItem(item).row())
            self.addItem(item)

    def add_selected_items_from_other(self, otherList: QtWidgets.QListWidget):
        """Take selected items from `otherList` list and add it to this list."""
        selectedItems = otherList.selectedItems()
        for item in selectedItems:
            self.move_item_from_other(item, otherList)

    def add_all_items_from_other(self, otherList: QtWidgets.QListWidget):
        """Take all items from `other` list and add it to this list."""
        while otherList.count() != 0:
            item = otherList.takeItem(0)
            if item is not None and (
                not self.findItems(item.text(), Qt.MatchFlag.MatchExactly)
            ):
                self.addItem(item)

    def get_list_of_items(self) -> list[str]:
        """Get the list of items as strings."""
        return [self.item(idx).text() for idx in range(self.count())]  # ty:ignore[possibly-missing-attribute]


class BatchProcessingWidget(QtWidgets.QWidget):
    """
    List widgets that can drag & drop items between each other.

    pyqtSignals
    -------
    sig_batch_process : emits when the "Batch process" is clicked.
    sig_echo_index_changed : emits when the echo index changed.
    """

    sig_batch_process = pyqtSignal()
    sig_echo_index_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._current_directory = ""

        layout = QtWidgets.QGridLayout()

        self.left_list = DropListWidget()
        self.right_list = DropListWidget()
        self.done_list = DropListWidget()
        self.wbuttons = self.init_buttons()

        left_list_title = QtWidgets.QLabel("Available files", self)
        left_list_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_list_title = QtWidgets.QLabel("Files to process", self)
        right_list_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        done_list_title = QtWidgets.QLabel("Processed files", self)

        readd_layout = QtWidgets.QHBoxLayout()
        readd_layout.addWidget(done_list_title, alignment=Qt.AlignmentFlag.AlignLeft)
        readd_layout.addWidget(
            self.init_readd_buttons(), alignment=Qt.AlignmentFlag.AlignRight
        )

        layout.addWidget(self.init_help_text(), 0, 0, 1, 2)
        layout.addWidget(self.init_edits_widgets(), 1, 0, 1, 2)
        layout.addWidget(left_list_title, 2, 0)
        layout.addWidget(self.left_list, 3, 0, 3, 1)
        layout.addWidget(right_list_title, 2, 1)
        layout.addWidget(self.right_list, 3, 1)
        layout.addLayout(readd_layout, 4, 1)
        layout.addWidget(self.done_list, 5, 1)
        layout.addWidget(self.wbuttons, 6, 0, 1, 2)

        self.setLayout(layout)

    @property
    def prefix(self) -> str:
        return self.line_prefix.text()

    @prefix.setter
    def prefix(self, value: str):
        self.line_prefix.setText(value)

    @property
    def suffix(self) -> str:
        return self.line_suffix.text()

    @suffix.setter
    def suffix(self, value: str):
        self.line_suffix.setText(value)

    @property
    def echo_index(self) -> int:
        return self.spinbox_echo_index.value()

    @echo_index.setter
    def echo_index(self, value: int):
        self.spinbox_echo_index.setValue(value)

    @property
    def current_directory(self) -> str:
        return self._current_directory

    @current_directory.setter
    def current_directory(self, value: str):
        self._current_directory = value
        self.list_files_in_dir()

    def init_help_text(self) -> QtWidgets.QLabel:
        """Set up the help string on top of the tab."""
        help_str = (
            "Drag & drop files from the left (right) to the right (left) to add"
            " (remove, respectively) files to the batch processor. Use the file name "
            "prefix and suffix to filter the available files. The 'Batch process' will "
            "process selected files with the same settings, including echo index."
        )

        help_widget = QtWidgets.QLabel(help_str, self)
        help_widget.setWordWrap(True)

        return help_widget

    def init_edits_widgets(self) -> QtWidgets.QWidget:
        """Set up editable fields to filter files."""
        prefix_label = QtWidgets.QLabel("Prefix", self)
        self.line_prefix = QtWidgets.QLineEdit("", self)
        self.line_prefix.textChanged.connect(self.list_files_in_dir)

        suffix_label = QtWidgets.QLabel("Suffix", self)
        self.line_suffix = QtWidgets.QLineEdit(".bin", self)  # TODO : generic default
        self.line_suffix.textChanged.connect(self.list_files_in_dir)

        # TODO : move to pyuson
        echo_index_label = QtWidgets.QLabel("Echo index", self)
        self.spinbox_echo_index = QtWidgets.QSpinBox()
        self.spinbox_echo_index.setValue(1)
        self.spinbox_echo_index.valueChanged.connect(self.sig_echo_index_changed)

        self.checkbox_save_as_csv = QtWidgets.QCheckBox("Save as CSV", self)
        self.checkbox_save_as_csv.setChecked(True)

        grid = QtWidgets.QHBoxLayout()
        grid.addWidget(prefix_label)
        grid.addWidget(self.line_prefix)
        grid.addWidget(suffix_label)
        grid.addWidget(self.line_suffix)
        grid.addWidget(echo_index_label)
        grid.addWidget(self.spinbox_echo_index)
        grid.addWidget(self.checkbox_save_as_csv)

        edits_widget = QtWidgets.QWidget(self)
        edits_widget.setLayout(grid)

        return edits_widget

    def init_buttons(self) -> QtWidgets.QWidget:
        """Set up buttons to manipulate lists."""
        self.button_add_selected = QtWidgets.QPushButton("Add selected", self)
        self.button_add_selected.clicked.connect(self.add_selected)

        self.button_add_all = QtWidgets.QPushButton("Add all", self)
        self.button_add_all.clicked.connect(self.add_all)

        self.button_clear_all = QtWidgets.QPushButton("Clear all", self)
        self.button_clear_all.clicked.connect(self.clear_all)

        self.button_run = QtWidgets.QPushButton("Batch process", self)
        self.button_run.clicked.connect(self.sig_batch_process.emit)

        # TODO : move to pyuson
        self.checkbox_rolling_average = QtWidgets.QCheckBox("Rolling average", self)

        self.buttons_grid = QtWidgets.QGridLayout()
        self.buttons_grid.addWidget(self.button_add_selected, 0, 0)
        self.buttons_grid.addWidget(self.button_add_all, 0, 1)
        self.buttons_grid.addWidget(self.button_clear_all, 0, 2)
        self.buttons_grid.addWidget(self.button_run, 0, 3, 1, 2)
        self.buttons_grid.addWidget(self.checkbox_rolling_average, 1, 3)

        buttons_widget = QtWidgets.QWidget(self)
        buttons_widget.setLayout(self.buttons_grid)

        return buttons_widget

    def add_findf0_checkbox(self) -> None:
        """Add a "Find f0" checkbox below the buttons."""
        # TODO : move to pyuson
        self.checkbox_find_f0 = QtWidgets.QCheckBox("Find f0", self)
        self.checkbox_find_f0.setChecked(True)
        self.buttons_grid.addWidget(self.checkbox_find_f0, 1, 4)
        self.wbuttons.setLayout(self.buttons_grid)

    def init_readd_buttons(self) -> QtWidgets.QWidget:
        """Set up buttons to read processed files back to the queue."""
        self.button_readd_all = QtWidgets.QPushButton("⇈", self)
        self.button_readd_all.clicked.connect(self.readd_all)

        self.button_readd_selected = QtWidgets.QPushButton("↑")
        self.button_readd_selected.clicked.connect(self.readd_selected)

        grid = QtWidgets.QHBoxLayout()
        grid.addWidget(self.button_readd_selected)
        grid.addWidget(self.button_readd_all)

        readd_widget = QtWidgets.QWidget()
        readd_widget.setLayout(grid)

        return readd_widget

    @pyqtSlot()
    def list_files_in_dir(self) -> None:
        """List files filtered with suffix and prefix."""
        directory = self.current_directory

        pattern = os.path.join(str(directory), self.prefix + "*" + self.suffix)
        new_items = [
            Path(filepath).name
            for filepath in glob.glob(pattern)
            if "-pickup" not in filepath
        ]

        self.left_list.clear()
        self.left_list.addItems(new_items)

    @pyqtSlot()
    def add_selected(self) -> None:
        """Add selected files in the left list to the right list."""
        self.right_list.add_selected_items_from_other(self.left_list)

    @pyqtSlot()
    def add_all(self) -> None:
        """Add all items in the left list to the right list."""
        self.right_list.add_all_items_from_other(self.left_list)

    @pyqtSlot()
    def readd_selected(self) -> None:
        """Add selected files in the done list to the right list."""
        self.right_list.add_selected_items_from_other(self.done_list)

    @pyqtSlot()
    def readd_all(self) -> None:
        """Add all files in the done list to the right list."""
        self.right_list.add_all_items_from_other(self.done_list)

    @pyqtSlot()
    def clear_all(self) -> None:
        """Remove all items from the right list and refresh the left list."""
        self.right_list.clear()
        self.list_files_in_dir()

    def move_to_done(self, file: str) -> None:
        """Move an item from the Files to process list to the Processed files list."""
        filename = Path(file).name
        item = self.right_list.findItems(filename, Qt.MatchFlag.MatchExactly)[0]
        self.done_list.move_item_from_other(item, self.right_list)

    def get_files_to_process(self) -> list[str]:
        """List full paths to the files to process."""
        names_list = self.right_list.get_list_of_items()
        return [os.path.join(self.current_directory, name) for name in names_list]

    def enable_buttons(self) -> None:
        """Enable all buttons."""
        self.button_add_selected.setEnabled(True)
        self.button_add_all.setEnabled(True)
        self.button_clear_all.setEnabled(True)
        self.button_readd_selected.setEnabled(True)
        self.button_readd_all.setEnabled(True)
        self.button_run.setEnabled(True)

    def disable_buttons(self) -> None:
        """Disable all buttons."""
        self.button_add_selected.setEnabled(False)
        self.button_add_all.setEnabled(False)
        self.button_clear_all.setEnabled(False)
        self.button_readd_selected.setEnabled(False)
        self.button_readd_all.setEnabled(False)
        self.button_run.setEnabled(False)
