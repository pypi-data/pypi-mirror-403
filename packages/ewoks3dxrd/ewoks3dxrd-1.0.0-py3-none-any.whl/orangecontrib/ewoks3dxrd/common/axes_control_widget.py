from __future__ import annotations

from typing import Optional
from silx.gui import qt
from silx.gui.plot.actions.control import XAxisLogarithmicAction, YAxisLogarithmicAction
from silx.gui.utils import blockSignals


class AxesAttrAction(qt.QComboBox):
    sigAxisAttrChanged = qt.Signal()

    def __init__(
        self,
        text: str,
        parent: Optional[qt.QObject] = None,
        defaultKey: str = "s_raw",
    ):
        super().__init__(parent)
        self._text = text
        self._defaultKey = defaultKey
        self.currentIndexChanged.connect(self.sigAxisAttrChanged.emit)

    def getSelectedKey(self) -> str:
        return self.currentText() if self.currentText() else self._defaultKey

    def populateAxes(self, availableKeys: tuple[str, ...], defaultKey: str = None):
        if defaultKey is not None:
            self._defaultKey = defaultKey
        self._initialItems = availableKeys

        with blockSignals(self):
            self.clear()
            self.addItems(availableKeys)
            if self._defaultKey:
                index = availableKeys.index(self._defaultKey)
                self.setCurrentIndex(index)


class AxisControlWidget(qt.QToolBar):
    sigAxisChanged = qt.Signal()

    def __init__(self, parent=None, plot=None):
        super().__init__(parent)

        self._xAxisAttrAction = AxesAttrAction(
            text="X", parent=self, defaultKey="s_raw"
        )
        self._yAxisAttrAction = AxesAttrAction(
            text="Y", parent=self, defaultKey="f_raw"
        )
        xLogAxis = XAxisLogarithmicAction(parent=self, plot=plot)
        yLogAxis = YAxisLogarithmicAction(parent=self, plot=plot)
        self.addAction(xLogAxis)
        self.addAction(yLogAxis)
        self._xAxisAttrAction.sigAxisAttrChanged.connect(self.sigAxisChanged.emit)
        self._yAxisAttrAction.sigAxisAttrChanged.connect(self.sigAxisChanged.emit)
        self.addWidget(qt.QLabel("X-axis"))
        self.addWidget(self._xAxisAttrAction)
        self.addWidget(qt.QLabel("Y-axis"))
        self.addWidget(self._yAxisAttrAction)

    def populateAxes(
        self,
        availableKeys: tuple[str, ...],
        defaultX: str = "ds",
        defaultY: str = "eta",
    ):
        self._xAxisAttrAction.populateAxes(
            availableKeys=availableKeys, defaultKey=defaultX
        )
        self._yAxisAttrAction.populateAxes(
            availableKeys=availableKeys, defaultKey=defaultY
        )

    def getSelectedX(self) -> str:
        return self._xAxisAttrAction.getSelectedKey()

    def getSelectedY(self) -> str:
        return self._yAxisAttrAction.getSelectedKey()
