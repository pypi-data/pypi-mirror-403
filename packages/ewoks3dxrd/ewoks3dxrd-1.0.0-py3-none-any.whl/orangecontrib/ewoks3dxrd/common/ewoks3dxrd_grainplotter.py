from __future__ import annotations

import logging
import os
import time
from typing import Optional

from ewoksorange.gui.owwidgets.meta import ow_build_opts
from silx.gui import qt

from ..common.log_streamer import LogStreamer
from ..common.log_widget import LogWidget
from ..indexer.constants import (
    LOG_INACTIVITY_TIMEOUT_SEC,
    MONITOR_INTERVAL_M_SEC,
    PLOT_GRAIN_UPDATE_TIME_M_SEC,
)
from .ewoks3dxrd_widget import Ewoks3DXRDWidget

_logger = logging.getLogger(__name__)


class GrainUpdateNotifier(qt.QObject):
    hasNewGrainData = qt.Signal(str)


class Ewoks3DXRDGrainPlotter(Ewoks3DXRDWidget, **ow_build_opts):
    """
    Handles Log Streamers, Subprocess Monitoring, and Live Grain Plotting.
    """

    def __init__(self):
        super().__init__()

    def initLogProcessManager(self):
        self._logWindow = LogWidget(title=f"{self.name} logs", parent=self)
        self._logWindow.sigTerminateRequested.connect(self._handleSubprocessTerminate)

        self._stdoutStreamer: Optional[LogStreamer] = None
        self._stderrStreamer: Optional[LogStreamer] = None

        self._monitorTimer = qt.QTimer(self)
        self._monitorTimer.setInterval(MONITOR_INTERVAL_M_SEC)
        self._monitorTimer.timeout.connect(self._monitorSubprocessActivity)

        self._grainUpdateTimer = qt.QTimer(self)
        self._grainUpdateTimer.timeout.connect(self._checkNewGrainData)
        self._grainNotifier = GrainUpdateNotifier()
        self._grainNotifier.hasNewGrainData.connect(self._plotGrainsUpdate)

        self._showLogAction = qt.QAction("Show Log", self)
        self._showLogAction.triggered.connect(self._logWindow.show)
        if hasattr(self, "menuBar"):
            self.menuBar().setEnabled(True)
            self.menuBar().addAction(self._showLogAction)

        _logger.debug("LogProcessManagerMixIn Initialized")

    def _cleanupLogging(self):
        self.grainTimerStop()
        self._monitorTimer.stop()
        if self._stdoutStreamer:
            self._stdoutStreamer.stop()
            self._stdoutStreamer = None
            _logger.debug(
                "LogProcessManagerMixIn _cleanupLogging stopped stdout Streamer"
            )
        if self._stderrStreamer:
            self._stderrStreamer.stop()
            self._stderrStreamer = None
            _logger.debug(
                "LogProcessManagerMixIn _cleanupLogging stopped stderr Streamer"
            )
        if self._logWindow.isVisible():
            self._logWindow.close()
        _logger.debug(
            "LogProcessManagerMixIn _cleanupLogging closed logWindow, stopped timer"
        )

    def _setupLogging(self, stdoutLabel="Stdout", stderrLabel="Stderr"):
        self._cleanupLogging()
        task = self.task_executor.current_task
        if not task:
            _logger.info(
                "LogProcessManagerMixIn _setupLogging found no current_task in the task_executor to setup"
            )
            return

        stdout, stderr = task.get_proc_stdout_stderr()
        if stdout:
            self._stdoutStreamer = LogStreamer(stdout, stdoutLabel)
            self._stdoutStreamer.logReceived.connect(self._logWindow.appendLog)
            self._stdoutStreamer.start()
            _logger.debug(
                "LogProcessManagerMixIn _setupLogging started stdout Streamer"
            )

        if stderr:
            self._stderrStreamer = LogStreamer(stderr, stderrLabel)
            self._stderrStreamer.logReceived.connect(self._logWindow.appendLog)
            self._stderrStreamer.start()
            _logger.debug(
                "LogProcessManagerMixIn _setupLogging started stderr Streamer"
            )

        self._logWindow.setLastLogTime(time.time())
        self._logWindow.show()
        self._monitorTimer.start()
        _logger.debug(
            "LogProcessManagerMixIn _setupLogging started monitorTimer, logWindow, streamer IO"
        )

    def _handleSubprocessTerminate(self):
        self._cleanupLogging()
        self.grainTimerStop()
        if self.task_executor.current_task:
            self.task_executor.cancel_running_task()
            self._enableControls()

    def _monitorSubprocessActivity(self):
        if not self.task_executor.isRunning():
            _logger.debug(
                "LogProcessManagerMixIn _monitorSubprocessActivity no running task Executor"
            )
            self._monitorTimer.stop()
            return

        if time.time() - self._logWindow.getLastLogTime() > LOG_INACTIVITY_TIMEOUT_SEC:
            self._logWindow.appendLog(
                f"No log activity for {LOG_INACTIVITY_TIMEOUT_SEC}s. Terminating subprocess...",
                "WARNING",
            )
            self.task_executor.current_task.stop()
            _logger.debug(
                "LogProcessManagerMixIn _monitorSubprocessActivity no activity, stopped the current_task"
            )

    def grainTimerStart(self):
        self._grainUpdateTimer.start(PLOT_GRAIN_UPDATE_TIME_M_SEC)

    def grainTimerStop(self):
        self._grainUpdateTimer.stop()

    def _checkNewGrainData(self):
        task = getattr(self.task_executor, "current_task", None)
        if not task:
            return

        path = self.task_executor.current_task.get_grain_file()
        if not path or not os.path.isfile(path):
            return

        try:
            self._grainNotifier.hasNewGrainData.emit(path)
        except OSError as e:
            _logger.error(f"Error checking grain file: {e}")

    @qt.Slot(str)
    def _plotGrainsUpdate(self, _: str):
        raise NotImplementedError("Base class: not implemented")
