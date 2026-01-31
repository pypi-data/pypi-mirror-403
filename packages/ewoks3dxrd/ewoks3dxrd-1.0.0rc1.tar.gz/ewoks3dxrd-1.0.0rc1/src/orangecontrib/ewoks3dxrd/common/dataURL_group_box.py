from silx.gui import qt
from silx.gui.dialog.GroupDialog import GroupDialog
from silx.io.utils import DataUrl
from ewoks3dxrd.nexus.utils import group_exists


class DataURLGroupBox(qt.QGroupBox):
    editingFinished = qt.Signal(str)
    textChanged = qt.Signal()

    def __init__(self, title="Segmented Data Group Source", parent=None):
        super().__init__(title, parent)
        self.setLayout(qt.QHBoxLayout())

        self.dataURLLineEdit = qt.QLineEdit()
        self.dataURLLineEdit.textChanged.connect(self.textChanged.emit)
        self.dataURLLineEdit.setPlaceholderText("Enter DATA URL or click Browse...")
        self.dataURLLineEdit.installEventFilter(self)
        self._browseButton = qt.QPushButton("Browse H5 Group...")
        self._browseButton.clicked.connect(self._selectH5Group)
        self._browseButton.setAutoDefault(False)
        self.layout().addWidget(self.dataURLLineEdit)
        self.layout().addWidget(self._browseButton)

        self.dataURLLineEdit.editingFinished.connect(
            lambda: self.editingFinished.emit(self.dataURLLineEdit.text())
        )

    def setText(self, text: str):
        self.dataURLLineEdit.setText(text)

    def text(self) -> str:
        return self.dataURLLineEdit.text().strip()

    def _selectH5Group(self):
        fileName, _ = qt.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select NeXus/HDF5 File",
            filter="HDF5 Files (*.h5 *.hdf5 *.nx *.nxs);;All Files (*)",
        )

        if not fileName:
            return

        dialog = GroupDialog(self)
        dialog.addFile(fileName)
        dialog.setWindowTitle(f"Select Data Group in: {fileName.split('/')[-1]}")

        if dialog.exec():
            selectedURL = dialog.getSelectedDataUrl().path()
            self.dataURLLineEdit.setText(selectedURL)
            self.editingFinished.emit(selectedURL)

    def validDataURL(
        self,
    ) -> bool:
        url = self.text()
        if not url:
            return False
        dataURL = DataUrl(url)
        return group_exists(
            filename=dataURL.file_path(), data_group_path=dataURL.data_path()
        )

    def eventFilter(self, obj, event):
        """Intercept and discard Enter/Return key presses for the LineEdit."""
        if obj is self.dataURLLineEdit and event.type() == qt.QEvent.KeyPress:
            if event.key() in (qt.Qt.Key_Return, qt.Qt.Key_Enter):
                # We return True to say 'we handled this event' (by doing nothing)
                # This prevents the Enter key from triggering buttons or editingFinished logic
                return True
        return super().eventFilter(obj, event)
