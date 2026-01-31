from __future__ import annotations
from typing import Optional
from silx.gui import qt
import threading
import io


class LogStreamer(qt.QObject):
    logReceived = qt.Signal(str, str)

    def __init__(self, pipe: Optional[io.TextIOWrapper], label: str):
        super().__init__()
        self.pipe = pipe
        self.label = label
        self._stopEvent = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stopEvent.is_set() and self.pipe:
            try:
                line = self.pipe.readline()
                if not line:
                    break

                self.logReceived.emit(line.rstrip(), self.label)
            except (IOError, ValueError, AttributeError):
                break
            except Exception as e:
                self.logReceived.emit(f"Error decoding log: {e}", "ERROR")

    def start(self):
        self._thread.start()

    def stop(self):
        self._stopEvent.set()
        if self.pipe:
            self.pipe.close()
        if self._thread.is_alive():
            self._thread.join(timeout=0.1)
