import os
from contextlib import contextmanager

from PyQt5.QtCore import QThread
from PyQt5.QtTest import QSignalSpy

from securedrop_client.export import Export as ExportService
from securedrop_client.gui.conversation.export import Device
from securedrop_client.logic import Controller
from tests import factory


@contextmanager
def thread():
    """Ensures that the thread is properly closed before its reference is dropped."""
    # See https://github.com/pytest-dev/pytest-qt/issues/276
    thread = QThread()
    yield thread
    thread.exit()
    # In theory, we could wait on the thread's finished() signal,
    # but that seems currently broken in pytest, see:
    # https://doc.qt.io/archives/qt-5.11/qsignalspy.html#wait
    # and https://github.com/pytest-dev/pytest-qt/issues/199#issuecomment-366518687
    # Sleeping for a bit, although inelegant, does the trick.
    thread.msleep(10)


def test_Device_run_printer_preflight_checks(homedir, mocker, session, source):
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        print_preflight_check_requested_emissions = QSignalSpy(
            device.print_preflight_check_requested
        )

        device.run_printer_preflight_checks()

        assert len(print_preflight_check_requested_emissions) == 1


def test_Device_run_printer_preflight_checks_not_qubes(homedir, mocker, session, source):
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        print_preflight_check_requested_emissions = QSignalSpy(
            device.print_preflight_check_requested
        )
        print_preflight_check_succeeded_emissions = QSignalSpy(
            device.print_preflight_check_succeeded
        )

        device.run_printer_preflight_checks()

        assert len(print_preflight_check_requested_emissions) == 0
        assert len(print_preflight_check_succeeded_emissions) == 1


def test_Device_run_print_file(mocker, session, homedir):
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        device._export_service = mocker.MagicMock(spec=ExportService)
        print_requested_emissions = QSignalSpy(device.print_requested)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        filepath = file.location(controller.data_dir)
        os.makedirs(os.path.dirname(filepath), mode=0o700, exist_ok=True)
        with open(filepath, "w"):
            pass

        device.print_file(file.uuid)

        assert len(print_requested_emissions) == 1


def test_Device_run_print_file_not_qubes(mocker, session, homedir):
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        print_requested_emissions = QSignalSpy(device.print_requested)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        filepath = file.location(controller.data_dir)
        os.makedirs(os.path.dirname(filepath), mode=0o700, exist_ok=True)
        with open(filepath, "w"):
            pass

        device.print_file(file.uuid)

        assert len(print_requested_emissions) == 0


def test_Device_print_file_file_missing(homedir, mocker, session, session_maker):
    """
    If the file is missing from the data dir, is_downloaded should be set to False and the failure
    should be communicated to the user.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)
        warning_logger = mocker.patch("securedrop_client.logic.logger.warning")

        device.print_file(file.uuid)

        log_msg = "Cannot find file in {}. File does not exist.".format(
            os.path.dirname(file.filename)
        )
        warning_logger.assert_called_once_with(log_msg)


def test_Device_print_file_file_missing_not_qubes(homedir, mocker, session, session_maker):
    """
    If the file is missing from the data dir, is_downloaded should be set to False and the failure
    should be communicated to the user.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)
        warning_logger = mocker.patch("securedrop_client.logic.logger.warning")

        device.print_file(file.uuid)

        log_msg = "Cannot find file in {}. File does not exist.".format(
            os.path.dirname(file.filename)
        )
        warning_logger.assert_called_once_with(log_msg)


def test_Device_print_file_when_orig_file_already_exists(
    homedir, config, mocker, session, session_maker, source
):
    """
    The signal `print_requested` should still be emmited if the original file already exists.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        file = factory.File(source=factory.Source())
        device._export_service = mocker.MagicMock(spec=ExportService)
        print_requested_emissions = QSignalSpy(device.print_requested)
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)
        mocker.patch("os.path.exists", return_value=True)

        device.print_file(file.uuid)

        assert len(print_requested_emissions) == 1
        controller.get_file.assert_called_with(file.uuid)


def test_Device_print_file_when_orig_file_already_exists_not_qubes(
    homedir, config, mocker, session, session_maker, source
):
    """
    The signal `print_requested` should still be emmited if the original file already exists.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        print_requested_emissions = QSignalSpy(device.print_requested)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        filepath = file.location(controller.data_dir)
        os.makedirs(os.path.dirname(filepath), mode=0o700, exist_ok=True)
        with open(filepath, "w"):
            pass

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        assert len(print_requested_emissions) == 0
        controller.get_file.assert_called_with(file.uuid)
        controller.get_file.assert_called_with(file.uuid)


def test_Device_run_export_preflight_checks(homedir, mocker, session, source):
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        device._export_service = mocker.MagicMock(spec=ExportService)
        export_preflight_check_requested_emissions = QSignalSpy(
            device.export_preflight_check_requested
        )
        file = factory.File(source=source["source"])
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        device.run_export_preflight_checks()

        assert len(export_preflight_check_requested_emissions) == 1


def test_Device_run_export_preflight_checks_not_qubes(homedir, mocker, session, source):
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        export_preflight_check_requested_emissions = QSignalSpy(
            device.export_preflight_check_requested
        )
        export_preflight_check_succeeded_emissions = QSignalSpy(
            device.export_preflight_check_succeeded
        )
        file = factory.File(source=source["source"])
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        device.run_export_preflight_checks()

        assert len(export_preflight_check_requested_emissions) == 0
        assert len(export_preflight_check_succeeded_emissions) == 1


def test_Device_export_file_to_usb_drive(homedir, mocker, session):
    """
    The signal `export_requested` should be emmited during export_file_to_usb_drive.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        device._export_service = mocker.MagicMock(spec=ExportService)
        export_requested_emissions = QSignalSpy(device.export_requested)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        filepath = file.location(controller.data_dir)
        os.makedirs(os.path.dirname(filepath), mode=0o700, exist_ok=True)
        with open(filepath, "w"):
            pass

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        assert len(export_requested_emissions) == 1


def test_Device_export_file_to_usb_drive_not_qubes(homedir, mocker, session):
    """
    The signal `export_requested` should be emmited during export_file_to_usb_drive.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        export_requested_emissions = QSignalSpy(device.export_requested)
        device._export_service = mocker.MagicMock(spec=ExportService)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        filepath = file.location(controller.data_dir)
        os.makedirs(os.path.dirname(filepath), mode=0o700, exist_ok=True)
        with open(filepath, "w"):
            pass

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        device._export_service.send_file_to_usb_device.assert_not_called()
        assert len(export_requested_emissions) == 0


def test_Device_export_file_to_usb_drive_file_missing(homedir, mocker, session, session_maker):
    """
    If the file is missing from the data dir, is_downloaded should be set to False and the failure
    should be communicated to the user.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)
        warning_logger = mocker.patch("securedrop_client.logic.logger.warning")

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        log_msg = "Cannot find file in {}. File does not exist.".format(
            os.path.dirname(file.filename)
        )
        warning_logger.assert_called_once_with(log_msg)


def test_Device_export_file_to_usb_drive_file_missing_not_qubes(
    homedir, mocker, session, session_maker
):
    """
    If the file is missing from the data dir, is_downloaded should be set to False and the failure
    should be communicated to the user.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)
        warning_logger = mocker.patch("securedrop_client.logic.logger.warning")

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        log_msg = "Cannot find file in {}. File does not exist.".format(
            os.path.dirname(file.filename)
        )
        warning_logger.assert_called_once_with(log_msg)


def test_Device_export_file_to_usb_drive_when_orig_file_already_exists(
    homedir, config, mocker, session, session_maker, source
):
    """
    The signal `export_requested` should still be emmited if the original file already exists.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        device._export_service = mocker.MagicMock(spec=ExportService)
        export_requested_emissions = QSignalSpy(device.export_requested)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)
        mocker.patch("os.path.exists", return_value=True)

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        assert len(export_requested_emissions) == 1
        controller.get_file.assert_called_with(file.uuid)


def test_Device_export_file_to_usb_drive_when_orig_file_already_exists_not_qubes(
    homedir, config, mocker, session, session_maker, source
):
    """
    The signal `export_requested` should still be emmited if the original file already exists.
    """
    gui = mocker.MagicMock()
    controller = Controller("http://localhost/", gui, session, homedir, None)
    with thread() as export_service_thread:
        device = Device(controller, export_service_thread)
        controller.qubes = False
        controller.data_dir = ""
        export_requested_emissions = QSignalSpy(device.export_requested)
        file = factory.File(source=factory.Source())
        session.add(file)
        session.commit()
        mocker.patch("securedrop_client.logic.Controller.get_file", return_value=file)

        filepath = file.location(controller.data_dir)
        os.makedirs(os.path.dirname(filepath), mode=0o700, exist_ok=True)
        with open(filepath, "w"):
            pass

        device.export_file_to_usb_drive(file.uuid, "mock passphrase")

        assert len(export_requested_emissions) == 0
        controller.get_file.assert_called_with(file.uuid)
