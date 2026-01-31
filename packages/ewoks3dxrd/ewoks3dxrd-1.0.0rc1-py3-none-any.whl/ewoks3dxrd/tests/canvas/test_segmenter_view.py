from orangecontrib.ewoks3dxrd.segmenter_frame import OWFrameSegmenter
from orangecontrib.ewoks3dxrd.segment.base_segmenter_algo_view import (
    _BaseSegmenterAlgoView as BaseSegmenterAlgoView,
)
from orangecontrib.ewoks3dxrd.segment.lima_segmenter_param_view import (
    LimaSegmenterParamView,
)
from orangecontrib.ewoks3dxrd.segment.gaussian_segmenter_param_view import (
    GaussianPeakSearchParamView,
)

from silx.gui import qt

ALGORITHMS: list[str] = [
    "gaussian_peak_search",
    "lima_segmenter",
]

VIEWS: list[BaseSegmenterAlgoView] = [
    GaussianPeakSearchParamView,
    LimaSegmenterParamView,
]


def _set_and_assert_segmenter(
    widget: OWFrameSegmenter, index: int = 0, list_index: int = 0
):
    widget._settingsPanel._segmenter_group._algoSelector.setCurrentIndex(index)
    qt.QApplication.instance().processEvents()
    assert (
        widget._settingsPanel._segmenter_group._currentAlgorithm
        == ALGORITHMS[list_index]
    )
    current_view = widget._settingsPanel._segmenter_group._currentView
    assert current_view is not None
    assert isinstance(current_view, VIEWS[list_index])


def test_segmenter_view_switch(qtapp):  # noqa F401
    widget = OWFrameSegmenter()
    segmenter_group = widget._settingsPanel._segmenter_group
    index = segmenter_group._algoSelector.findText(ALGORITHMS[0])
    assert index != -1, f"Algorithm {ALGORITHMS[0]} not found in ComboBox items."
    _set_and_assert_segmenter(widget=widget, index=index, list_index=0)
    index = segmenter_group._algoSelector.findText(ALGORITHMS[1])
    assert index != -1, f"Algorithm {ALGORITHMS[1]} not found in ComboBox items."
    _set_and_assert_segmenter(widget=widget, index=index, list_index=1)
    index = segmenter_group._algoSelector.findText(ALGORITHMS[0])
    assert index != -1, f"Algorithm {ALGORITHMS[0]} not found in ComboBox items."
    _set_and_assert_segmenter(widget=widget, index=index, list_index=0)
