from __future__ import annotations
import logging
import threading
import subprocess
from typing import Optional, Tuple, IO, Any

_logger = logging.getLogger(__name__)


class SubprocessTaskMixin:
    """
    SubprocessTaskMixin: Handles the subprocess and threading signal mechanism within Ewoks3DXRD tasks
    """

    def init_sub_process_attributes(self):
        self._proc: Optional[subprocess.Popen] = None
        self._init_event = threading.Event()
        self._proc_lock = threading.Lock()

    def get_proc_stdout_stderr(self) -> Tuple[Optional[IO[Any]], Optional[IO[Any]]]:
        with self._proc_lock:
            if self._proc:
                return self._proc.stdout, self._proc.stderr
        return None, None

    def _close_streams(self):
        if self._proc is None:
            return
        try:
            if self._proc.stdout:
                self._proc.stdout.close()
            if self._proc.stderr:
                self._proc.stderr.close()
        except Exception as e:
            _logger.debug(f"Error closing streams: {e}")
        _logger.debug("Subprocess streams closed.")

    def get_task_init_event(self) -> threading.Event:
        return self._init_event

    def _start_subprocess(self, start_func, *args, **kwargs):
        self._init_event.clear()
        result = start_func(*args, **kwargs)

        with self._proc_lock:
            self._proc = result[0]

        self._init_event.set()
        return result

    def stop(self, timeout=0.1):
        with self._proc_lock:
            if self._proc and self._proc.poll() is None:
                _logger.info(f"Terminating subprocess {self._proc.pid}")
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    _logger.warning("Timeout expired. Killing.")
                    self._proc.kill()

            self._close_streams()
            self._proc = None
            self._init_event.clear()

    def cancel(self):
        _logger.info("Cancellation requested for GridIndexGrainsSubProcess")
        self.stop(timeout=0.1)
