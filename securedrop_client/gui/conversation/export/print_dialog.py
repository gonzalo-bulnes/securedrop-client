import time
from gettext import gettext as _
from typing import Optional

from PyQt5.QtCore import QSize, pyqtSlot

from securedrop_client.export import ExportError, ExportStatus
from securedrop_client.gui.base import ModalDialog, SecureQLabel

from .device import Device, Printer


class ConfirmationDialog(ModalDialog):

    FILENAME_WIDTH_PX = 260

    def __init__(self, printer: Printer, file_name: str) -> None:
        super().__init__()

        self._printer = printer
        self._printer.status_changed.connect(self._on_printer_status_changed)

        self.continue_button.setText("PRINT")
        self.continue_button.clicked.connect(
            self.accept
        )  # FIXME The ModalDialog is more complex than needed to do this.

        file_name = SecureQLabel(
            file_name, wordwrap=False, max_length=self.FILENAME_WIDTH_PX
        ).text()  # FIXME This seems like a heavy way to sanitize a string.
        header = _("Print:<br />" '<span style="font-weight:normal">{}</span>').format(file_name)
        body = _(
            "<h2>Managing printout risks</h2>"
            "<b>QR codes and web addresses</b>"
            "<br />"
            "Never type in and open web addresses or scan QR codes contained in printed "
            "documents without taking security precautions. If you are unsure how to "
            "manage this risk, please contact your administrator."
            "<br /><br />"
            "<b>Printer dots</b>"
            "<br />"
            "Any part of a printed page may contain identifying information "
            "invisible to the naked eye, such as printer dots. Please carefully "
            "consider this risk when working with or publishing scanned printouts."
        )

        self.header.setText(header)
        self.header_icon.update_image("printer.svg", svg_size=QSize(64, 64))
        self.body.setText(body)
        self.adjustSize()

        self._body = body

        self._on_printer_status_changed()

    @pyqtSlot()
    def _on_printer_status_changed(self) -> None:
        printer_status = self._printer.status
        if printer_status == Printer.StatusUnknown:
            self._on_printer_status_unknown()
        elif printer_status == Printer.StatusReady:
            self._on_printer_ready()
        elif printer_status == Printer.StatusUnreachable:
            self._on_printer_unreachable()
        else:  # Printer.StatusBusy
            self._on_printer_busy()

    def _on_printer_status_unknown(self) -> None:
        self.continue_button.setEnabled(False)
        self.printer_start_requested.emit()

        status = "<i>Waiting for printer status to be known...</i>"
        self.body.setText("<br /><br />".join([self._body, status]))
        self.adjustSize()

    def _on_printer_ready(self) -> None:
        self.continue_button.setEnabled(True)

        self.body.setText(self._body)
        self.adjustSize()

    def _on_printer_unreachable(self) -> None:
        self.continue_button.setEnabled(False)

        status = "<i>Printer unreachable, please verify it's connected.</i>"
        self.body.setText("<br /><br />".join([self._body, status]))
        self.adjustSize()

    def _on_printer_busy(self) -> None:
        self.continue_button.setEnabled(False)

        status = "<i>Printer busy, please wait a moment...</i>"
        self.body.setText("<br /><br />".join([self._body, status]))
        self.adjustSize()


class ErrorDialog(ModalDialog):

    FILENAME_WIDTH_PX = 260

    def __init__(self, file_name: str, reason: str) -> None:
        super().__init__()

        self.continue_button.clicked.connect(
            self.accept
        )  # FIXME The ModalDialog is more complex than needed to do this.

        file_name = SecureQLabel(
            file_name, wordwrap=False, max_length=self.FILENAME_WIDTH_PX
        ).text()  # FIXME This seems like a heavy way to sanitize a string.
        reason = SecureQLabel(
            reason, wordwrap=False, max_length=self.FILENAME_WIDTH_PX
        ).text()  # FIXME This seems like a heavy way to sanitize a string.
        header = _("Printing failed<br />" '<span style="font-weight:normal">{}</span>').format(file_name)

        self.header.setText(header)
        self.header_icon.update_image("printer.svg", svg_size=QSize(64, 64))
        self.body.setText(reason)
        self.adjustSize()


class PrintDialog(ModalDialog):

    FILENAME_WIDTH_PX = 260

    def __init__(self, device: Device, file_uuid: str, file_name: str) -> None:
        super().__init__()

        self._device = device
        self.file_uuid = file_uuid
        self.file_name = SecureQLabel(
            file_name, wordwrap=False, max_length=self.FILENAME_WIDTH_PX
        ).text()
        # Hold onto the error status we receive from the Export VM
        self.error_status: Optional[ExportStatus] = None

        # Connect device signals to slots
        self._device.print_preflight_check_succeeded.connect(
            self._on_print_preflight_check_succeeded
        )
        self._device.print_preflight_check_failed.connect(self._on_print_preflight_check_failed)

        # Connect parent signals to slots
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self._run_preflight)

        # Dialog content
        self.starting_header = _(
            "Preparing to print:<br />" '<span style="font-weight:normal">{}</span>'
        ).format(self.file_name)
        self.ready_header = _(
            "Ready to print:<br />" '<span style="font-weight:normal">{}</span>'
        ).format(self.file_name)
        self.insert_usb_header = _("Connect USB printer")
        self.error_header = _("Printing failed")
        self.starting_message = _(
            "<h2>Managing printout risks</h2>"
            "<b>QR codes and web addresses</b>"
            "<br />"
            "Never type in and open web addresses or scan QR codes contained in printed "
            "documents without taking security precautions. If you are unsure how to "
            "manage this risk, please contact your administrator."
            "<br /><br />"
            "<b>Printer dots</b>"
            "<br />"
            "Any part of a printed page may contain identifying information "
            "invisible to the naked eye, such as printer dots. Please carefully "
            "consider this risk when working with or publishing scanned printouts."
        )
        self.insert_usb_message = _("Please connect your printer to a USB port.")
        self.generic_error_message = _("See your administrator for help.")

        self._show_starting_instructions()
        self.start_animate_header()
        self._run_preflight()

    def _show_starting_instructions(self) -> None:
        self.header.setText(self.starting_header)
        self.body.setText(self.starting_message)
        self.error_details.hide()
        self.adjustSize()

    def _show_insert_usb_message(self) -> None:
        self.continue_button.clicked.disconnect()
        self.continue_button.clicked.connect(self._run_preflight)
        self.header.setText(self.insert_usb_header)
        self.body.setText(self.insert_usb_message)
        self.error_details.hide()
        self.adjustSize()

    def _show_generic_error_message(self) -> None:
        self.continue_button.clicked.disconnect()
        self.continue_button.clicked.connect(self.close)
        self.continue_button.setText(_("DONE"))
        self.header.setText(self.error_header)
        self.body.setText(  # nosemgrep: semgrep.untranslated-gui-string
            "{}: {}".format(self.error_status, self.generic_error_message)
        )
        self.error_details.hide()
        self.adjustSize()

    @pyqtSlot()
    def _run_preflight(self) -> None:
        self._device.run_printer_preflight_checks()

    @pyqtSlot()
    def _print_file(self) -> None:
        self._device.print_file(self.file_uuid)
        self.close()

    @pyqtSlot()
    def _on_print_preflight_check_succeeded(self) -> None:
        # If the continue button is disabled then this is the result of a background preflight check
        self.stop_animate_header()
        self.header_icon.update_image("printer.svg", svg_size=QSize(64, 64))
        self.header.setText(self.ready_header)
        if not self.continue_button.isEnabled():
            self.continue_button.clicked.disconnect()
            self.continue_button.clicked.connect(self._print_file)
            self.continue_button.setEnabled(True)
            self.continue_button.setFocus()
            return

        self._print_file()

    @pyqtSlot(object)
    def _on_print_preflight_check_failed(self, error: ExportError) -> None:
        self.stop_animate_header()
        self.header_icon.update_image("printer.svg", svg_size=QSize(64, 64))
        self.error_status = error.status
        # If the continue button is disabled then this is the result of a background preflight check
        if not self.continue_button.isEnabled():
            self.continue_button.clicked.disconnect()
            if error.status == ExportStatus.PRINTER_NOT_FOUND:
                self.continue_button.clicked.connect(self._show_insert_usb_message)
            else:
                self.continue_button.clicked.connect(self._show_generic_error_message)

            self.continue_button.setEnabled(True)
            self.continue_button.setFocus()
        else:
            if error.status == ExportStatus.PRINTER_NOT_FOUND:
                self._show_insert_usb_message()
            else:
                self._show_generic_error_message()
