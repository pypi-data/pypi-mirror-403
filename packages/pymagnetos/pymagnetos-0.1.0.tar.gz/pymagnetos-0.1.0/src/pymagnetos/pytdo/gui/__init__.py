"""Application for TDO experiments during high-magnetic field."""

from PyQt6 import QtWidgets

from .main import MainWindow


def run(exec: bool = True) -> None | MainWindow:
    """
    Build and run the app.

    Set `exec=False` in an interactive prompt to interact with the GUI from the shell.

    Parameters
    ----------
    exec : bool, optional
        Execute the process thread. Set to False in an interactive prompt. Default is
        True.
    """
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    if exec:
        app.exec()
    else:
        return win