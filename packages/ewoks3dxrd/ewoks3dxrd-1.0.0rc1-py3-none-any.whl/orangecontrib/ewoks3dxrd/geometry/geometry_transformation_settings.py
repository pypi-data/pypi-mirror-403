from silx.gui import qt

from ..common.master_file_widget import MasterFileWidget
from .geometry_parameters import GeometryParameterGroupBox


class GeometryTransformationSettings(qt.QGroupBox):
    sigParametersChanged = qt.Signal()
    sigConfigurationChanged = qt.Signal()

    def __init__(self, parent=None, withRefinement=False):
        super().__init__("Geometry settings", parent)
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)

        layout = qt.QVBoxLayout()
        fileBtnLayout = qt.QFormLayout()
        self._geometryFileWidget = MasterFileWidget(
            dialogTitle="Geometry Parameter File"
        )
        self._geometryFileWidget.setNameFilters(
            [
                "par Files (*.par)",
                "PONI Files (*.poni)",
                "JSON Files (*.json)",
            ]
        )
        self._geometryFileWidget.setAutoDefault(False)
        fileBtnLayout.addRow("Import file", self._geometryFileWidget)
        layout.addLayout(fileBtnLayout)
        self._geoParameterGroup = GeometryParameterGroupBox(
            self, withRefinement=withRefinement
        )
        self._geoParameterGroup.sigGeometryParamsChanged.connect(
            self.sigParametersChanged.emit
        )
        layout.addWidget(self._geoParameterGroup)
        self.setLayout(layout)

        self._geometryFileWidget.sigMasterFileChanged.connect(
            self._updateGeometryParameters
        )
        if withRefinement:
            self._geoParameterGroup.sigConfigurationChanged.connect(
                self.sigConfigurationChanged
            )

    def _updateGeometryParameters(self, filePath: str):
        self._geoParameterGroup.fillGeometryValues(filePath=filePath)

    def getGeometryParameters(self) -> dict[str, str]:
        return self._geoParameterGroup.getGeometryParameters()

    def setGeometryFile(self, filePath: str):
        self._geometryFileWidget.setText(filePath)
        self._updateGeometryParameters(filePath)

    def setGeometryParameters(self, parameters: dict[str, float | int | bool]):
        self._geoParameterGroup.updateGeometryParameters(parameters=parameters)

    def getRefineParametersFlags(
        self,
    ) -> dict[str, bool]:
        par_dict = {
            name: self._geoParameterGroup.getParameterFlag(name)
            for name in self._geoParameterGroup._widgets.keys()
        }
        return par_dict

    def setRefineParameterFlag(self, name: str, flag: bool):
        self._geoParameterGroup.setParameterFlag(name=name, flag=flag)
