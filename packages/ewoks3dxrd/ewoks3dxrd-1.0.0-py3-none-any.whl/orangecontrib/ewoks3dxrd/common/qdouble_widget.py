from silx.gui import qt


class QDoubleWidget(qt.QDoubleSpinBox):
    def __init__(
        self,
        unit: str,
        step: float,
        decimals: int,
        minimum: float,
        maximum: float,
        toolTip: str,
        parent=None,
    ):
        super().__init__(
            parent,
        )
        self.setSuffix(f" {unit}")
        self.setRange(minimum, maximum)
        self.setDecimals(decimals)
        self.setSingleStep(step)
        self.setToolTip(toolTip)

    def wheelEvent(self, event: qt.QWheelEvent) -> None:
        event.ignore()
