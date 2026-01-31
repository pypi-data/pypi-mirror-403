from __future__ import annotations
from silx.gui import qt


class FilenameCompleterLineEdit(qt.QLineEdit):
    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)

        completer = qt.QCompleter()
        model = qt.QFileSystemModel(completer)
        model.setOption(qt.QFileSystemModel.Option.DontWatchForChanges, True)
        model.setRootPath(qt.QDir.rootPath())

        completer.setModel(model)
        completer.setCompletionRole(qt.QFileSystemModel.Roles.FileNameRole)
        self.setCompleter(completer)
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == qt.QtCore.QEvent.Type.ToolTip and self.text():
            qt.QToolTip.showText(event.globalPos(), self.text(), self)
            return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        """
        Handles key press events for the widget.

        This method is overridden to prevent the 'Enter' or 'Return' key
        from propagating to parent widgets (like Browse button in MasterFileWidget).

        The expected behavior is:
        - When the user presses 'Enter' or 'Return' inside this widget, it was consumed and not passed to
        any other widget
        - Other key presses are passed to the default handler to ensure
        """

        if event.key() == qt.Qt.Key.Key_Enter or event.key() == qt.Qt.Key.Key_Return:
            event.accept()
        else:
            super().keyPressEvent(event)
