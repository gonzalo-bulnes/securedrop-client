import unittest
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtTest import QSignalSpy

from securedrop_client import export
from securedrop_client.gui.conversation import Printer
from securedrop_client.logic import Controller


class Consumer(QObject):

    signal = pyqtSignal()
    str_str_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()


class TestPrinterPublicAPI(unittest.TestCase):
    def test_status_is_unknown_by_default(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        self.assertEqual(printer.status, Printer.StatusUnknown)

    @patch.object(export.Service, "run_printer_preflight")
    def test_start_on_allows_to_run_preflight_checks_on_arbitrary_signal(self, _):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        example = Consumer()
        printer.start_on(example.signal)

        example.signal.emit()

        export_service.run_printer_preflight.assert_called_once()

    @patch.object(export.Service, "print")
    def test_enqueue_job_on_allows_to_run_preflight_checks_on_arbitrary_signal(self, _):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        example = Consumer()
        printer.enqueue_job_on(example.str_str_signal)

        example.str_str_signal.emit("one", "two")

        export_service.print.assert_called_once()

    def test_job_done_signal_is_defined(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        printer.job_done.emit("some job ID")
        assert True  # No exceptions were raised.

    def test_job_failed_signal_is_defined(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        printer.job_failed.emit("some job ID", "some failure reason")
        assert True  # No exceptions were raised.


class TestPrinterInterfaceWithExportService(unittest.TestCase):
    def test_status_is_updated_on_export_service_success_signal(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        export_service.printer_preflight_success.emit()

        self.assertEqual(printer.status, Printer.StatusReady)

    def test_status_is_updated_on_export_service_failure_signal(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        reason = export.ExportError(export.ExportStatus.PRINTER_NOT_FOUND)

        export_service.printer_preflight_failure.emit(reason)

        self.assertEqual(printer.status, Printer.StatusUnreachable)

    def test_job_done_signal_is_emitted_on_export_service_success_signal(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        job_done_emissions = QSignalSpy(printer.job_done)

        export_service.print_call_success.emit()

        self.assertTrue(job_done_emissions.isValid())
        self.assertEqual(len(job_done_emissions), 1)

    def test_job_failed_signal_is_emitted_on_export_service_failure_signal(self):
        controller = MagicMock(spec=Controller)
        export_service = export.Service()
        printer = Printer(controller, export_service)

        job_failed_emissions = QSignalSpy(printer.job_failed)

        reason = export.ExportError(export.ExportStatus.CALLED_PROCESS_ERROR)

        export_service.print_call_failure.emit(reason)

        self.assertTrue(job_failed_emissions.isValid())
        self.assertEqual(len(job_failed_emissions), 1)
