import logging
import os
from typing import NewType

from PyQt5.QtCore import QObject, QState, QStateMachine, pyqtSignal
from PyQt5.QtWidgets import QWidget

from securedrop_client import export
from securedrop_client.logic import Controller

logger = logging.getLogger(__name__)


class _State(QWidget):
    """
    Paste the following state chart in https://mermaid.live for
    a visual representation of the behavior implemented by this class!

    stateDiagram-v2
      [*] --> unknown
      unknown --> unlocked: found_unlocked
      unknown --> locked: found_locked
      unknown --> missing: not_found

      missing --> unlocked: found_unlocked
      missing --> locked: found_locked

      locked --> missing: not_found
      unlocked --> missing: not_found

      state locked {
        [*] --> resting
        resting --> unlocking: unlocking_started
        unlocking --> resting: unlocking_failed
      }

      locked --> unlocked: unlocking_succeeded
      unlocked --> locked: locked
    """

    def __init__(self, device: "Device"):
        super().__init__()

        self._device = device

        # Declare the state chart described in the docstring.
        # See https://doc.qt.io/qt-5/statemachine-api.html
        #
        # This is a very declarative exercise.
        # The state names are part of the API of this class.
        self._machine = QStateMachine()

        self.unknown = QState()
        self.missing = QState()
        self.locked = QState()
        self.unlocked = QState()

        self.unknown.addTransition(self._device.found_unlocked, self.unlocked)
        self.unknown.addTransition(self._device.found_locked, self.locked)
        self.unknown.addTransition(self._device.not_found, self.missing)

        self.missing.addTransition(self._device.found_unlocked, self.unlocked)
        self.missing.addTransition(self._device.found_locked, self.locked)

        self.locked.addTransition(self._device.not_found, self.missing)
        self.unlocked.addTransition(self._device.not_found, self.missing)

        self.resting = QState(self.locked)
        self.unlocking = QState(self.locked)

        self.locked.setInitialState(self.resting)
        self.resting.addTransition(self._device.unlocking_started, self.unlocking)
        self.unlocking.addTransition(self._device.unlocking_failed, self.resting)

        self.locked.addTransition(self._device.unlocking_succeeded, self.unlocked)
        self.unlocked.addTransition(self._device.locked, self.locked)

        self._machine.addState(self.unknown)
        self._machine.addState(self.missing)
        self._machine.addState(self.locked)
        self._machine.addState(self.unlocked)
        self._machine.setInitialState(self.unknown)

        self._machine.start()


class Device(QObject):
    """Abstracts an export service for use in GUI components.

    This class defines an interface for GUI components to have access
    to the status of an export device without needed to interact directly
    with the underlying export service.
    """

    # These two signals and states are part of the device public API,
    # along with the public methods.
    state_changed = pyqtSignal(str)
    unlocking_started = pyqtSignal(str)
    unlocking_failed = pyqtSignal()

    State = NewType("State", str)
    UnknownState = State("unknown")
    MissingState = State("missing")
    LockedState = State("locked")
    UnlockingState = State("unlocking")
    UnlockedState = State("unlocked")
    RemovedState = State("removed")

    # These signals are part of the device private API.
    # They are used internally to keep track of the device state by
    # triggering state machine transitions in the _State instance.
    #
    # In this demo, the simulator connects to this API, but that's a hack.
    found_locked = pyqtSignal()
    found_unlocked = pyqtSignal()
    not_found = pyqtSignal()
    unlocking_succeeded = pyqtSignal()
    locked = pyqtSignal()

    # The following signals are part of the DEPRECATED legacy API.
    export_preflight_check_requested = pyqtSignal()
    export_preflight_check_succeeded = pyqtSignal()
    export_preflight_check_failed = pyqtSignal(object)

    export_requested = pyqtSignal(list, str)
    export_succeeded = pyqtSignal()
    export_failed = pyqtSignal(object)
    export_completed = pyqtSignal(list)

    print_preflight_check_requested = pyqtSignal()
    print_preflight_check_succeeded = pyqtSignal()
    print_preflight_check_failed = pyqtSignal(object)

    print_requested = pyqtSignal(list)
    print_succeeded = pyqtSignal()
    print_failed = pyqtSignal(object)

    def __init__(self, controller: Controller, export_service: export.Service) -> None:
        super().__init__()

        self._state = _State(self)

        # Track changes of state for public consumption.
        self._state.unknown.entered.connect(self._on_unknown_state_entered)
        self._state.missing.entered.connect(self._on_missing_state_entered)
        self._state.unlocking.entered.connect(self._on_unlocking_state_entered)
        self._state.resting.entered.connect(self._on_locked_state_entered)
        self._state.unlocked.entered.connect(self._on_unlocked_state_entered)
        self._current_state = Device.UnknownState

        self._controller = controller
        self._export_service = export_service

        self._export_service.connect_signals(
            self.export_preflight_check_requested,
            self.export_requested,
            self.print_preflight_check_requested,
            self.print_requested,
        )

        # Abstract the Export instance away from the GUI
        self._export_service.preflight_check_call_success.connect(
            self.export_preflight_check_succeeded
        )
        self._export_service.preflight_check_call_failure.connect(
            self.export_preflight_check_failed
        )

        self._export_service.export_usb_call_success.connect(self.export_succeeded)
        self._export_service.export_usb_call_failure.connect(self.export_failed)
        self._export_service.export_completed.connect(self.export_completed)

        self._export_service.printer_preflight_success.connect(self.print_preflight_check_succeeded)
        self._export_service.printer_preflight_failure.connect(self.print_preflight_check_failed)

        self._export_service.print_call_failure.connect(self.print_failed)
        self._export_service.print_call_success.connect(self.print_succeeded)

    @property
    def state(self) -> "Device.State":
        return self._current_state

    def emit_state_changed(func):
        def decorated(self):
            func(self)
            self.state_changed.emit(self._current_state)

        return decorated

    def attempt_unlocking(self, passphrase: str) -> None:
        self.unlocking_started.emit(passphrase)

    @emit_state_changed
    def _on_missing_state_entered(self) -> None:
        if self.state == Device.UnknownState:
            self._current_state = Device.MissingState
        else:
            # We can get subtle because we have access
            # to two subsequent states.
            # Some user interfaces could take advantage
            # of distinctions like this one.
            self._current_state = Device.RemovedState

    @emit_state_changed
    def _on_unlocking_state_entered(self) -> None:
        self._current_state = Device.UnlockingState

    @emit_state_changed
    def _on_locked_state_entered(self) -> None:
        self._current_state = Device.LockedState

    @emit_state_changed
    def _on_unlocked_state_entered(self) -> None:
        self._current_state = Device.UnlockedState

    @emit_state_changed
    def _on_unknown_state_entered(self) -> None:
        self._current_state = Device.UnknownState

    def run_printer_preflight_checks(self) -> None:
        """
        Run preflight checks to make sure the Export VM is configured correctly.
        """
        logger.info("Running printer preflight check")
        self.print_preflight_check_requested.emit()

    def run_export_preflight_checks(self) -> None:
        """
        Run preflight checks to make sure the Export VM is configured correctly.
        """
        logger.info("Running export preflight check")
        self.export_preflight_check_requested.emit()

    def export_file_to_usb_drive(self, file_uuid: str, passphrase: str) -> None:
        """
        Send the file specified by file_uuid to the Export VM with the user-provided passphrase for
        unlocking the attached transfer device.  If the file is missing, update the db so that
        is_downloaded is set to False.
        """
        file = self._controller.get_file(file_uuid)
        file_location = file.location(self._controller.data_dir)
        logger.info("Exporting file in: {}".format(os.path.dirname(file_location)))

        if not self._controller.downloaded_file_exists(file):
            return

        self.export_requested.emit([file_location], passphrase)

    def print_file(self, file_uuid: str) -> None:
        """
        Send the file specified by file_uuid to the Export VM. If the file is missing, update the db
        so that is_downloaded is set to False.
        """
        file = self._controller.get_file(file_uuid)
        file_location = file.location(self._controller.data_dir)
        logger.info("Printing file in: {}".format(os.path.dirname(file_location)))

        if not self._controller.downloaded_file_exists(file):
            return

        self.print_requested.emit([file_location])
