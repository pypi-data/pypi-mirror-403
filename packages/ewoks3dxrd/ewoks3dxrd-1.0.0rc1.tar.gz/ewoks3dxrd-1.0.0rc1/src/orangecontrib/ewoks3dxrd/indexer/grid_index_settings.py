from silx.gui import qt

from ewoks3dxrd.models import GridIndexParameters

from .grid_index_parameter_group_box import GridIndexParameterGroupBox


class GridIndexSettings(qt.QWidget):
    sigGridSettingsChanged = qt.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Grid Index Config")
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        layout = qt.QVBoxLayout()

        _gridSearchGroup = qt.QGroupBox("Sample and Beam Info")

        self._sampleWidth = qt.QSpinBox()
        self._sampleWidth.setRange(1, 100000)
        self._sampleWidth.setValue(1200)
        self._sampleWidth.setSuffix(" µm")
        self._sampleWidth.setToolTip("Provide width of sample.")

        self._sampleDepth = qt.QSpinBox()
        self._sampleDepth.setRange(1, 100000)
        self._sampleDepth.setValue(1200)
        self._sampleDepth.setSuffix(" µm")
        self._sampleDepth.setToolTip("Provide depth of sample.")

        self._beamIlluminationRange = qt.QSpinBox()
        self._beamIlluminationRange.setRange(1, 100000)
        self._beamIlluminationRange.setValue(200)
        self._beamIlluminationRange.setSuffix(" µm")
        self._beamIlluminationRange.setToolTip("Provide beam height.")

        self._grainSpottingWidth = qt.QSpinBox()
        self._grainSpottingWidth.setRange(1, 10000)
        self._grainSpottingWidth.setValue(100)
        self._grainSpottingWidth.setSuffix(" µm")
        self._grainSpottingWidth.setToolTip("Provide 1 or 2 times detector pixel size.")

        gridSearchLayout = qt.QFormLayout(_gridSearchGroup)
        gridSearchLayout.addRow("Sample Width", self._sampleWidth)
        gridSearchLayout.addRow("Sample Depth", self._sampleDepth)
        gridSearchLayout.addRow("Beam Height", self._beamIlluminationRange)
        gridSearchLayout.addRow("Grid Step", self._grainSpottingWidth)

        layout.addWidget(_gridSearchGroup)
        self._gridIndexParametergroup = GridIndexParameterGroupBox(self)
        self._gridIndexParametergroup.sigGridSettingsChanged.connect(
            self.sigGridSettingsChanged
        )
        layout.addWidget(self._gridIndexParametergroup)
        self.setLayout(layout)

    def getGridIndexParameters(self) -> dict:
        return self._gridIndexParametergroup.getGridIndexParameters().model_dump()

    def getGridXLimit(self) -> int:
        return int(self._sampleWidth.value() / 2)

    def getGridYLimit(self) -> int:
        return int(self._sampleDepth.value() / 2)

    def getGridZLimit(self) -> int:
        return int(self._beamIlluminationRange.value() / 2)

    def getGridStep(self) -> int:
        return self._grainSpottingWidth.value()

    def setGridIndexParameters(self, value: dict):
        self._gridIndexParametergroup.setGridIndexParameters(
            GridIndexParameters(**value)
        )

    def setGridXLimit(self, value: int):
        self._sampleWidth.setValue(2 * value)

    def setGridYLimit(self, value: int):
        self._sampleDepth.setValue(2 * value)

    def setGridZLimit(self, value: int):
        self._beamIlluminationRange.setValue(2 * value)

    def setGridStep(self, value: int):
        self._grainSpottingWidth.setValue(value)
