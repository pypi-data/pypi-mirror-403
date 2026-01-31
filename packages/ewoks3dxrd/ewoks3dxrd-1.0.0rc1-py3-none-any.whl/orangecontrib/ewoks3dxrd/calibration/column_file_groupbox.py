from __future__ import annotations
from silx.gui import qt
from ..common.dataURL_group_box import DataURLGroupBox


class ColumnFileGroupBox(qt.QGroupBox):
    sigUrlChanged = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__("ColumnFile Info", parent=parent, **kwargs)
        formLayout = qt.QFormLayout(self)
        self._url = DataURLGroupBox(title="Peaks Data URL")
        self._peaksInfo = qt.QLineEdit()
        self._url.textChanged.connect(self.sigUrlChanged.emit)
        formLayout.addWidget(self._url)
        formLayout.addRow("Peaks Info", self._peaksInfo)

    def setPeaksInfo(self, message: str):
        self._peaksInfo.setText(message)

    def getPeaksDataURL(self) -> str:
        return self._url.text()

    def setPeaksDataURL(self, dataURL: str):
        self._url.setText(dataURL)
