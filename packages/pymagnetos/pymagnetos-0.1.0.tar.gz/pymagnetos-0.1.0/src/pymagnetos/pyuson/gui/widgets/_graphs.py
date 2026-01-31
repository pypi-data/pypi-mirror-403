"""The graph area widget for pyuson."""

import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

from pymagnetos.core.gui.widgets import BaseGraphsWidget


class GraphsWidget(BaseGraphsWidget):
    """
    The graphs area with all the plots.

    pyqtSignals
    -------
    sig_roi_changed : emits when the draggable time-window moved.
    """

    sig_roi_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        # Internal conversion factor from time to frames
        self._time2frame_scale = 1.0

        # Create empty canvases in tabs
        field_tab = self.create_field_plot()
        frame_tab = self.create_frame_plot()
        amplitude_tab = self.create_amplitude_plot()
        phase_tab = self.create_phase_plot()

        self.init_coordinates_on_hover()

        # Create a main splitter for rows (vertical)
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # Create a top splitter for the first row (horizontal)
        top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        top_splitter.addWidget(field_tab)
        top_splitter.addWidget(frame_tab)
        top_splitter.setStretchFactor(0, 1)  # field_tab stretch factor
        # frame_tab spans 3 columns
        top_splitter.setStretchFactor(1, 3)

        # Create a bottom splitter for the second row (horizontal)
        bottom_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(amplitude_tab)
        bottom_splitter.addWidget(phase_tab)
        # amplitude_tab spans 2 columns
        bottom_splitter.setStretchFactor(0, 2)
        # phase_tab spans 2 columns
        bottom_splitter.setStretchFactor(1, 2)

        # Add the top and bottom splitters to the main splitter
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setStretchFactor(0, 1)  # top row stretch factor
        main_splitter.setStretchFactor(1, 1)  # bottom row stretch factor

        # Set the main splitter as the central widget
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)

    @property
    def time2frame_scale(self) -> float:
        return self._time2frame_scale

    @time2frame_scale.setter
    def time2frame_scale(self, value: float) -> None:
        self._time2frame_scale = value
        self.field.getAxis("top").setScale(self.time2frame_scale)
        self.dfield.getAxis("top").setScale(self.time2frame_scale)

    def create_field_plot(self) -> QtWidgets.QTabWidget:
        tab = QtWidgets.QTabWidget(self)

        # magnetic field (integrated)
        self.field = pg.PlotWidget(title="Magnetic field")
        self.field.setLabel("bottom", "time (s)")
        self.field.setLabel("top", "frame (#) - field not aligned")
        self.field.setLabel("left", "field (T)")
        self.field.showGrid(y=True)
        self._plots_list.add(self.field)

        # pickup coil voltage (measured)
        self.dfield = pg.PlotWidget(title="Pickup")
        self.dfield.setLabel("bottom", "time (s)")
        self.dfield.setLabel("top", "frame (#)")
        self.dfield.setLabel("left", "pickup (V)")
        self.dfield.showGrid(y=True)
        self._plots_list.add(self.dfield)

        tab.addTab(self.field, "B(t)")
        tab.addTab(self.dfield, "Pickup")

        return tab

    def create_frame_plot(self) -> QtWidgets.QTabWidget:
        tab = QtWidgets.QTabWidget(self)

        # amplitude
        self.amp_frame = pg.PlotWidget(title="Frames amplitude")
        self.amp_frame.setLabel("bottom", "time (µs)")
        self.amp_frame.setLabel("left", "signal (V)")
        self.amp_frame.showGrid(y=True)
        self.roi = pg.LinearRegionItem()  # time range selector
        self.roi.sigRegionChangeFinished.connect(self.roi1_changed)
        self.roi.sigRegionChangeFinished.connect(self.sig_roi_changed.emit)
        self.amp_frame.addItem(self.roi, ignoreBounds=True)  # ty:ignore[unknown-argument]
        self._plots_list.add(self.amp_frame)

        # phases
        self.phase_frame = pg.PlotWidget(title="Frames phase")
        self.phase_frame.setLabel("bottom", "time (µs)")
        self.phase_frame.setLabel("left", "signal (V)")
        self.phase_frame.showGrid(y=True)
        self.roi2 = pg.LinearRegionItem()  # twin in phase plot
        self.phase_frame.addItem(self.roi2, ignoreBounds=True)  # ty:ignore[unknown-argument]
        self.roi2.sigRegionChangeFinished.connect(self.roi2_changed)
        self.phase_frame.getPlotItem().addLegend()
        self._plots_list.add(self.phase_frame)

        tab.addTab(self.amp_frame, "Frame amplitude")
        tab.addTab(self.phase_frame, "Frame phase")

        # Keep a reference to it to add more plots if needed
        self.tab_frame_plot = tab

        return tab

    def add_reference_in_frame_tab(self) -> None:
        """Add a plot for the reference signal for digital demodulation."""
        if hasattr(self, "reference_frame") and isinstance(
            self.reference_frame, pg.PlotWidget
        ):
            # Already has a reference frame plot
            return
        self.reference_frame = pg.PlotWidget(title="Frames reference")
        self.reference_frame.setLabel("bottom", "time (µs)")
        self.reference_frame.setLabel("left", "signal (V)")
        self.reference_frame.showGrid(y=True)
        self._plots_list.add(self.reference_frame)
        self.coordinates_on_hover(self.reference_frame)

        self.tab_frame_plot.addTab(self.reference_frame, "Frame reference")

    def create_amplitude_plot(self) -> QtWidgets.QTabWidget:
        tab = QtWidgets.QTabWidget(self)

        # vs field
        self.amp_field = pg.PlotWidget(title="Amplitude (B)")
        self.amp_field.setLabel("bottom", "field (T)")
        self.amp_field.setLabel("left", "attenuation (dB/cm)")
        self.amp_field.showGrid(y=True)
        self.amp_field.getPlotItem().addLegend()
        self._plots_list.add(self.amp_field)

        # vs amplitude
        self.amp_time = pg.PlotWidget(title="Amplitude (t)")
        self.amp_time.setLabel("bottom", "time (s)")
        self.amp_time.setLabel("left", "attenuation (dB/cm)")
        self.amp_time.showGrid(y=True)
        self._plots_list.add(self.amp_time)

        tab.addTab(self.amp_field, "Amplitude (B)")
        tab.addTab(self.amp_time, "Amplitude (t)")

        return tab

    def create_phase_plot(self) -> QtWidgets.QTabWidget:
        tab = QtWidgets.QTabWidget(self)

        # vs field
        self.phase_field = pg.PlotWidget(title="Phase (B)")
        self.phase_field.setLabel("bottom", "field (T)")
        self.phase_field.setLabel("left", "dphi/phi")
        self.phase_field.showGrid(y=True)
        self.phase_field.getPlotItem().addLegend()
        self._plots_list.add(self.phase_field)

        # vs plot
        self.phase_time = pg.PlotWidget(title="Phase (t)")
        self.phase_time.setLabel("bottom", "time (s)")
        self.phase_time.setLabel("left", "dphi/phi")
        self.phase_time.showGrid(y=True)
        self._plots_list.add(self.phase_time)

        tab.addTab(self.phase_field, "Phase (B)")
        tab.addTab(self.phase_time, "Phase (t)")

        return tab

    def init_plot_style(self) -> None:
        """Set up PyQtGraph line styles."""
        w0 = 1
        w1 = 1
        self.pen_field = pg.mkPen("#c7c7c7", width=w0)
        self.pen_amp = pg.mkPen("#1f77b480", width=w0)
        self.pen_amp_demod = pg.mkPen("#d6272880", width=w0)
        self.pen_in_phase = pg.mkPen("#ff7f0e80", width=w1)
        self.pen_out_phase = pg.mkPen("#17becf80", width=w1)
        self.pen_phase_demod = pg.mkPen("#9467bd80", width=w0)
        self.pen_bup = pg.mkPen("#2ca02cbf", width=w0)
        self.pen_bdown = pg.mkPen("#d62728bf", width=w0)

    def init_field_crosshair(self) -> None:
        """Create line cursor on field plot that tracks frame number."""
        self.field_vline = pg.InfiniteLine(angle=90, movable=False)
        self.field.addItem(self.field_vline, ignoreBounds=True)  # ty:ignore[unknown-argument]
        self.field.scene().sigMouseMoved.connect(self.field_crosshair_moved)  # ty:ignore[possibly-missing-attribute]

    def field_crosshair_moved(self, evt) -> None:
        """Define the callback function when the cursor is moved."""
        pos = evt
        vb = self.field.getViewBox()
        if self.field.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            index = int(mouse_point.x() * self.time2frame_scale)
            self.field.setLabel("top", f"frame (#), current : {index}")
            self.field_vline.setPos(mouse_point.x())

    @pyqtSlot()
    def roi1_changed(self) -> None:
        """Update ROI in the phase panel when the ROI in the amplitude panel moved."""
        roi1 = self.roi.getRegion()  # amplitude panel
        roi2 = self.roi2.getRegion()  # phase panel
        if roi1 != roi2:
            self.roi2.setRegion(self.roi.getRegion())

    @pyqtSlot()
    def roi2_changed(self) -> None:
        """Update ROI in the amplitude panel when the ROI in the phase panel moved."""
        roi1 = self.roi.getRegion()  # amplitude panel
        roi2 = self.roi2.getRegion()  # phase panel
        if roi1 != roi2:
            self.roi.setRegion(self.roi2.getRegion())

    def enable_rois(self) -> None:
        """Enable moving ROIs."""
        self.roi.setMovable(True)
        self.roi2.setMovable(True)

    def disable_rois(self) -> None:
        """Disable moving ROIs."""
        self.roi.setMovable(False)
        self.roi2.setMovable(False)
