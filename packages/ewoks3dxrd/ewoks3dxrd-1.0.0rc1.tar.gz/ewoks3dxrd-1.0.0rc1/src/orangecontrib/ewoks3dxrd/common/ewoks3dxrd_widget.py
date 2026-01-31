from __future__ import annotations

import logging
from typing import Any, Callable

from ewoksorange.gui.orange_utils.settings import Setting
from ewoksorange.gui.owwidgets.meta import ow_build_opts
from ewoksorange.gui.owwidgets.threaded import OWEwoksWidgetOneThread
from silx.gui import qt
from silx.io.utils import DataUrl
from ewoks3dxrd.nexus.utils import group_exists
from silx.gui.plot.PlotWidget import PlotWidget

from .utils import format_exception, isPlotOnMainThread

_logger = logging.getLogger(__name__)


class Ewoks3DXRDWidget(OWEwoksWidgetOneThread, **ow_build_opts):
    want_main_area = True
    want_control_area = False
    resizing_enabled = True
    _ewoks3dxrd_output_data_url = Setting("", schema_only=True)

    # Implementation of a __post_init__ function
    # When a subclass is implemented, __init_subclass__ will be called and will wrap the __init__ with the init_decorator
    # This will allow __post_init__ to be called after the __init__ of the subclass instance (here called `subclass_init`)
    # Based on https://stackoverflow.com/a/72593763
    def __init_subclass__(cls, **kwargs):
        def init_decorator(subclass_init):
            def new_init(self, *args, **kwargs):
                subclass_init(self, *args, **kwargs)
                # This condition is needed in case of multiple subclass inheritance.
                # We want to call __post_init__ only for the last subclass in the hierarchy
                if type(self) is cls:
                    self.__post_init__()

            return new_init

        cls.__init__ = init_decorator(cls.__init__)

    def __post_init__(self):
        self._restoreDefaultInputs()
        self._restoreOutputDataUrlDisplay()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)

        self._splitter = qt.QSplitter(qt.Qt.Orientation.Horizontal)
        self._splitter.setSizes([300, 700])
        self.mainArea.layout().addWidget(self._splitter)
        self._input_getters: dict[str, Callable[..., Any]] = {}
        self._input_setters: dict[str, Callable[[Any], None]] = {}

    def registerInput(
        self, name: str, getter: Callable[..., Any], setter: Callable[[Any], None]
    ):
        """Registers an input so its value can be restored at start-up and used at execution"""
        self._input_getters[name] = getter
        self._input_setters[name] = setter

    def _restoreDefaultInputs(self):
        for name, setter in self._input_setters.items():
            try:
                value = self.get_default_input_value(name)
                if value is not None:
                    setter(value)
            except Exception as error:
                _logger.warning(
                    f"Default input restoration failed for {type(self)}.{name}. Cause: {format_exception(error)}"
                )
                self.set_default_input(name, None)
                _logger.warning(f"Default input of {type(self)}.{name} was cleared.")

    def addControlWidget(self, widget: qt.QWidget):
        self._splitter.insertWidget(0, widget)

    def addMainWidget(self, widget: qt.QWidget):
        self._splitter.insertWidget(1, widget)

    def execute_ewoks_task(self, log_missing_inputs=False):
        self._disableControls()
        try:
            self.update_default_inputs(
                **{name: getter() for name, getter in self._input_getters.items()}
            )
            super().execute_ewoks_task(log_missing_inputs)
        except Exception as e:
            self.showError(e)
            self._enableControls()

    def task_output_changed(self):
        super().task_output_changed()
        self._enableControls()
        if self.task_exception is not None:
            self.showError(self.task_exception)
            return

        self.handleSuccessfulExecution()

    def handleSuccessfulExecution(self):
        pass

    def showError(self, error: Exception, title: str | None = None):
        qt.QMessageBox.critical(
            self,
            f"{title if title else self.name} Error",
            format_exception(error),
        )

    def _disableControls(self):
        controlWidget = self._splitter.widget(0)
        if controlWidget:
            controlWidget.setDisabled(True)

    def _enableControls(self):
        controlWidget = self._splitter.widget(0)
        if controlWidget:
            controlWidget.setEnabled(True)

    def setOutputDataUrl(self, data_url: str):
        self._ewoks3dxrd_output_data_url = str(data_url)

    def getOutputDataUrl(self):
        return self._ewoks3dxrd_output_data_url

    def _restoreOutputDataUrlDisplay(self):
        url = self._ewoks3dxrd_output_data_url
        if not url:
            return
        data_url = DataUrl(url)
        nexus_file_path = data_url.file_path()
        data_group_path = data_url.data_path()
        if group_exists(filename=nexus_file_path, data_group_path=data_group_path):
            _logger.info(f"Restoring output visualization for {url}")
            self.displayOutputDataUrl()
        else:
            _logger.debug(f"Saved data url {url} not exist.")

    def displayOutputDataUrl(self):
        _logger.debug(
            f"Base Class display data url not implemented to produce results {self._ewoks3dxrd_output_data_url}"
        )

    def _logGuiPlotUpdate(self, actionName: str):
        guiOnMainThread, currentThreadId = isPlotOnMainThread()
        threadPtr = f"0x{int(currentThreadId):016x}"
        msg = f"[{self.name}] {actionName} | GUI Thread: {guiOnMainThread} | ThreadID: {threadPtr}"

        if not guiOnMainThread:
            _logger.debug(f"THREAD UPDATE: {msg}")
        else:
            _logger.debug(f"MAIN UPDATE: {msg}")

    def _onPlotEvent(self, event: dict):
        eventType = event.get("event")
        self._logGuiPlotUpdate(f"Event Type: {eventType}")

    def _logPlotEvents(self, plot: PlotWidget):
        plot.sigPlotSignal.connect(self._onPlotEvent)
