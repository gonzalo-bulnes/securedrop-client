"""
The actions available to the journalist.

Over time, this module could become the interface between
the GUI and the controller.
"""
from gettext import gettext as _
from typing import Callable, Optional

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QAction, QDialog, QMenu

from securedrop_client import state
from securedrop_client.db import Source
from securedrop_client.logic import Controller


class DownloadConversation(QAction):
    """Download all files and messages of the currently selected conversation."""

    def __init__(
        self, parent: QMenu, controller: Controller, app_state: Optional[state.State] = None
    ) -> None:
        self._controller = controller
        self._state = app_state
        self._text = _("All Files")
        super().__init__(self._text, parent)
        self.setShortcut(Qt.CTRL + Qt.Key_D)
        self.triggered.connect(self.on_triggered)
        self.setShortcutVisibleInContextMenu(True)

        self._connect_enabled_to_conversation_changes()
        self._set_enabled_initial_value()

    @pyqtSlot()
    def on_triggered(self) -> None:
        if self._controller.api is None:
            self._controller.on_action_requiring_login()
        else:
            if self._state is not None:
                id = self._state.selected_conversation
                if id is None:
                    return
                self._controller.download_conversation(id)

    def _connect_enabled_to_conversation_changes(self) -> None:
        if self._state is not None:
            self._state.selected_conversation_files_changed.connect(
                self._on_selected_conversation_files_changed
            )

    @pyqtSlot()
    def _on_selected_conversation_files_changed(self) -> None:
        if self._state is None:
            return
        if self._state.selected_conversation_has_downloadable_files:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

    def _set_enabled_initial_value(self) -> None:
        self._on_selected_conversation_files_changed()


class DeleteSourceAction(QAction):
    """Use this action to delete the source record."""

    def __init__(
        self,
        source: Source,
        parent: QMenu,
        controller: Controller,
        confirmation_dialog: Callable[[Source], QDialog],
    ) -> None:
        self.source = source
        self.controller = controller
        self.text = _("Entire source account")

        super().__init__(self.text, parent)

        self._confirmation_dialog = confirmation_dialog(self.source)
        self._confirmation_dialog.accepted.connect(
            lambda: self.controller.delete_source(self.source)
        )
        self.triggered.connect(self.trigger)

    def trigger(self) -> None:
        if self.controller.api is None:
            self.controller.on_action_requiring_login()
        else:
            self._confirmation_dialog.exec()


class DeleteConversationAction(QAction):
    """Use this action to delete a source's submissions and replies."""

    def __init__(
        self,
        source: Source,
        parent: QMenu,
        controller: Controller,
        confirmation_dialog: Callable[[Source], QDialog],
        app_state: Optional[state.State] = None,
    ) -> None:
        self.source = source
        self.controller = controller
        self._state = app_state
        self.text = _("Files and messages")

        super().__init__(self.text, parent)

        self._confirmation_dialog = confirmation_dialog(self.source)
        self._confirmation_dialog.accepted.connect(lambda: self._on_confirmation_dialog_accepted())
        self.triggered.connect(self.trigger)

    def trigger(self) -> None:
        if self.controller.api is None:
            self.controller.on_action_requiring_login()
        else:
            self._confirmation_dialog.exec()

    def _on_confirmation_dialog_accepted(self) -> None:
        if self._state is not None:
            id = self._state.selected_conversation
            if id is None:
                return
            self.controller.delete_conversation(self.source)
            self._state.remove_conversation_files(id)


class ExportConversationFiles(QAction):
    """Download all files of the currently selected conversation."""

    def __init__(
        self,
        source: Source,
        parent: QMenu,
        controller: Controller,
        confirmation_dialog: Callable[[Source], QDialog],
        app_state: Optional[state.State] = None,
    ) -> None:
        self._controller = controller
        self._state = app_state
        self._text = _("All Files")  # same as DownloadConversation because the verb is missing :(
        super().__init__(self._text, parent)

        self._passphrase: Optional[str] = None

        self._confirmation_dialog = confirmation_dialog(self.source)
        self._confirmation_dialog.passphrase_submitted.connect(self._on_passphrase_submitted)
        self._confirmation_dialog.accepted.connect(lambda: self._on_confirmation_dialog_accepted())
        self._confirmation_dialog.rejected.connect(lambda: self._on_confirmation_dialog_rejected())
        self.triggered.connect(self.trigger)

        self._connect_enabled_to_conversation_changes()
        self._set_enabled_initial_value()

    @property
    def passphrase(self) -> Optional[str]:
        """A single-use passphrase"""
        passphrase = self._passphrase
        self._passphrase = None
        return passphrase

    @passphrase.setter
    def passphrase(self, passphrase: Optional[str]) -> None:
        self._passphrase = passphrase

    @pyqtSlot(str)
    def on_passphrase_submitted(self, passphrase: str) -> None:
        print("on_passphrase_submitted", passphrase)
        self._passphrase = passphrase

    @pyqtSlot()
    def on_confirmation_dialog_accepted(self) -> None:
        print("on_conformation_dialog_accepted")
        if self._controller.api is None:
            self._controller.on_action_requiring_login()
        else:
            if self._state is not None:
                id = self._state.selected_conversation
                if id is None:
                    return
                passphrase = self.passphrase
                if passphrase is None:
                    passphrase = ""
                self._controller.export_conversation(id, passphrase)

    def _connect_enabled_to_conversation_changes(self) -> None:
        if self._state is not None:
            self._state.selected_conversation_files_changed.connect(
                self._on_selected_conversation_files_changed
            )

    @pyqtSlot()
    def _on_selected_conversation_files_changed(self) -> None:
        if self._state is None:
            return
        if self._state.selected_conversation_has_exportable_files:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

    def _set_enabled_initial_value(self) -> None:
        self._on_selected_conversation_files_changed()
