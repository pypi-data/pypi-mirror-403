from __future__ import annotations

from typing import Sequence

import numpy as np
import qtawesome
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.dialog.ColormapDialog import ColormapDialog
from silx.gui.plot import PlotWidget, actions
from silx.gui.plot.items import Scatter
from silx.gui.plot.tools import PositionInfo

from .axes_control_widget import AxisControlWidget

_UNFILTERED_PEAKS_LEGEND = "unfiltered"
_FILTERED_PEAKS_LEGEND = "filtered"


class _PeakFilterToolBar(qt.QToolBar):
    togglePeaks = qt.Signal(bool)

    def __init__(
        self,
        plot: PlotWidget,
        parent=None,
    ):
        super().__init__("Plot Tools", parent)

        self.setToolButtonStyle(qt.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        zoomAction = actions.mode.ZoomModeAction(parent=self, plot=plot)
        panAction = actions.mode.PanModeAction(parent=self, plot=plot)
        self.addAction(panAction)
        self.addAction(zoomAction)
        plot.setInteractiveMode("pan")

        resetZoom = actions.control.ResetZoomAction(parent=self, plot=plot)
        self.addAction(resetZoom)
        colormapAction = actions.control.ColormapAction(parent=self, plot=plot)
        colormapDialog = ColormapDialog(parent=self)
        colormapAction.setColorDialog(colormapDialog)
        self.addAction(colormapAction)
        self._togglePeaksAction = qt.QAction(
            qtawesome.icon("fa6s.xmark", rotated=45), "Show/Hide Filtered Peaks", self
        )
        self._togglePeaksAction.setIconText("Filtered peaks")
        self._togglePeaksAction.setCheckable(True)
        self._togglePeaksAction.setChecked(True)
        self._togglePeaksAction.setDisabled(True)
        self._togglePeaksAction.triggered.connect(self.togglePeaks)
        self.addAction(self._togglePeaksAction)

    def enableTogglePeaksAction(self, value: bool):
        self._togglePeaksAction.setEnabled(value)


class PeakFilterPlot2D(qt.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initCentralLayout()
        toolbar = _PeakFilterToolBar(
            plot=self._plot,
            parent=self,
        )
        toolbar.togglePeaks.connect(self._toggleFilteredPeaks)
        toolbar.setToolButtonStyle(qt.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(qt.Qt.TopToolBarArea, toolbar)
        self._toolbar = toolbar

    def addPeakAttributesAction(self, axisControls: AxisControlWidget):
        self._axisControls = axisControls
        self._toolbar.addWidget(self._axisControls)

    def _initCentralLayout(self):
        centralWidget = qt.QWidget(self)
        self.setCentralWidget(centralWidget)

        self._plot = PlotWidget(parent=centralWidget, backend="gl")
        self._plot.setGraphGrid(True)
        self._plot.setAxesMargins(0.05, 0.03, 0.03, 0.05)
        self._plot.setKeepDataAspectRatio(False)
        positionInfo = PositionInfo(plot=self._plot, parent=centralWidget)

        layout = qt.QGridLayout(centralWidget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot, 0, 0)
        layout.addWidget(positionInfo, 1, 0, 1, 2)

        centralWidget.setLayout(layout)

    def getXAxis(
        self,
    ):
        return self._plot.getXAxis()

    def getYAxis(
        self,
    ):
        return self._plot.getYAxis()

    def getPlotWidget(self) -> PlotWidget:
        return self._plot

    def addUnfilteredScatter(
        self,
        x: np.ndarray,
        y: np.ndarray,
        value: np.ndarray,
        colormap: Colormap | dict,
    ) -> Scatter:
        scatter = self._plot.addScatter(
            x=x,
            y=y,
            value=value,
            colormap=colormap,
            symbol="o",
            legend=_UNFILTERED_PEAKS_LEGEND,
            z=1,
        )
        scatter.setSymbolSize(10)
        return scatter

    def addFilteredScatter(
        self,
        x: np.ndarray,
        y: np.ndarray,
        value: np.ndarray,
        colormap: Colormap | dict,
    ) -> Scatter:
        scatter = self._plot.addScatter(
            x=x,
            y=y,
            value=value,
            colormap=colormap,
            symbol="+",
            legend=_FILTERED_PEAKS_LEGEND,
            z=2,
        )
        scatter.setSymbolSize(7)
        self._toolbar.enableTogglePeaksAction(True)
        return scatter

    def resetZoom(self):
        self._plot.resetZoom()

    def setYAxisLogarithmic(self, flag=True):
        self._plot.setYAxisLogarithmic(flag)

    def setGraphXLabel(self, str_val: str):
        self._plot.setGraphXLabel(str_val)

    def setGraphYLabel(self, label: str):
        self._plot.setGraphYLabel(label)

    def _toggleFilteredPeaks(self, checked: bool):
        scatter = self._plot.getScatter(legend=_FILTERED_PEAKS_LEGEND)
        if scatter:
            scatter.setVisible(checked)

    def addCurve(self, x: np.ndarray, y: np.ndarray, legend: str, linewidth: int):
        self._plot.addCurve(x, y, legend=legend, linewidth=linewidth)

    def addRings(self, rings_ds: Sequence[float]):
        for i, ring_ds in enumerate(rings_ds):
            marker = self._plot.addXMarker(
                ring_ds, legend=f"Ring {i}", text=f"Ring {i}"
            )
            color, ls = self._plot._getColorAndStyle()
            marker.setColor(color)
            marker.setLineStyle(ls)
            marker.setLineWidth(2)
