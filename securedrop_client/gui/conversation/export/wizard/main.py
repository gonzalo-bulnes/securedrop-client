from enum import IntEnum

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QWizard

from securedrop_client import export

from ..device import Device
from .pages import ExportPage, InsertDevicePage, ReviewDataPage, StartPage, UnlockDevicePage


class Wizard(QWizard):

    PageId = IntEnum("PageId", "START INSERT_DEVICE UNLOCK_DEVICE REVIEW_DATA EXPORT")

    def __init__(self, device: Device, export_service: export.Service, parent: QWidget = None):
        super().__init__(parent)

        # Connect the device
        self._device = device
        self._device.state_changed.connect(self._on_device_state_changed)

        self._export_service = export_service

        self.setWindowTitle("Wizard")
        self.setModal(False)
        self.setOptions(
            QWizard.NoBackButtonOnLastPage
            | QWizard.NoCancelButtonOnLastPage
            | QWizard.NoBackButtonOnStartPage
        )

        self.setPage(Wizard.PageId.START, StartPage())
        self.setPage(Wizard.PageId.INSERT_DEVICE, InsertDevicePage(self._device.state_changed))
        self.setPage(Wizard.PageId.UNLOCK_DEVICE, UnlockDevicePage(self._device))
        self.setPage(Wizard.PageId.REVIEW_DATA, ReviewDataPage())
        self.setPage(Wizard.PageId.EXPORT, ExportPage(self._export_service))

        self.setStartId(Wizard.PageId.START)

        for page in [self.page(id) for id in self.pageIds()]:
            page.completeChanged.connect(lambda: self._set_focus(QWizard.WizardButton.NextButton))

    def device_locked(self) -> bool:
        return self._device.state == Device.LockedState

    def device_unlocked(self) -> bool:
        return self._device.state == Device.UnlockedState

    def device_unlocking(self) -> bool:
        return self._device.state == Device.UnlockingState

    @pyqtSlot(int)
    def _set_focus(self, which: QWizard.WizardButton) -> None:
        self.button(which).setFocus(True)

    @pyqtSlot(str)
    def _on_device_state_changed(self, state: Device.State) -> None:
        device_state = self._device.state
        page_id = self.currentId()

        # this method screams for thorough unit testing - the proof-of-concept works
        if page_id >= Wizard.PageId.EXPORT:
            return  # once the export is started, device events are handled in place

        if device_state == Device.UnknownState:
            pass  # only happens on the Wizard.PageId.START, where it's OK
        elif device_state == Device.MissingState or device_state == Device.RemovedState:
            if (
                page_id > Wizard.PageId.INSERT_DEVICE
            ):  # after that page, the device presence is required
                self._back_to_page(Wizard.PageId.INSERT_DEVICE)  # let's get it back!
        elif device_state == Device.UnlockedState:
            pass  # unlocked devices are always OK!
        else:  # covers the varied states of locked devices
            if (
                page_id > Wizard.PageId.UNLOCK_DEVICE
            ):  # after that page, the device must be unlocked
                self._back_to_page(Wizard.PageId.UNLOCK_DEVICE)  # let's go unlock it!

    def _back_to_page(self, id: "Wizard.PageId") -> None:
        while self.currentId() > id:  # assumes that pages are sorted by ID, which is true
            self.back()
