from __future__ import annotations

import os
import logging
from silx.gui import qt

from ewoks3dxrd.models import SampleConfig

from ..common.master_file_widget import MasterFileWidget
from .constants import OmegaMotor
from .utils import find_possible_scan_numbers, get_unique_instrument_keys

_logger = logging.getLogger(__name__)


class SampleConfigGroupBox(qt.QGroupBox):
    sigMasterFileChanged = qt.Signal(str)

    def __init__(
        self, title: str = "Sample Config Settings", parent: qt.QWidget | None = None
    ) -> None:
        super().__init__(title, parent=parent)
        folderLayout = qt.QFormLayout(self)

        self._masterFilePath = MasterFileWidget(dialogTitle="Experiment Master File")
        self._masterFilePath.setNameFilters(["Hdf5 Files (*.h5)", "NeXus Files (*.nx)"])
        self._masterFilePath.setAutoDefault(False)
        self._masterFilePath.sigMasterFileChanged.connect(self._fillDefaultValues)

        self._motorComboBox = qt.QComboBox()
        self._motorComboBox.addItems([motor.value for motor in OmegaMotor])

        self._scanComboBox = qt.QComboBox()

        folderLayout.addRow("Master File:", self._masterFilePath)
        folderLayout.addRow("Rotation Motor:", self._motorComboBox)
        folderLayout.addRow("Scan No:", self._scanComboBox)

    def getSampleConfig(self) -> SampleConfig | None:
        masterFilePath = self._masterFilePath.getText()
        if not os.path.isfile(masterFilePath):
            self.showError("Error", f"Master file does not exist: {masterFilePath}")
            return None
        config = {
            "omega_motor": self._motorComboBox.currentText(),
            "master_file": masterFilePath,
            "scan_number": self.getScanNumber(),
        }
        return SampleConfig(**config)

    def setSampleConfig(self, config: SampleConfig) -> None:
        if config is None:
            return
        self._masterFilePath.setText(config.master_file)
        self._motorComboBox.setCurrentText(config.omega_motor)
        self._scanComboBox.clear()
        self._scanComboBox.addItem(str(config.scan_number))
        self._scanComboBox.setCurrentText(str(config.scan_number))

    def showError(self, info: str, title: str | None = None):
        qt.QMessageBox.critical(self, info, title)

    def _fillDefaultValues(self, master_file_path: str):
        self._setDefaultScanNumber(master_file_path)
        self._setDefaultMotor(master_file_path)
        self.sigMasterFileChanged.emit(master_file_path)

    def _setDefaultScanNumber(self, master_file: str):
        self._scanComboBox.clear()
        if not os.path.isfile(master_file):
            _logger.debug(f"No valid master file: {master_file}.")
            return
        candidates = find_possible_scan_numbers(master_file)
        for c in candidates:
            self._scanComboBox.addItem(str(c))
        self._scanComboBox.setDisabled(len(candidates) <= 1)

    def _setDefaultMotor(self, master_file_path: str):
        if not os.path.isfile(master_file_path):
            _logger.warning(f"No valid master file: {master_file_path}.")
            return
        instrument_keys = get_unique_instrument_keys(
            master_file=master_file_path, groups=["1.1", "1.2"]
        )
        omega_match = None
        for motor in OmegaMotor:
            if motor in instrument_keys:
                omega_match = motor
                break

        if omega_match:
            idx = self._motorComboBox.findText(omega_match)
            if idx != -1:
                self._motorComboBox.setCurrentIndex(idx)
                self._motorComboBox.setEnabled(False)

    def getScanNumber(self) -> int | None:
        try:
            return int(self._scanComboBox.currentText())
        except ValueError:
            # case not scan defined.
            return None

    def getMasterFilePath(self) -> str:
        return self._masterFilePath.getText()

    def hasValidMasterFile(self) -> bool:
        return os.path.isfile(self._masterFilePath.getText().strip())
