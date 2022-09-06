from PyQt5.QtWidgets import QPushButton, QWidget

from securedrop_client import export

from ..device import Device
from .main import Wizard


class ThemedWizard(Wizard):
    def __init__(self, device: Device, export_service: export.Service, parent: QWidget = None):
        super().__init__(device, export_service, parent)

        self.setOption(Wizard.CancelButtonOnLeft)

        button = PushButton(PushButton.TypeContained)
        button.setText("Next")
        self.setButton(Wizard.WizardButton.NextButton, button)

        button = PushButton(PushButton.TypeOutlined)
        button.setText("Back")
        self.setButton(Wizard.WizardButton.BackButton, button)

        button = PushButton(PushButton.TypeText)
        button.setText("Cancel")
        self.setButton(Wizard.WizardButton.CancelButton, button)

        button = PushButton(PushButton.TypeContained)
        button.setText("Finish")
        self.setButton(Wizard.WizardButton.FinishButton, button)

        self.setButtonLayout(
            [
                Wizard.WizardButton.CancelButton,
                Wizard.WizardButton.Stretch,
                Wizard.WizardButton.BackButton,
                Wizard.WizardButton.NextButton,
                Wizard.WizardButton.FinishButton,
            ]
        )
