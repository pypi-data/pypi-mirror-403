from __future__ import annotations

import time

from silx.gui import qt


class LogWidget(qt.QDialog):
    sigTerminateRequested = qt.Signal()

    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)

        layout = qt.QVBoxLayout(self)
        self._textEdit = qt.QPlainTextEdit(self)
        self._textEdit.setReadOnly(True)
        layout.addWidget(self._textEdit)

        self._closeButton = qt.QPushButton("Close", self)
        self._closeButton.clicked.connect(self.close)
        layout.addWidget(self._closeButton)

        self._terminateButton = qt.QPushButton("Terminate", self)
        self._terminateButton.clicked.connect(self.terminate)
        layout.addWidget(self._terminateButton)
        self._lastLogTime: float = time.time()

    def appendLog(self, message: str, source: str = "INFO"):
        self._textEdit.appendPlainText(f"[{source}] {message}")
        self._lastLogTime = time.time()

    def setLastLogTime(self, lastLogTime: float):
        self._lastLogTime = lastLogTime

    def getLastLogTime(self):
        return self._lastLogTime

    def terminate(self):
        reply = qt.QMessageBox.question(
            self,
            "Confirm Termination",
            "Are you sure you want to stop Find/Refine Grain process?",
            qt.QMessageBox.Yes | qt.QMessageBox.No,
        )

        if reply == qt.QMessageBox.Yes:
            self.appendLog("Termination signal sent...", source="SYSTEM")
            self.sigTerminateRequested.emit()
