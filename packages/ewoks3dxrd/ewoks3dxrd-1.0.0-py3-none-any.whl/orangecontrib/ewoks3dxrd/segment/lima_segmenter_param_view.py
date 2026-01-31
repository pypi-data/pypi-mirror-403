from __future__ import annotations

from silx.gui import qt
from ewoks3dxrd.models import SegmenterConfig, LimaSegmenterAlgoConfig
from .base_segmenter_algo_view import _BaseSegmenterAlgoView as BaseSegmenterAlgoView
from ..common.utils import NoWheelSpinBox
from .constants import LIMA_SEGMENTER_DEFAULTS, LIMA_SEGMENTER_TOOLTIPS


class LimaSegmenterParamView(BaseSegmenterAlgoView):
    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)
        seg_layout = qt.QFormLayout()
        self._lowerBoundCut = NoWheelSpinBox(self)
        self._lowerBoundCut.setRange(0, 200)
        self._lowerBoundCut.setValue(LIMA_SEGMENTER_DEFAULTS["lower_bound_cut"])
        self._lowerBoundCut.setSingleStep(1)

        self._maxNumPeaks = NoWheelSpinBox(self)
        self._maxNumPeaks.setRange(1, int(1e9))
        self._maxNumPeaks.setValue(LIMA_SEGMENTER_DEFAULTS["max_pixels_per_frame"])
        self._maxNumPeaks.setSingleStep(1)

        self._numPixelsInSpot = NoWheelSpinBox(self)
        self._numPixelsInSpot.setRange(0, 100)
        self._numPixelsInSpot.setValue(LIMA_SEGMENTER_DEFAULTS["num_pixels_in_spot"])
        self._numPixelsInSpot.setSingleStep(1)

        self._lowerBoundCut.setToolTip(LIMA_SEGMENTER_TOOLTIPS["lower_bound_cut"])
        self._maxNumPeaks.setToolTip(LIMA_SEGMENTER_TOOLTIPS["max_pixels_per_frame"])
        self._numPixelsInSpot.setToolTip(LIMA_SEGMENTER_TOOLTIPS["num_pixels_in_spot"])

        seg_layout.addRow("Lower Bound Cut:", self._lowerBoundCut)
        seg_layout.addRow("Max #Peaks in Frame:", self._maxNumPeaks)
        seg_layout.addRow("Num Pixels in Spot:", self._numPixelsInSpot)
        self.setLayout(seg_layout)

        self._last_params: dict[str, int] = {}

        for widget in [
            self._lowerBoundCut,
            self._maxNumPeaks,
            self._numPixelsInSpot,
        ]:
            widget.valueChanged.connect(self._debounceTimer.start)

    def getConfig(self) -> SegmenterConfig:
        return LimaSegmenterAlgoConfig(
            algorithm="lima_segmenter",
            lower_bound_cut=self._lowerBoundCut.value(),
            max_pixels_per_frame=self._maxNumPeaks.value(),
            num_pixels_in_spot=self._numPixelsInSpot.value(),
        )

    def setConfig(self, config: SegmenterConfig):
        self._lowerBoundCut.setValue(config.lower_bound_cut)
        self._maxNumPeaks.setValue(config.max_pixels_per_frame)
        self._numPixelsInSpot.setValue(config.num_pixels_in_spot)
