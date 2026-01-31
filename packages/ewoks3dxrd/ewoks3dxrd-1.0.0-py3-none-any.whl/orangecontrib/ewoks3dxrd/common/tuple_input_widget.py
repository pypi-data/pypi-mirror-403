from typing import Any, Iterable, Type

from silx.gui import qt


class TupleInputWidget(qt.QWidget):
    sigTupleChanged = qt.Signal()

    def __init__(
        self,
        placeHolderText: str = "Enter tuple, e.g. 0, 1, 2",
        Type: Type = int,
        parent: qt.QWidget | None = None,
    ):
        super().__init__(parent)

        self._tupleEdit = qt.QLineEdit()
        self._tupleEdit.installEventFilter(self)
        self._tupleEdit.setPlaceholderText(placeHolderText)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self._tupleEdit)
        layout.setContentsMargins(0, 0, 0, 0)

        self._type = Type
        self._tupleEdit.editingFinished.connect(self._validate)

    def _validate(self):
        try:
            _ = self.getValue()
        except Exception:
            self._tupleEdit.setStyleSheet("border: 1px solid red")
        else:
            self._tupleEdit.setStyleSheet("")
            self.sigTupleChanged.emit()

    def getValue(self) -> tuple:
        text = self._tupleEdit.text().strip()

        if not text:
            return tuple()

        try:
            return tuple(self._type(part) for part in text.split(",") if part.strip())
        except ValueError as e:
            raise ValueError(f"Input must be a tuple of {self._type.__name__}") from e

    def setValue(self, values: Iterable[Any]):
        self._tupleEdit.setText(",".join(str(value) for value in values))

    def eventFilter(self, obj, event):
        """Intercept and discard Enter/Return key presses for the LineEdit."""
        if obj is self._tupleEdit and event.type() == qt.QEvent.KeyPress:
            if event.key() in (qt.Qt.Key_Return, qt.Qt.Key_Enter):
                self._validate()
                # We return True to say 'we handled this event' (by doing nothing)
                # This prevents the Enter key from triggering buttons or editingFinished logic
                return True
        return super().eventFilter(obj, event)
