import unittest
from unittest import mock

from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QWizard

from securedrop_client import export
from securedrop_client.gui import conversation
from securedrop_client.logic import Controller
from tests.helper import app  # noqa: F401


class TestExportWizard(unittest.TestCase):
    def setUp(self):
        controller = mock.MagicMock(spec=Controller)
        export_service = export.Service()
        device = conversation.ExportDevice(controller, export_service)
        wizard = conversation.ExportWizard(device, export_service)
        device_started = QSignalSpy(device._state._machine.started)
        device_started.wait(1000)

        self.wizard = wizard
        self.device = device

    def test_defines_public_page_ids(self):
        assert conversation.ExportWizard.PageId.START
        assert conversation.ExportWizard.PageId.INSERT_DEVICE
        assert conversation.ExportWizard.PageId.UNLOCK_DEVICE
        assert conversation.ExportWizard.PageId.REVIEW_DATA
        assert conversation.ExportWizard.PageId.EXPORT

    def test_pages_are_ordered(self):
        assert self.wizard.pageIds() == [
            conversation.ExportWizard.PageId.START,
            conversation.ExportWizard.PageId.INSERT_DEVICE,
            conversation.ExportWizard.PageId.UNLOCK_DEVICE,
            conversation.ExportWizard.PageId.REVIEW_DATA,
            conversation.ExportWizard.PageId.EXPORT,
        ]

    def test_export_page_is_final(self):
        assert self.wizard.page(conversation.ExportWizard.PageId.EXPORT).isFinalPage()

    def test_start_page_next_button_is_enabled(self):
        self.wizard.restart()
        assert self.wizard.currentId() == conversation.ExportWizard.PageId.START
        assert self.wizard.button(QWizard.WizardButton.NextButton).isEnabled()

    def test_insert_device_page_button_is_disabled_until_device_is_found(self):
        device_state_changed_emissions = QSignalSpy(self.device.state_changed)

        self.wizard.restart()
        self.wizard.next()
        assert self.wizard.currentId() == conversation.ExportWizard.PageId.INSERT_DEVICE
        assert not self.wizard.button(QWizard.WizardButton.NextButton).isEnabled()

        self.device.found_locked.emit()
        device_state_changed_emissions.wait(1000)
        assert self.wizard.device_locked()
        assert self.wizard.currentId() == conversation.ExportWizard.PageId.INSERT_DEVICE
        assert self.wizard.button(QWizard.WizardButton.NextButton).isEnabled()

        self.device.not_found.emit()
        device_state_changed_emissions.wait(1000)
        assert self.wizard.currentId() == conversation.ExportWizard.PageId.INSERT_DEVICE
        assert not self.wizard.button(QWizard.WizardButton.NextButton).isEnabled()

        self.device.found_unlocked.emit()
        device_state_changed_emissions.wait(1000)
        assert self.wizard.device_unlocked()
        assert self.wizard.currentId() == conversation.ExportWizard.PageId.INSERT_DEVICE
        assert self.wizard.button(QWizard.WizardButton.NextButton).isEnabled()
