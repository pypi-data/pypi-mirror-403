from silx.gui import qt
from silx.gui.plot3d.SceneWindow import SceneWindow


class GrainMapScene(SceneWindow):
    grainSizeChanged = qt.Signal(float)
    """
    A reusable SceneWindow with a pre-configured 3D scene and toolbar
    for adjusting grain visualization.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Configure the 3D scene's basic properties
        # The parent of the tree view and reset widget is a QDockWidget.
        # Calling parent() hides the QDockWidget.
        self.getParamTreeView().parent().setVisible(False)
        self.getGroupResetWidget().parent().setVisible(False)
        self.getSceneWidget().setBackgroundColor((0.8, 0.8, 0.8, 1.0))
        self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)

        mainToolbar = qt.QToolBar("Toolbar")
        self.addToolBar(mainToolbar)
        labelGrainSize = qt.QLabel("Grain Scale:")
        mainToolbar.addWidget(labelGrainSize)
        self._grainSizeSpinBox = qt.QDoubleSpinBox()
        self._grainSizeSpinBox.setRange(0.00002, 3)
        self._grainSizeSpinBox.setSingleStep(0.00001)
        self._grainSizeSpinBox.setDecimals(5)
        self._grainSizeSpinBox.setValue(0.0001)
        self._grainSizeSpinBox.setToolTip("Adjust grain size for visualization")
        mainToolbar.addWidget(self._grainSizeSpinBox)

        self._grainSizeSpinBox.valueChanged.connect(self.grainSizeChanged.emit)

    def getGrainSize(self) -> float:
        return self._grainSizeSpinBox.value()
