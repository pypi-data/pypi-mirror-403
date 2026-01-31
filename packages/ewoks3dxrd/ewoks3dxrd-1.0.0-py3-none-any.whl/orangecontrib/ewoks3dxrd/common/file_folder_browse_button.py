from __future__ import annotations
from silx.gui import qt
from .filename_completer_line_edit import FilenameCompleterLineEdit


class FileFolderBrowseButton(qt.QWidget):
    def __init__(
        self,
        parent: qt.QWidget | None = None,
        dialogTitle: str = "",
        directory: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(parent=parent, **kwargs)

        layout = qt.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._dialogTitle = dialogTitle
        self._directory = directory
        self._lineEdit = FilenameCompleterLineEdit(self)
        self._browseBtn = qt.QPushButton("Browse...")
        self._browseBtn.setAutoDefault(False)
        self._browseBtn.clicked.connect(self._openDialog)
        self._fileDialogFilters = [
            "All Files (*)",
        ]

        layout.addWidget(self._lineEdit)
        layout.addWidget(self._browseBtn)

    def _openDialog(self):
        path = ""
        if self._directory:
            fileDialog = qt.QFileDialog(self, self._dialogTitle)
            fileDialog.setFileMode(qt.QFileDialog.FileMode.Directory)
            fileDialog.setOption(qt.QFileDialog.Option.ShowDirsOnly, True)
            fileDialog.setNameFilters(self._fileDialogFilters)
            currentPath = self._lineEdit.text().strip()
            if currentPath:
                fileDialog.setDirectory(currentPath)
            if fileDialog.exec_() == qt.QDialog.DialogCode.Accepted:
                path = fileDialog.selectedFiles()[0]
        else:
            path, _ = qt.QFileDialog.getOpenFileName(
                self, self._dialogTitle, filter=";;".join(self._fileDialogFilters)
            )
        if path:
            self._lineEdit.setText(path)

    def getText(self) -> str:
        return self._lineEdit.text().strip()

    def setText(self, path: str):
        self._lineEdit.setText(path)

    def setNameFilters(self, filters: list[str]) -> None:
        """
        Sets the filters used in the file dialog.
        """
        self._fileDialogFilters = filters

    def eventFilter(self, source, event):
        if event.type() == qt.QtCore.QEvent.Type.ToolTip and self.getText():
            qt.QToolTip.showText(event.globalPos(), self.getText(), self)
            return True
        return super().eventFilter(source, event)

    def clearText(self):
        self._lineEdit.clear()
