from __future__ import annotations

from ewokscore import missing_data
from silx.gui import qt


class ProcessNameLineEdit(qt.QLineEdit):

    def __init__(self, default: str, parent: qt.QWidget | None = None):
        super().__init__(parent)
        self.setPlaceholderText(default)
        self.label = "Output NeXus Group Name"
        self.setToolTip(
            f"Name of the NeXus group where data will be saved. Default: '{default}'"
        )

    def getText(self) -> str | missing_data.MissingData:
        value = self.text().strip()
        if value == "":
            return missing_data.MISSING_DATA
        return value

    def keyPressEvent(self, event):
        """
        Handles key press events for the widget.

        This method is overridden to prevent the 'Enter' or 'Return' key
        from propagating to parent widgets.

        The expected behavior is:
        - When the user presses 'Enter' or 'Return' inside this widget, it was consumed and not passed to
        any other widget
        - Other key presses are passed to the default handler to ensure
        """

        if event.key() == qt.Qt.Key.Key_Enter or event.key() == qt.Qt.Key.Key_Return:
            event.accept()
        else:
            super().keyPressEvent(event)
