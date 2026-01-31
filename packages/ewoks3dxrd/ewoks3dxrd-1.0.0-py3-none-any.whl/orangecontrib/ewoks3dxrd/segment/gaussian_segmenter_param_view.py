from __future__ import annotations

from silx.gui import qt
from .base_segmenter_algo_view import _BaseSegmenterAlgoView as BaseSegmenterAlgoView
from ewoks3dxrd.models import SegmenterConfig, GaussianPeakSearchConfig

from ..common.utils import NoWheelSpinBox, NoWheelDoubleSpinBox
from .constants import GAUSSIAN_SEGMENTER_DEFAULTS, GAUSSIAN_SEGMENTER_TOOLTIPS


class GaussianPeakSearchParamView(BaseSegmenterAlgoView):
    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)
        seg_layout = qt.QFormLayout()
        self._threshold = NoWheelSpinBox(
            self,
        )
        self._threshold.setRange(0, 1000)
        self._threshold.setValue(GAUSSIAN_SEGMENTER_DEFAULTS["threshold"])
        self._threshold.setSingleStep(1)

        self._smooth_sigma = NoWheelDoubleSpinBox(
            self,
        )
        self._smooth_sigma.setRange(0.0, 6.0)
        self._smooth_sigma.setValue(GAUSSIAN_SEGMENTER_DEFAULTS["smooth_sigma"])
        self._smooth_sigma.setSingleStep(0.01)
        self._smooth_sigma.setDecimals(3)

        self._bgc = NoWheelDoubleSpinBox()
        self._bgc.setRange(0.0, 1.0)
        self._bgc.setValue(GAUSSIAN_SEGMENTER_DEFAULTS["bgc"])
        self._bgc.setSingleStep(0.01)
        self._bgc.setDecimals(3)

        self._min_px = NoWheelSpinBox(
            self,
        )
        self._min_px.setRange(0, 10000)
        self._min_px.setValue(GAUSSIAN_SEGMENTER_DEFAULTS["min_px"])
        self._min_px.setSingleStep(1)

        self._offset_threshold = NoWheelSpinBox(
            self,
        )
        self._offset_threshold.setRange(0, 1000)
        self._offset_threshold.setValue(GAUSSIAN_SEGMENTER_DEFAULTS["offset_threshold"])
        self._offset_threshold.setSingleStep(1)

        self._ratio_threshold = NoWheelSpinBox(
            self,
        )
        self._ratio_threshold.setRange(0, 1000)
        self._ratio_threshold.setValue(GAUSSIAN_SEGMENTER_DEFAULTS["ratio_threshold"])
        self._ratio_threshold.setSingleStep(1)

        self._threshold.setToolTip(GAUSSIAN_SEGMENTER_TOOLTIPS["threshold"])
        self._smooth_sigma.setToolTip(GAUSSIAN_SEGMENTER_TOOLTIPS["smooth_sigma"])
        self._bgc.setToolTip(GAUSSIAN_SEGMENTER_TOOLTIPS["bgc"])
        self._min_px.setToolTip(GAUSSIAN_SEGMENTER_TOOLTIPS["min_px"])
        self._offset_threshold.setToolTip(
            GAUSSIAN_SEGMENTER_TOOLTIPS["offset_threshold"]
        )
        self._ratio_threshold.setToolTip(GAUSSIAN_SEGMENTER_TOOLTIPS["ratio_threshold"])

        seg_layout.addRow("Threshold:", self._threshold)
        seg_layout.addRow("Smooth Sigma:", self._smooth_sigma)
        seg_layout.addRow("Background Constant:", self._bgc)
        seg_layout.addRow("Min Pixels:", self._min_px)
        seg_layout.addRow("Offset Threshold:", self._offset_threshold)
        seg_layout.addRow("Ratio Threshold:", self._ratio_threshold)
        self.setLayout(seg_layout)

        for widget in [
            self._threshold,
            self._smooth_sigma,
            self._bgc,
            self._min_px,
            self._offset_threshold,
            self._ratio_threshold,
        ]:
            widget.valueChanged.connect(self._debounceTimer.start)

    def getConfig(self) -> SegmenterConfig:
        return GaussianPeakSearchConfig(
            algorithm="gaussian_peak_search",
            threshold=self._threshold.value(),
            smooth_sigma=self._smooth_sigma.value(),
            bgc=self._bgc.value(),
            min_px=self._min_px.value(),
            offset_threshold=self._offset_threshold.value(),
            ratio_threshold=self._ratio_threshold.value(),
        )

    def setConfig(self, config: SegmenterConfig):
        self._threshold.setValue(config.threshold)
        self._smooth_sigma.setValue(config.smooth_sigma)
        self._bgc.setValue(config.bgc)
        self._offset_threshold.setValue(config.offset_threshold)
        self._ratio_threshold.setValue(config.ratio_threshold)
