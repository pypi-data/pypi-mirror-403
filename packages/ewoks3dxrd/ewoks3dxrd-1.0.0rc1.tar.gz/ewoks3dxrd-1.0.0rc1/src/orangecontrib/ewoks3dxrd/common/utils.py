from __future__ import annotations

import traceback
from silx.gui import qt
from AnyQt.QtCore import QCoreApplication, QThread


def format_exception(error: Exception) -> str:
    return "\n".join(traceback.format_exception(error))


def getFileNameFromUser(fileType: str, extension: str):
    options = qt.QFileDialog.Options(qt.QFileDialog.DontUseNativeDialog)
    filePath, _ = qt.QFileDialog.getSaveFileName(
        None,
        f"Save {fileType}",
        "",
        f"File extensions (*.{extension})",
        options=options,
    )
    return filePath


def isPlotOnMainThread():
    app = QCoreApplication.instance()
    currentThreadId = QThread.currentThreadId()
    if app is None:
        return False, currentThreadId
    return (currentThreadId == app.thread()), currentThreadId


class NoWheelMixin:
    """A mixin to disable mouse wheel events for a widget."""

    def wheelEvent(self, event: qt.QWheelEvent) -> None:
        event.ignore()


class NoWheelSpinBox(NoWheelMixin, qt.QSpinBox):
    pass


class NoWheelDoubleSpinBox(NoWheelMixin, qt.QDoubleSpinBox):
    pass
