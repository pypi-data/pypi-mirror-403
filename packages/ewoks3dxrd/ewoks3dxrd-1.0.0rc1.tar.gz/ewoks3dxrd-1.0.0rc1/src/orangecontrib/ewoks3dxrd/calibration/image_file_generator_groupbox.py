from __future__ import annotations


import os
from silx.gui import qt
from ..common.master_file_widget import MasterFileWidget
from ..segment.constants import Detector
from ..segment.utils import find_possible_scan_numbers, get_unique_instrument_keys


class ImageFileGeneratorGroupBox(qt.QGroupBox):
    sigMasterFileChanged = qt.Signal(str)

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__("Correction Image Metadata Settings", parent=parent, **kwargs)
        folderLayout = qt.QFormLayout(self)

        self._masterFilePath = MasterFileWidget(dialogTitle="Experiment Master File")
        self._masterFilePath.setNameFilters(["Hdf5 Files (*.h5)", "NeXus Files (*.nx)"])
        folderLayout.addRow("Master File:", self._masterFilePath)
        self._masterFilePath.sigMasterFileChanged.connect(self._onMasterFileChanged)

        self._detector = qt.QComboBox()
        self._detector.addItems([detector.value for detector in Detector])
        self._detector.setToolTip("Select detector used for the experiment.")
        folderLayout.addRow("Detector:", self._detector)

        self._scanNumber = qt.QComboBox()
        self._scanNumber.setToolTip("Select scan number from master file.")
        folderLayout.addRow("Scan Number:", self._scanNumber)

    def _onMasterFileChanged(self, masterFilePath: str):
        self._setDefaultFolderMetadata(masterFilePath)

        if os.path.isfile(masterFilePath):
            instrumentKeys = get_unique_instrument_keys(
                master_file=masterFilePath, groups=["1.1"]
            )
            self._setDefaultDetector(instrumentKeys)
            self.sigMasterFileChanged.emit(masterFilePath)
        else:
            self._scanNumber.clear()
            self._scanNumber.setDisabled(True)
            self._detector.setCurrentIndex(0)
            self._detector.setEnabled(True)
            self.showError("Error", f"Master file not found: {masterFilePath}")

    def _setDefaultFolderMetadata(self, master_file: str):
        self._scanNumber.clear()
        print(master_file)
        if not os.path.isfile(master_file):
            return

        candidates = find_possible_scan_numbers(master_file)
        for c in candidates:
            self._scanNumber.addItem(str(c))
        self._scanNumber.setDisabled(len(candidates) <= 1)

    def _setDefaultDetector(self, instrumentKeys: list[str]):
        detectorMatch = None
        for detector in Detector:
            if detector.value in instrumentKeys:
                detectorMatch = detector.value
                break

        if detectorMatch:
            self._detector.setCurrentText(detectorMatch)
        self._detector.setEnabled(detectorMatch is None)

    def getConfig(self) -> dict:
        masterFilePath = self._masterFilePath.getText()
        if not os.path.isfile(masterFilePath):
            self.showError("Error", f"Master file does not exist: {masterFilePath}")
            return {}

        return {
            "master_file_path": masterFilePath,
            "scan_number": int(self._scanNumber.currentText()),
            "detector": self._detector.currentText(),
        }

    def getScanNumber(self) -> int:
        return int(self._scanNumber.currentText())

    def getMasterFilePath(self) -> str:
        return self._masterFilePath.getText()

    def showError(self, info: str, title: str | None = None):
        qt.QMessageBox.critical(self, info, title)
