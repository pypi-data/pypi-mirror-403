from __future__ import annotations
from silx.gui import qt
import os
from ..common.filename_completer_line_edit import FilenameCompleterLineEdit

_FEEDBACK_TIMEOUT = 5000


class MasterFileWidget(qt.QWidget):
    sigMasterFileChanged = qt.Signal(str)

    def __init__(
        self,
        dialogTitle="Select Master File",
        parent: qt.QWidget | None = None,
        **kwargs,
    ) -> None:
        super().__init__(parent=parent, **kwargs)

        self._lineEdit = FilenameCompleterLineEdit(self)
        self._fileDialogFilters = [
            "All Files (*)",
        ]
        self._lineEdit.setToolTip("No file selected")
        self._lineEdit.setToolTipDuration(5000)

        self._browseBtn = qt.QPushButton("Browse...")
        layout = qt.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._lineEdit)
        layout.addWidget(self._browseBtn)

        self._dialogTitle = dialogTitle
        self._currentPath = ""

        self._browseBtn.clicked.connect(self._openFileDialog)
        self._lineEdit.textEdited.connect(self._onPathChanged)
        self._lineEdit.returnPressed.connect(
            lambda: self._onPathChanged(self._lineEdit.text(), forceEmit=True)
        )

    def _openFileDialog(self):
        fileDialog = qt.QFileDialog(self, self._dialogTitle)
        fileDialog.setViewMode(qt.QFileDialog.Detail)
        fileDialog.setNameFilters(self._fileDialogFilters)
        path, _ = fileDialog.getOpenFileName(
            self, self._dialogTitle, filter=";;".join(self._fileDialogFilters)
        )
        if path:
            self._lineEdit.setText(path)
            self._onPathChanged(path)

    def setNameFilters(self, filters: list[str]) -> None:
        """
        Sets the filters used in the file dialog.
        """
        self._fileDialogFilters = filters

    def getText(self) -> str:
        return self._lineEdit.text().strip()

    def setText(self, file_path):
        self._lineEdit.setText(file_path)
        self._currentPath = file_path
        self._updateLabelDisplay(file_path)

    def _onPathChanged(self, text: str):
        path = text.strip()
        self._currentPath = path
        self._updateLabelDisplay(path)

        if os.path.exists(path) and os.path.isfile(path):
            self.sigMasterFileChanged.emit(path)
        else:
            self._lineEdit.setToolTip("Not a valid file path")

    def setAutoDefault(self, status: bool):
        self._browseBtn.setAutoDefault(status)

    def _updateLabelDisplay(self, filePath: str):
        self._lineEdit.setToolTip(filePath)
