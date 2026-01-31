"""The Configuration widget for pyuson."""

from functools import partial

from PyQt6.QtCore import pyqtSignal
from pyqtgraph.parametertree import Parameter

from pymagnetos.core.gui.widgets import BaseConfigurationWidget

from ._param_content import ParamContent


class ConfigurationWidget(BaseConfigurationWidget):
    """
    Initialize a PyQtGraph ParameterTree.

    pyqtSignals
    -------
    sig_echo_index_changed : emits when the echo index (in the Settings section ) is
        changed.
    sig_find_f0 : emits when the "Find f0" button is clicked.
    sig_demodulate : emits when the "Demodulate" button is clicked.
    """

    sig_echo_index_changed = pyqtSignal()
    sig_find_f0 = pyqtSignal()
    sig_demodulate = pyqtSignal()

    def __init__(self, param_content: type[ParamContent]) -> None:
        super().__init__(param_content)

    def init_demodulation_tree(self) -> None:
        """Create ParameterTree for demodulation parameters."""
        if not hasattr(self._param_content, "children_demodulation"):
            raise ValueError(
                "Could not add the demodulation parameter tree, not in digital mode"
            )
        self.demodulation_parameters = Parameter.create(
            name="Demodulation",
            type="group",
            children=self._param_content.children_demodulation,
        )
        self.host_parameters.addChild(self.demodulation_parameters)

        # Store buttons as the others
        self.button_findf0 = self.demodulation_parameters.child("find_f0")
        self.button_findf0.setOpts(enabled=False)
        self.button_demodulate = self.demodulation_parameters.child("demodulate")
        self.button_demodulate.setOpts(enabled=False)

        self.connect_to_signals_demodulation()

    def connect_to_signals(self) -> None:
        """Connect changes to signals."""
        super().connect_to_signals()

        # Special case for echo_index to sync it with another spinbox in the Batch
        # processing tab
        self.settings_parameters.child("echo_index").sigValueChanged.connect(
            self.sig_echo_index_changed.emit
        )

    def connect_to_signals_demodulation(self) -> None:
        """Additionnal connections for demodulation."""
        self.button_findf0.sigActivated.connect(self.sig_find_f0.emit)
        self.button_demodulate.sigActivated.connect(self.sig_demodulate.emit)

        for p in self.demodulation_parameters:
            self.demodulation_parameters.child(p.name()).sigValueChanged.connect(
                partial(self.sig_parameter_changed.emit, p.name(), "demodulation")
            )

    def enable_buttons(self) -> None:
        super().enable_buttons()
        if hasattr(self, "button_findf0"):
            self.button_findf0.setOpts(enabled=True)
        if hasattr(self, "button_demodulate"):
            self.button_demodulate.setOpts(enabled=True)

    def disable_buttons(self) -> None:
        super().disable_buttons()
        if hasattr(self, "button_findf0"):
            self.button_findf0.setOpts(enabled=False)
        if hasattr(self, "button_demodulate"):
            self.button_demodulate.setOpts(enabled=False)
