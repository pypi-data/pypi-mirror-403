"""The graphs area that holds all the plots."""

import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

from pymagnetos.core.gui.widgets import BaseGraphsWidget


class GraphsWidget(BaseGraphsWidget):
    """
    The graphs area with all the plots.

    There are two tabs, one with :
    - dB/dt
    - B(t)
    - TDO(t)
    - TDO(B)
    The other with :
    - B(t)
    - TDO(B)
    - TDO_detrended(B)
    - TDO_detrended(1/B)
    - FFT

    Since B(t) and TDO(B) are re-used, placeholders plots are created. They are replaced
    when the tab is selected.

    Signals
    -------
    sig_roi1_changed : emits when the draggable field-window moved in tdo(B).
    sig_roi2_changed : emits when the draggable field-window moved in tdo_detrend(B).
    """

    sig_roi1_changed = pyqtSignal()
    sig_roi2_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Flags
        self._sync_roi = False

        # Create layouts
        widget1 = self.create_first_tab()
        widget2 = self.create_second_tab()

        # Create the tabs
        tab = QtWidgets.QTabWidget(self)
        tab.addTab(widget1, "TDO")
        tab.addTab(widget2, "Oscillations")
        tab.currentChanged.connect(self.move_plots)  # replace placeholders

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(tab)
        self.setLayout(layout)

        # Apply axes style
        self.customize_axis()
        self.init_coordinates_on_hover()

    def create_first_tab(self) -> QtWidgets.QSplitter:
        """Create the tab with the magnetic field and TDO signal."""
        # Create the plots
        self.create_field_plot()
        self.create_signal_plot()

        # Create splitter for the top row
        self.tab1_top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.tab1_top_splitter.addWidget(self.dfield)
        self.tab1_top_splitter.addWidget(self.field)
        self.tab1_top_splitter.addWidget(self.sig_time)

        # Create splitter for the bottom row
        self.tab1_main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.tab1_main_splitter.addWidget(self.tab1_top_splitter)
        self.tab1_main_splitter.addWidget(self.sig_field)

        # Adjust ratios
        self.tab1_main_splitter.setStretchFactor(0, 1)
        self.tab1_main_splitter.setStretchFactor(1, 2)

        return self.tab1_main_splitter

    def create_second_tab(self) -> QtWidgets.QSplitter:
        """Create the tab with the detrended TDO signals and the FFT."""
        self.create_tdo_plot()
        self.create_fft_plot()

        # Create splitter for the top row
        self.tab2_top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        # Add the placeholders plots, they will be replaced when the tab is shown
        self.tab2_top_splitter.addWidget(self._v2field)
        self.tab2_top_splitter.addWidget(self._v2sig_field)

        # Create splitter for the bottom row
        bottom_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(self.tdo_field)
        bottom_splitter.addWidget(self.tdo_inverse_field)
        bottom_splitter.addWidget(self.fft)

        # Create main splitter
        self.tab2_main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.tab2_main_splitter.addWidget(self.tab2_top_splitter)
        self.tab2_main_splitter.addWidget(bottom_splitter)

        return self.tab2_main_splitter

    def create_field_plot(self) -> None:
        # magnetic field (integrated)
        self.field = pg.PlotWidget(title="Magnetic field")
        self.field.setLabel("bottom", "time (s)")
        self.field.setLabel("left", "field (T)")
        self.field.getAxis("left").enableAutoSIPrefix(False)
        self._plots_list.add(self.field)
        # magnetic field (placeholders)
        self._v1field = pg.PlotWidget(title="Magnetic field")
        self._v1field.setLabel("bottom", "time (s)")
        self._v1field.setLabel("left", "field (T)")
        self._v2field = pg.PlotWidget(title="Magnetic field")
        self._v2field.setLabel("bottom", "time (s)")
        self._v2field.setLabel("left", "field (T)")

        # pickup coil voltage (measured)
        self.dfield = pg.PlotWidget(title="Pickup")
        self.dfield.setLabel("bottom", "time (s)")
        self.dfield.setLabel("left", "pickup (V)")
        self._plots_list.add(self.dfield)

    def create_signal_plot(self):
        # TDO signal versus field
        self.sig_field = pg.PlotWidget(title="Signal versus field")
        self.sig_field.setLabel("bottom", "field (T)")
        self.sig_field.setLabel("left", "TDO frequency (Hz)")
        # Field-window selector
        self.roi = pg.LinearRegionItem(
            brush=pg.mkBrush("#0000ff1a"), pen=self.pen_fitbounds
        )
        # Disable mouse drag
        self.roi.hoverEvent = lambda *args, **kwargs: None  # ty:ignore[invalid-assignment]
        self.roi.mouseDragEvent = lambda *args, **kwargs: None  # ty:ignore[invalid-assignment]
        self.sig_field.addItem(self.roi, ignoreBounds=True)  # ty:ignore[unknown-argument]

        self.roi.sigRegionChangeFinished.connect(self.roi1_changed)
        self.sig_field.getPlotItem().addLegend()
        self._plots_list.add(self.sig_field)

        # TDO signal versus field (placeholders)
        self._v1sig_field = pg.PlotWidget(title="Signal versus field")
        self._v1sig_field.setLabel("bottom", "field (T)")
        self._v1sig_field.setLabel("left", "TDO frequency (Hz)")
        self._v2sig_field = pg.PlotWidget(title="Signal versus field")
        self._v2sig_field.setLabel("bottom", "field (T)")
        self._v2sig_field.setLabel("left", "TDO frequency (Hz)")

        # TDO signal versus time
        self.sig_time = pg.PlotWidget(title="Signal versus time")
        self.sig_time.setLabel("bottom", "time (s)")
        self.sig_time.setLabel("left", "TDO frequency (Hz)")
        self._plots_list.add(self.sig_time)

    def create_tdo_plot(self):
        # vs field
        self.tdo_field = pg.PlotWidget(title="Oscillatory part versus field")
        self.tdo_field.setLabel("bottom", "field (T)")
        self.tdo_field.setLabel("left", "TDO detrended")
        self.tdo_field.getPlotItem().addLegend()
        # Field-window selector for FFT range
        self.roi2 = pg.LinearRegionItem(
            brush=pg.mkBrush("#0000ff1a"), pen=self.pen_fftbounds
        )
        # Disable mouse drag
        self.roi2.hoverEvent = lambda *args, **kwargs: None  # ty:ignore[invalid-assignment]
        self.roi2.mouseDragEvent = lambda *args, **kwargs: None  # ty:ignore[invalid-assignment]

        self.tdo_field.addItem(self.roi2, ignoreBounds=True)  # ty:ignore[unknown-argument]
        self.roi2.sigRegionChangeFinished.connect(self.roi2_changed)

        # Vertical lines to show polynomial fit range
        self.fit_bounds1 = pg.InfiniteLine(pen=self.pen_fitbounds, movable=False)
        self.fit_bounds2 = pg.InfiniteLine(pen=self.pen_fitbounds, movable=False)
        self.tdo_field.addItem(self.fit_bounds1)
        self.tdo_field.addItem(self.fit_bounds2)
        self._plots_list.add(self.tdo_field)

        # vs 1/B
        self.tdo_inverse_field = pg.PlotWidget(title="Oscillatory part versus 1/B")
        self.tdo_inverse_field.setLabel("bottom", "1/B (T^-1)")
        self.tdo_inverse_field.setLabel("left", "TDO detrended")
        # Vertical lines to show FFT range
        self.fft_bounds1 = pg.InfiniteLine(pen=self.pen_fftbounds, movable=False)
        self.fft_bounds2 = pg.InfiniteLine(pen=self.pen_fftbounds, movable=False)
        self.tdo_inverse_field.addItem(self.fft_bounds1)
        self.tdo_inverse_field.addItem(self.fft_bounds2)
        self._plots_list.add(self.tdo_inverse_field)

    def create_fft_plot(self):
        # vs field
        self.fft = pg.PlotWidget(title="Fourier transform")
        self.fft.setLabel("bottom", "B-frequency (T)")
        self.fft.setLabel("left", "magnitude")
        self.fft.getPlotItem().addLegend()
        self._plots_list.add(self.fft)

    def customize_axis(self):
        """Set a right axis and show the grid, for all the plots."""
        for plot in self._plots_list:
            plot.showAxis("right")
            plot.getAxis("right").setTicks([])
            plot.showGrid(y=True)

    def init_plot_style(self):
        """Set up PyQtGraph line styles."""
        w0 = 1
        w1 = 2
        self.pen_field = pg.mkPen("#c7c7c7", width=w0)
        self.pen_bup = pg.mkPen("#2ca02cff", width=w0)
        self.pen_bdown = pg.mkPen("#d62728ff", width=w0)
        self.pen_tdo = pg.mkPen("#fffc5c80", width=w0)
        self.pen_fitbup = pg.mkPen("#2ca02cb1", width=w0)
        self.pen_fitdown = pg.mkPen("#d62728b1", width=w0)
        self.pen_fitbounds = pg.mkPen("#7477ed99", width=w1)
        self.pen_fftbounds = pg.mkPen("#eddd86ff", width=w1)

    @pyqtSlot()
    def roi1_changed(self):
        """Update ROI in the TDO detrended panel when the ROI in the TDO panel moved."""
        roi1 = self.roi.getRegion()  # TDO panel
        # Show the select fit range in the TDO detrended panel
        self.fit_bounds1.setPos(roi1[0])
        self.fit_bounds2.setPos(roi1[1])
        self.sig_roi1_changed.emit()
        if not self._sync_roi:
            return

        roi2 = self.roi2.getRegion()  # TDO detrend panel

        if roi1 != roi2:
            self.roi2.setRegion(self.roi.getRegion())

    @pyqtSlot()
    def roi2_changed(self):
        """Update ROI in the TDO panel when the ROI in the TDO detrended panel moved."""
        roi2 = self.roi2.getRegion()  # TDO detrend panel
        # Show the FFT range in the TDO 1/B panel
        self.fft_bounds1.setPos(1 / roi2[0])
        self.fft_bounds2.setPos(1 / roi2[1])
        self.sig_roi2_changed.emit()
        if not self._sync_roi:
            return

        roi1 = self.roi.getRegion()  # TDO panel

        if roi1 != roi2:
            self.roi.setRegion(self.roi2.getRegion())

    def enable_rois(self):
        """Enable moving ROIs."""
        self.roi.setMovable(True)
        self.roi2.setMovable(True)

    def disable_rois(self):
        """Disable moving ROIs."""
        self.roi.setMovable(False)
        self.roi2.setMovable(False)

    @pyqtSlot(int)
    def move_plots(self, index: int):
        """Move plots from one tab to another, because a widget can't be copied."""
        if index == 0:
            # First tab
            self.tab2_top_splitter.replaceWidget(0, self._v2field)
            self.tab2_top_splitter.replaceWidget(1, self._v2sig_field)
            self.tab1_top_splitter.replaceWidget(1, self.field)
            self.tab1_main_splitter.replaceWidget(1, self.sig_field)
        elif index == 1:
            # Second tab
            self.tab1_top_splitter.replaceWidget(1, self._v1field)
            self.tab1_main_splitter.replaceWidget(1, self._v1sig_field)
            self.tab2_top_splitter.replaceWidget(0, self.field)
            self.tab2_top_splitter.replaceWidget(1, self.sig_field)
