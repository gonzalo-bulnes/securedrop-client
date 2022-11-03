from typing import NewType

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from securedrop_client import export
from securedrop_client.logic import Controller


class Printer(QObject):

    status_changed = pyqtSignal()
    job_done = pyqtSignal(str)
    job_failed = pyqtSignal(str, str)

    _printer_start_requested = pyqtSignal()
    _job_enqueuing_requested = pyqtSignal(list)

    Status = NewType("Status", str)
    StatusUnknown = Status("unknown-sf5fd")
    StatusReady = Status("ready-83jf3")
    StatusUnreachable = Status("unreachable-120a0")
    # TODO StatusBusy = Status("busy-4bf83")

    def __init__(self, controller: Controller, export_service: export.Service) -> None:
        super().__init__()

        self._status = self.StatusUnknown

        # The API of the export service is awkward,
        # please bear with me!
        export_service.connect_signals(
            print_preflight_check_requested=self._printer_start_requested,
            print_requested=self._job_enqueuing_requested,
        )

        export_service.printer_preflight_failure.connect(self._on_printer_not_found_ready)
        export_service.printer_preflight_success.connect(self._on_printer_found_ready)
        export_service.print_call_failure.connect(self._on_job_enqueuing_failed)
        export_service.print_call_success.connect(self._on_job_enqueued)

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, new: Status) -> None:
        if new != self._status:
            self._status = new
            self.status_changed.emit()

    def start_on(self, signal: pyqtSignal) -> None:
        """Allow printer to be started in a thread-safe manner."""
        signal.connect(self._start)

    def enqueue_job_on(self, signal: pyqtSignal) -> None:
        signal.connect(self._enqueue_job)

    @pyqtSlot()
    def _start(self) -> None:
        """Ensure the physical printer is ready."""
        self._printer_start_requested.emit()

    @pyqtSlot(str, str)
    def _enqueue_job(self, id: str, file_name: str) -> None:
        """Send a printing job to the print queue."""
        self._job_enqueuing_requested.emit([file_name])

    @pyqtSlot()
    def _on_job_enqueued(self) -> None:
        self.job_done.emit("unknown job ID")  # FIXME

    @pyqtSlot(object)
    def _on_job_enqueuing_failed(self, error: export.ExportError) -> None:
        reason = str(error)  # FIXME check the output
        self.job_failed.emit("unknown job ID", reason)  # FIXME

    @pyqtSlot()
    def _on_printer_found_ready(self) -> None:
        self.status = self.StatusReady

    @pyqtSlot(object)
    def _on_printer_not_found_ready(self, reason: object) -> None:
        self.status = self.StatusUnreachable
