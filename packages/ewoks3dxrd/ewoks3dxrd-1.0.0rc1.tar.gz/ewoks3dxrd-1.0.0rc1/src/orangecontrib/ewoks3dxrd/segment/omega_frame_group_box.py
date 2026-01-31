from __future__ import annotations

import numpy as np
import qtawesome
from silx.gui import qt

from .utils import get_omega_array


class OmegaFrameGroupBox(qt.QGroupBox):
    frameIndexChanged = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__("Omega and Frame Selection", parent=parent, **kwargs)

        self._omega_array: np.ndarray | None = None
        self._frame_idx: int | None = None

        layout = qt.QVBoxLayout(self)

        frame_layout = qt.QHBoxLayout()
        self._frame_index_label = qt.QLabel("Frame: auto")
        frame_layout.addWidget(self._frame_index_label)
        self._resetToAutoButton = qt.QPushButton(qtawesome.icon("fa5s.undo"), "Auto")
        self._resetToAutoButton.setSizePolicy(
            qt.QSizePolicy.Policy.Fixed, qt.QSizePolicy.Policy.Fixed
        )
        self._resetToAutoButton.setDisabled(True)
        frame_layout.addWidget(self._resetToAutoButton)
        layout.addLayout(frame_layout)

        self._frame_slider = qt.QSlider(qt.Qt.Horizontal)
        self._frame_slider.setDisabled(True)
        layout.addWidget(self._frame_slider)
        self._omega_label = qt.QLabel("Omega: auto")
        layout.addWidget(self._omega_label)

        self._frame_slider.sliderReleased.connect(self._updateFrameIndex)
        self._resetToAutoButton.clicked.connect(self._resetFrameIndex)

    def _updateFrameIndex(self):
        self._frame_idx = self._frame_slider.value()
        self._resetToAutoButton.setEnabled(True)
        if self._omega_array is None:
            return
        omega_value = float(self._omega_array[self._frame_idx])

        self._frame_index_label.setText(f"Frame Index: {self._frame_idx}")
        self._omega_label.setText(f"Omega: {omega_value:.2f}°")
        self.frameIndexChanged.emit()

    def _resetFrameIndex(self):
        self._frame_idx = None
        self._resetToAutoButton.setDisabled(True)

        self._frame_index_label.setText("Frame Index: auto")
        self._omega_label.setText("Omega: auto")
        self._frame_slider.setValue(0)
        self.frameIndexChanged.emit()

    def setOmegaArray(self, master_file: str, omega_motor: str, scan_id: str):
        self._omega_array = get_omega_array(
            file_path=master_file,
            omega_motor=omega_motor,
            scan_id=scan_id,
        )
        self._frame_slider.setDisabled(False)
        self._frame_slider.setMinimum(0)
        self._frame_slider.setMaximum(len(self._omega_array) - 1)

    def getFrameIdx(self) -> int | None:
        return self._frame_idx
