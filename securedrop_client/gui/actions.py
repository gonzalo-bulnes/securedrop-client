"""
The actions available to the journalist.

Over time, this module could become the interface between
the GUI and the controller.
"""
import logging
from gettext import gettext as _
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QAction, QDialog, QMenu

from securedrop_client import conversation, state
from securedrop_client.db import Source
from securedrop_client.logic import Controller
from securedrop_client.utils import safe_mkdir

logger = logging.getLogger(__name__)


class DownloadConversation(QAction):
    """Download all files and messages of the currently selected conversation."""

    def __init__(
        self, parent: QMenu, controller: Controller, app_state: Optional[state.State] = None
    ) -> None:
        self._controller = controller
        self._state = app_state
        self._text = _("Download All Files")
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


class DeleteSource(QAction):
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
        self.text = _("Delete Source Account")

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


class DeleteConversation(QAction):
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
        self.text = _("Delete All Files and Messages")

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


class PrintConversation(QAction):
    """Use this action to print a snapshot of the messages, replies, etc.

    Includes eventual references to attached files.
    """

    def __init__(
        self,
        source: Source,
        parent: QMenu,
        controller: Controller,
        print_conversation: Callable[[Path], None],
        confirmation_dialog: Callable[[Source], QDialog],
        app_state: Optional[state.State] = None,
    ) -> None:
        self._source = source
        self._controller = controller
        self._print_conversation = print_conversation
        self._state = app_state
        self._text = _("Print Conversation")

        super().__init__(self._text, parent)

        self._confirmation_dialog = confirmation_dialog(self._source)
        self._confirmation_dialog.accepted.connect(lambda: self._on_confirmation_dialog_accepted())
        self.triggered.connect(self.trigger)

    def trigger(self) -> None:
        if self._controller.api is None:
            self._controller.on_action_requiring_login()
        else:
            self._confirmation_dialog.exec()

    def _on_confirmation_dialog_accepted(self) -> None:
        if self._state is not None:
            id = self._state.selected_conversation
            if id is None:
                return

            transcript = conversation.Transcript(self._source)
            path = Path(self._controller.data_dir).joinpath(self._source.journalist_filename)
            safe_mkdir(path)

            path = path.joinpath("conversation.txt")

            with open(path, "w") as f:
                f.write(str(transcript))

                logger.info(f"Printing transcript of conversation ({id})")
                self._print_conversation(path)
