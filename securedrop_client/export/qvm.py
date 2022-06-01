import logging
import subprocess
from enum import Enum
from shlex import quote

logger = logging.getLogger(__name__)


class QVM:
    """A Python interface for the Qubes OS qvm command-line tool."""

    class Status(Enum):
        # On the way to success
        USB_CONNECTED = "USB_CONNECTED"
        DISK_ENCRYPTED = "USB_ENCRYPTED"

        # Not too far from success
        USB_NOT_CONNECTED = "USB_NOT_CONNECTED"
        BAD_PASSPHRASE = "USB_BAD_PASSPHRASE"

        # Failure
        DISK_ENCRYPTION_NOT_SUPPORTED_ERROR = "USB_ENCRYPTION_NOT_SUPPORTED"
        ERROR_USB_CONFIGURATION = "ERROR_USB_CONFIGURATION"
        UNEXPECTED_RETURN_VALUE = "Unexpected!"
        PRINTER_NOT_FOUND = "ERROR_PRINTER_NOT_FOUND"
        MISSING_PRINTER_URI = "ERROR_MISSING_PRINTER_URI"

        SUBPROCESS_ERROR = "CALLED_PROCESS_ERROR"

    @classmethod
    def open_in_export_vm(cls, unsafe_file_path: str) -> Status:
        """Send a file to the export VM (sd-devices)."""

        # There are already talks of switching to a QVM-RPC implementation for unlocking devices
        # and exporting files, so it's important to remember to shell-escape what we pass to the
        # shell, even if for the time being we're already protected against shell injection via
        # Python's implementation of subprocess, see
        # https://docs.python.org/3/library/subprocess.html#security-considerations
        file_path = quote(unsafe_file_path)

        try:
            output = subprocess.check_output(
                ["qvm-open-in-vm", "sd-devices", file_path, "--view-only"],
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            logger.debug(f"Export subprocess failed: {e}")
            return QVM.Status.SUBPROCESS_ERROR

        try:
            status = QVM.Status(output.decode("utf-8").strip())
        except ValueError as e:
            logger.debug(f"Export subprocess returned unexpected value: {e}")
            status = QVM.Status.UNEXPECTED_RETURN_VALUE

        return status
