from __future__ import annotations

from typing import Any

from silx.gui import qt
from ..common.collapsible_widget import CollapsibleWidget
from ewoks3dxrd.models import (
    SegmenterConfig,
    LimaSegmenterAlgoConfig,
    GaussianPeakSearchConfig,
)
from .base_segmenter_algo_view import _BaseSegmenterAlgoView as BaseSegmenterAlgoView
from .gaussian_segmenter_param_view import GaussianPeakSearchParamView
from .lima_segmenter_param_view import LimaSegmenterParamView


class SegmenterParamGroupBox(CollapsibleWidget):
    sigParamsChanged = qt.Signal()
    ALGORITHMS: list[str] = [
        GaussianPeakSearchConfig.model_fields["algorithm"].default,
        LimaSegmenterAlgoConfig.model_fields["algorithm"].default,
    ]

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__("Segmentation Parameters", parent=parent, **kwargs)

        mainLayout = qt.QVBoxLayout()
        self.setLayout(mainLayout)
        self._algoSelector = qt.QComboBox(self)
        for algo in self.ALGORITHMS:
            self._algoSelector.addItem(algo)
        self._algoSelector.setToolTip(
            "Select the segmentation method.\n\n"
            "**lima_segmenter:** Fast thresholding, ideal for high-count, low-noise data.\n"
            "**gaussian_peak_search:** Robust smoothing and background subtraction (ImageD11 style), ideal for noisy or complex backgrounds."
        )
        self._algoSelector.currentTextChanged.connect(self._buildUiForAlgorithm)
        mainLayout.addWidget(self._algoSelector)

        self._contentLayout = qt.QVBoxLayout()
        mainLayout.addLayout(self._contentLayout)
        self._currentView: BaseSegmenterAlgoView | None = None
        self._currentAlgorithm: str | None = None
        self._lastParams: dict[str, Any] = {}
        self._buildUiForAlgorithm(self.ALGORITHMS[0])

    def _clearLayout(self):
        if self._currentView is None:
            return

        self._currentView.sigParamsChanged.disconnect(self.sigParamsChanged)
        self._contentLayout.removeWidget(self._currentView)
        self._currentView.deleteLater()
        self._currentView = None

    def getConfig(self) -> SegmenterConfig | None:
        if self._currentView:
            return self._currentView.getConfig()
        return None

    def setConfig(self, config: SegmenterConfig):
        algorithmName = config.algorithm
        self._buildUiForAlgorithm(algorithmName)
        self._algoSelector.setCurrentText(algorithmName)

        if self._currentView:
            self._currentView.setConfig(config)

    def setAlgorithm(self, algorithmName: str):
        self._buildUiForAlgorithm(algorithmName)

    def _buildUiForAlgorithm(self, algorithmName: str):
        if algorithmName == self._currentAlgorithm:
            return
        self._clearLayout()

        if algorithmName == LimaSegmenterAlgoConfig.model_fields["algorithm"].default:
            self._currentView: BaseSegmenterAlgoView = LimaSegmenterParamView(self)
        elif (
            algorithmName == GaussianPeakSearchConfig.model_fields["algorithm"].default
        ):
            self._currentView: BaseSegmenterAlgoView = GaussianPeakSearchParamView(self)
        else:
            raise NotImplementedError(
                f"Provided Algorithm type: {algorithmName} not found in the library."
            )
        self._currentAlgorithm = algorithmName
        if self._currentView is not None:
            self._contentLayout.addWidget(self._currentView)

        self._currentView.sigParamsChanged.connect(self.sigParamsChanged)
        self.sigParamsChanged.emit()
