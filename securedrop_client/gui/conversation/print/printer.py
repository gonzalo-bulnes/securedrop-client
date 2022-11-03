import random
from typing import NewType

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from securedrop_client import export
from securedrop_client.logic import Controller


class Printer(QObject):

    status_changed = pyqtSignal()
    job_done = pyqtSignal(str)
    job_failed = pyqtSignal(str, str)

    Status = NewType("Status", str)
    StatusUnknown = Status("unknown-sf5fd")
    StatusReady = Status("ready-83jf3")
    StatusUnreachable = Status("unreachable-120a0")
    StatusBusy = Status("busy-4bf83")

    def __init__(self, controller: Controller, export_service: export.Service) -> None:
        super().__init__()

        self._status = self.StatusUnknown

    @property
    def status(self) -> Status:
        return self._status

    def start_on(self, signal: pyqtSignal) -> None:
        """Allow printer to be started in a thread-safe manner."""
        signal.connect(self._start)

    def enqueue_job_on(self, signal: pyqtSignal) -> None:
        signal.connect(self._enqueue_job)

    @pyqtSlot()
    def _start(self) -> None:
        """Ensure the physical printer is ready."""
        status = random.choice(
            [self.StatusReady, self.StatusBusy, self.StatusUnreachable]
        )  # FIXME Get status from CLI
        print(f"Started printer, status: {status}")
        if status != self._status:
            self._status = status
            self.status_changed.emit()

    @pyqtSlot(str, str)
    def _enqueue_job(self, id: str, file_name: str) -> None:
        """Send a printing job to the physical printer."""

        try:
            pass  # FIXME Enqueue job via CLI
            print(f"Job enqueued ({id})")
            if random.choice([True, False]):
                raise Exception
        except:  # noqa: E722
            print(f"Job failed ({id})")
            reason = "FIXME"  # FIXME Get failure reason form CLI
            self.job_failed.emit(id, reason)
            return

        print(f"Job suceeded ({id})")
        self.job_done.emit(id)
