"""
The graphs area that holds all the plots.

The plots themselves should be placed on a custom layout by subclass. This Base class
merely provides plots behavior :
- mouse coordinates on hover,
- CRTL+click to zoom in an area.
"""

from functools import partial

import pyqtgraph as pg
from PyQt6 import QtWidgets
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent


class BaseGraphsWidget(QtWidgets.QWidget):
    """Base class for the graphs area with all the plots."""

    _plots_list: set[pg.PlotWidget]

    def __init__(self) -> None:
        super().__init__()

        # Internal flags
        self._mouse_pan_mode = True

        # Registered plots
        self._plots_list = set()

        # Get pens
        self.init_plot_style()

    def init_plot_style(self) -> None:
        """Set and store QPen for styling of curves and ROIs."""
        raise NotImplementedError("Subclass must implement this method.")

    def event(self, ev: QEvent) -> bool:
        """Handle mouse selection while holding CTRL to make a ROI zoom in plots."""
        # Switch to rectangular zoom selection on the first Ctrl key press event
        if ev.type() == QKeyEvent.Type.KeyPress and ev.key() == Qt.Key.Key_Control:
            if self._mouse_pan_mode:
                self.switch_mouse_pan_mode(False)

        # Switch back to pan mode on left click when releasing the Ctrl key
        if ev.type() == QKeyEvent.Type.KeyRelease and ev.key() == Qt.Key.Key_Control:
            self.switch_mouse_pan_mode(True)

        return super().event(ev)

    def switch_mouse_pan_mode(self, state: bool) -> None:
        """
        Switch mouse behavior from panning to ROI-zooming when holding CTRL.

        Parameters
        ----------
        state : bool
            If True, all plots are set to pan mode, otherwise they are set in ROI-zoom
            mode.
        """
        # Get mode
        mode = pg.ViewBox.PanMode if state else pg.ViewBox.RectMode
        self._mouse_pan_mode = state

        # Set mode for all registered plots
        for plot in self._plots_list:
            plot.getPlotItem().getViewBox().setMouseMode(mode)

    def init_coordinates_on_hover(self) -> None:
        """Add x, y coordinates on mouse hover for all registered plots."""
        for plot in self._plots_list:
            self.coordinates_on_hover(plot)

    def coordinates_on_hover(self, plot) -> None:
        """Add x, y coordinates on mouse hover."""
        plot.scene().sigMouseMoved.connect(partial(self.mouse_moved_in_plot, plot))
        plot.setLabel("top", "x=, y=")
        plot.getAxis("top").setStyle(showValues=False)

    def mouse_moved_in_plot(self, plot, evt) -> None:
        """Define what happens when the mouse moves within a plot."""
        pos = evt
        if plot.getPlotItem().sceneBoundingRect().contains(pos):
            vb = plot.getPlotItem().getViewBox()
            mouse_point = vb.mapSceneToView(pos)
            label_text = f"x={mouse_point.x():0.6f}, y={mouse_point.y():0.6f}"
            plot.setLabel("top", label_text)

    def clear_all_plots(self) -> None:
        """Clear plots."""
        for plot in self._plots_list:
            plot.clearPlots()
