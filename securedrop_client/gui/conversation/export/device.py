from typing import Optional

from PyQt5.QtCore import QObject, QState, QStateMachine, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget

from securedrop_client.export import ConnectedDevice, EncryptedDevice


class Device(QObject):
    """An export device (typically a USB drive) which availability can be monitored.

    Usage:

    1. Connect to the signals that compose the public API: e.g. absent, available,
       removed and available_again.
    2. Trigger the verification as often as needed using the verify_availability slot.
    """

    # Internal Signals
    availability_verification_requested = pyqtSignal()
    availability_verification_started = pyqtSignal()
    presence_verification_failed = pyqtSignal()
    encryption_verification_failed = pyqtSignal()

    # Public API
    absent = pyqtSignal()
    available = pyqtSignal()
    removed = pyqtSignal()
    available_again = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._state = DeviceState(self)
        self._debug = False

        self._state.verifying.entered.connect(self.verify_availability)
        if self._debug:
            self._state.verifying.entered.connect(lambda: print("verifying device..."))

        self._history = DeviceHistory(self)
        self._history.device_was_never_available.entered.connect(self.absent)
        self._history.device_was_never_available.exited.connect(self.available)
        self._history.device_currently_available.exited.connect(self.removed)
        self._history.device_recently_available.entered.connect(self.available_again)
        if self._debug:
            self.absent.connect(lambda: print("device absent"))
            self.available.connect(lambda: print("device available"))
            self.removed.connect(lambda: print("device removed"))
            self.available_again.connect(lambda: print("device available again"))

    @pyqtSlot()
    def verify_availability(self) -> None:
        """Trigger an ad-hoc availability verification."""
        self.availability_verification_requested.emit()

    @pyqtSlot()
    def _verify_availability(self) -> None:
        """Verify the availability of a USB device.

        Currently, availability is defined as being present and encrypted.
        """
        self.availability_verification_started.emit()
        connected_device = ConnectedDevice.create()
        if connected_device is None:
            self.presence_verification_failed.emit()
            return

        encrypted_device = EncryptedDevice.create(connected_device)
        if encrypted_device is None:
            self.encryption_verification_failed.emit()
            return

        self.availability_verification_succeded.emit()


class DeviceState(QWidget):
    """The state of an export device (USB drive).

    There should be no need for you to use this class directly.

    This class describes the behavior of an export device. An available device
    is defined as being present (connected) and encrypted, because those
    are the requirements for exporting (sensitive) files to it.

    A device is missing when not connected, and can be connected but not encrypted.
    Since there is no way to verify the encryption state of a disconnected device,
    a device that is described as device_inadequate is guaranteed to be connected.

    If you were to use this class, please note that the actual verifying behavior
    should be connected to the signal that is emitted when the verifying state is entered.


    Paste the following state chart in https://mermaid.live for
    a visual representation of the behavior implemented by this class!

    stateDiagram-v2
        direction LR
        verifying --> device_missing: device_presence_verification_failed
        verifying --> device_inadequate: device_encryption_verification_failed
        verifying --> device_available: device_verification_succeeded
        device_missing --> verifying: device_availability_verification_requested
        device_inadequate --> verifying: device_availability_verification_requested
        device_available --> verifying: device_availability_verification_requested
    """

    def __init__(self, device: Optional[Device] = None) -> None:
        super().__init__()

        # Declare the state chart described in the docstring.
        # See https://doc.qt.io/qt-5/statemachine-api.html
        #
        # This is a very declarative exercise.
        # The state names are part of the API of this class.
        self._machine = QStateMachine()

        self.verifying = QState()
        self.device_available = QState()
        self.device_missing = QState()
        self.device_inadequate = QState()

        self._machine.addState(self.verifying)
        self._machine.addState(self.device_available)
        self._machine.addState(self.device_missing)
        self._machine.addState(self.device_inadequate)

        self._machine.setInitialState(self.verifying)

        if device is not None:
            self.verifying.addTransition(
                device.availability_verification_failed, self.device_missing
            )
            self.verifying.addTransition(
                device.encryption_verification_failed, self.device_inadequate
            )
            self.verifying.addTransition(
                device.availability_verification_succeeded, self.device_available
            )

            self.device_available.addTransition(
                device.availability_verification_requested, self.verifying
            )
            self.device_missing.addTransition(
                device.availability_verification_requested, self.verifying
            )
            self.device_inadequate.addTransition(
                device.availability_verification_requested, self.verifying
            )

        self._machine.start()


class DeviceHistory(QWidget):
    """The history of an export device (USB drive).

    There should be no need for you to use this class directly.

    This class describes the history of an export device. An device that
    is currently missing may have been present recently, and that information
    can be used to provide relevant guidance to journalists via the GUI.


    Paste the following state chart in https://mermaid.live for
    a visual representation of the behavior implemented by this class!

    stateDiagram-v2
        device_was_never_available --> device_currently_available: device_availability_verification_succeeded
        device_currently_available --> device_recently_available: device_availability_verification_failed
        device_recently_available --> device_currently_available: device_availability_verification_succeeded
    """  # noqa: E501

    def __init__(self, device: Optional[Device] = None) -> None:
        super().__init__()

        # Declare the state chart described in the docstring.
        # See https://doc.qt.io/qt-5/statemachine-api.html
        #
        # This is a very declarative exercise.
        # The state names are part of the API of this class.
        self._machine = QStateMachine()

        self.verifying = QState()
        self.device_was_never_available = QState()
        self.device_currently_available = QState()
        self.device_recently_available = QState()

        self._machine.addState(self.verifying)
        self._machine.addState(self.device_was_never_available)
        self._machine.addState(self.device_currently_available)
        self._machine.addState(self.device_recently_available)

        if device is not None:
            self.device_as_never_available.addTransition(
                device.availability_verification_succeeded, self.device_currently_available
            )
            self.device_currently_available.addTransition(
                device.availability_verification_faileded, self.device_recently_available
            )
            self.device_recently_available.addTransition(
                device.availability_verification_succeeded, self.device_currently_available
            )

        self._machine.setInitialState(self.verifying)

        self._machine.start()
