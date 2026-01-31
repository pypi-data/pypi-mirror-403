from __future__ import annotations

from typing import Tuple

from silx.gui import qt

_RESET_TOL_SEQ_VALUE: Tuple[float, ...] = (0.02, 0.015, 0.01)


class ToleranceSelector(qt.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = qt.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._resetBtn = qt.QPushButton("Reset to Default")
        self._lineEdit = qt.QLineEdit()
        self._lineEdit.setPlaceholderText("e.g. 0.2, 0.015, 0.01, 0.005")
        self._lineEdit.setToolTip(
            "HKL Tolerance Sequence in decreasing order to refine the Grains in Iteration"
        )
        layout.addWidget(self._lineEdit)
        layout.addWidget(self._resetBtn)
        self._resetBtn.clicked.connect(self._resetHKLSeq)
        self._resetHKLSeq()

    def _resetHKLSeq(self):
        self.setValue(_RESET_TOL_SEQ_VALUE)

    def getValue(self) -> Tuple[float, ...]:
        text = self._lineEdit.text().strip()
        if not text:
            raise ValueError("HKL-tolerance sequence values are empty")

        try:
            values = tuple(float(x.strip()) for x in text.split(",") if x.strip())
        except ValueError:
            raise ValueError("Invalid input. Please enter numbers separated by commas.")
        return values

    def setValue(self, value: Tuple[float, ...]):
        if not all(isinstance(v, (int, float)) for v in value):
            raise ValueError("All tolerance values must be numeric.")

        text = ", ".join(f"{v:g}" for v in value)
        self._lineEdit.setText(text)
