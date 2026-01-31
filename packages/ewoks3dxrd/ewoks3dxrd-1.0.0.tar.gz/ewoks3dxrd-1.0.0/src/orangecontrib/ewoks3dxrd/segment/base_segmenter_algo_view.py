from __future__ import annotations
from typing import Any
from silx.gui import qt
from ..common.debounce_timer import DebounceTimer

from ewoks3dxrd.models import (
    SegmenterConfig,
    GaussianPeakSearchConfig,
    LimaSegmenterAlgoConfig,
)


class _BaseSegmenterAlgoView(qt.QWidget):
    sigParamsChanged = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)
        self._lastParams: dict[str, Any] = {}
        self._debounceTimer = DebounceTimer(
            callback=self._onParamChanged, timeout_ms=200, parent=self
        )

    def getConfig(self) -> SegmenterConfig:
        raise NotImplementedError("Base class")

    def setConfig(self, config: SegmenterConfig):
        raise NotImplementedError("Base class")

    def _onParamChanged(self):
        try:
            params = self.getConfig()
        except NotImplementedError as e:
            raise e
        if not isinstance(params, (GaussianPeakSearchConfig, LimaSegmenterAlgoConfig)):
            error_msg = (
                f"'getConfig()' is expected to return an instance of {SegmenterConfig}"
                f"(like {GaussianPeakSearchConfig} or {LimaSegmenterAlgoConfig}), "
                f"but got {type(params).__name__}."
            )
            raise TypeError(error_msg)

        currentParamsDump = params.model_dump()
        if not params or self._lastParams == currentParamsDump:
            return

        self._lastParams = currentParamsDump
        self.sigParamsChanged.emit()
