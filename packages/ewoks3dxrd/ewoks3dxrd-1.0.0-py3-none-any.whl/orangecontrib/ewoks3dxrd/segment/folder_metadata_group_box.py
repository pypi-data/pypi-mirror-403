from __future__ import annotations

import os
from pathlib import Path
from silx.gui import qt

from ewoks3dxrd.models import SegmenterFolderConfig

from ..common.file_folder_browse_button import FileFolderBrowseButton
from .constants import Detector
from .sample_config_group_box import SampleConfigGroupBox
from .utils import get_unique_instrument_keys


class FolderMetadataGroupBox(SampleConfigGroupBox):

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__("Folder and Metadata Settings", parent=parent, **kwargs)
        formLayout: qt.QFormLayout = self.layout()

        self._detector = qt.QComboBox()
        self._detector.addItems([e.value for e in Detector])
        formLayout.addRow("Detector:", self._detector)
        self._analyse_folder_path = FileFolderBrowseButton(
            dialogTitle="Select Analysis Folder", directory=True
        )
        formLayout.addRow("Analyse Folder Path:", self._analyse_folder_path)
        self.sigMasterFileChanged.connect(self._set_default_analyse_folder)
        self.sigMasterFileChanged.connect(self._set_default_detector)

    def _set_default_analyse_folder(self, _: str):
        parent_dir = str(Path.home())
        processed_data_path = os.path.join(parent_dir, "3DXRD_PROCESSED_DATA")
        if os.path.isdir(processed_data_path):
            self._analyse_folder_path.setText(processed_data_path)
        else:
            self._analyse_folder_path.setText(parent_dir)

    def _set_default_detector(self, master_file_path: str):
        instrument_keys = get_unique_instrument_keys(
            master_file=master_file_path, groups=["1.1", "1.2"]
        )
        detector_match = None
        for detector in Detector:
            if detector in instrument_keys:
                detector_match = detector
                break

        if detector_match:
            idx = self._detector.findText(detector_match)
            if idx != -1:
                self._detector.setCurrentIndex(idx)
                self._detector.setEnabled(False)

    def getConfig(self) -> SegmenterFolderConfig | None:
        sample_config = self.getSampleConfig()
        if sample_config is None:
            return None
        return SegmenterFolderConfig(
            **sample_config.model_dump(),
            detector=self._detector.currentText(),
            analyse_folder=self._analyse_folder_path.getText() or None,
        )

    def setConfig(self, config: SegmenterFolderConfig):
        self.setSampleConfig(config)
        self._detector.setCurrentText(config.detector)
        if config.analyse_folder:
            self._analyse_folder_path.setText(config.analyse_folder)
