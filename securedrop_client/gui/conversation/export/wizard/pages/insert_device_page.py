from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QWizardPage


class InsertDevicePage(QWizardPage):
    def __init__(self, device_state_changed: pyqtSignal, parent: QWidget = None):
        super().__init__(parent)

        self.setTitle("Insert USB device")

        instructions = QLabel("The USB device must be encrypted with LUKS or Veracrypt.")
        instructions.setWordWrap(True)
        completion_message = QLabel("USB device found, feel free to change it if needed.")
        completion_message.hide()

        layout = QVBoxLayout()
        layout.addWidget(instructions)
        layout.addWidget(completion_message)
        self.setLayout(layout)

        device_state_changed.connect(self.completeChanged)

        self.instructions = instructions
        self.completion_message = completion_message

    def isComplete(self) -> bool:
        is_complete = (
            self.wizard().device_locked()
            or self.wizard().device_unlocking()
            or self.wizard().device_unlocked()
        )

        if is_complete:
            self.instructions.hide()
            self.completion_message.show()
        else:
            self.instructions.show()
            self.completion_message.hide()

        return is_complete
