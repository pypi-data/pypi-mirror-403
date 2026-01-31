from ewoksorange.gui.owwidgets.meta import ow_build_opts
from silx.gui import qt
from silx.io.utils import DataUrl

from ewoks3dxrd.nexus.utils import group_exists

from .axes_control_widget import AxisControlWidget
from .ewoks3dxrd_grainplotter import Ewoks3DXRDGrainPlotter
from .peak_filter_plot2d import PeakFilterPlot2D


class Ewoks3DXRDPeaksPlotter(Ewoks3DXRDGrainPlotter, **ow_build_opts):
    """
    This class provide uniform way to plot the incoming peaks either triggered from another task
    or it was provided by user in the line edit of input data url widget
    """

    def __init__(self):
        super().__init__()
        self._axisControls: AxisControlWidget = None
        self._xPeakAttr = "ds"
        self._yPeakAttr = "eta"

    def __post_init__(self):
        super().__post_init__()
        self._plotIncomingPeaks()

    def _buildPeaksAttributeControlPlot(self):
        self._customPeak2DPlot = PeakFilterPlot2D(self)
        self._logPlotEvents(self._customPeak2DPlot._plot)
        self._axisControls: AxisControlWidget = AxisControlWidget(
            self, self._customPeak2DPlot
        )
        self._customPeak2DPlot.addPeakAttributesAction(self._axisControls)
        self._axisControls.sigAxisChanged.connect(self.setCustomPeaksAttr)

    def setCustomPeaksAttr(
        self,
    ):
        if self._axisControls is None:
            return

        self._xPeakAttr = self._axisControls.getSelectedX()
        self._yPeakAttr = self._axisControls.getSelectedY()
        self.plotCustomPeakPlot()

    def plotCustomPeakPlot(self):
        raise NotImplementedError("Base class")

    def populateCustomPeakAttr(
        self,
        availableKeys: tuple[str, ...],
    ):
        if self._axisControls:
            self._axisControls.populateAxes(
                availableKeys=availableKeys,
                defaultX=self._xPeakAttr,
                defaultY=self._yPeakAttr,
            )

    def _plotIncomingPeaks(
        self,
    ):
        raise NotImplementedError("Base class")

    def _inPeaksWidgetExecution(
        self,
        urlWidget: qt.QLineEdit,
        defaultInputKey: str,
        errorTitle: str,
    ) -> None:
        dataURL = urlWidget.text()
        input_peaks_url = DataUrl(dataURL)
        data_url_exist = group_exists(
            filename=input_peaks_url.file_path(),
            data_group_path=input_peaks_url.data_path(),
        )
        if data_url_exist is False:
            not_found_exception = FileNotFoundError(
                f"The specified data URL does not exist: '{dataURL}'"
            )
            self.showError(not_found_exception, title=errorTitle)
            return
        self.set_default_input(defaultInputKey, dataURL)
        self._plotIncomingPeaks()
