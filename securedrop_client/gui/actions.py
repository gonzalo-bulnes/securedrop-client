"""
The actions available to the journalist.

Copyright (C) 2021 The Freedom of the Press Foundation.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from gettext import gettext as _
from typing import Callable, List, Type

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QAction, QDialog, QMenu

from securedrop_client.db import File, Source
from securedrop_client.logic import Controller


class DownloadAllFiles(QAction):
    def __init__(
            self, source: Source, download: Callable[[File, str], None], parent: QMenu
    ) -> None:
        self._text = _("Download All")

        super().__init__(self._text, parent)
        self._source = source
        self._download = download

        self.triggered.connect(self._download_all_files)

    @pyqtSlot()
    def _download_all_files(self) -> None:
        print("Downloading all files...")
        for file in self._files():
            self._download(File, file.uuid)

    def _files(self) -> List[File]:
        return []


class DeleteSourceAction(QAction):
    """Use this action to delete the source record."""

    def __init__(
        self,
        source: Source,
        parent: QMenu,
        controller: Controller,
        confirmation_dialog: Type[QDialog],
    ) -> None:
        self.source = source
        self.controller = controller
        self.text = _("Entire source account")

        super().__init__(self.text, parent)

        self._confirmation_dialog = confirmation_dialog(self.source, self.controller)
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
        confirmation_dialog: Type[QDialog],
    ) -> None:
        self.source = source
        self.controller = controller
        self.text = _("Files and messages")

        super().__init__(self.text, parent)

        self.confirmation_dialog = confirmation_dialog(self.source, self.controller)
        self.triggered.connect(self.trigger)

    def trigger(self) -> None:
        if self.controller.api is None:
            self.controller.on_action_requiring_login()
        else:
            self.confirmation_dialog.exec()
