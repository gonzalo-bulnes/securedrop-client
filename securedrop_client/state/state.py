# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright © 2022 The Freedom of the Press Foundation.
"""
Stores and provides read/write access to the internal state of the SecureDrop Client.

Note: the Graphical User Interface MUST NOT write state, except in QActions.
"""
from typing import Dict, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from .domain import ConversationId, File, FileId


class State(QObject):
    """Stores and provides read/write access to the internal state of the SecureDrop Client.

    Note: the Graphical User Interface SHOULD NOT write state, except in QActions.
    """

    selected_conversation_files_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._files: Dict[FileId, File] = {}
        self._conversation_files: Dict[ConversationId, List[File]] = {}
        self._selected_conversation: Optional[ConversationId] = None

    def add_file(self, cid: ConversationId, fid: FileId) -> None:
        file = File(fid)  # store references to the same object
        if fid not in self._files.keys():
            self._files[fid] = file

        if cid not in self._conversation_files.keys():
            self._conversation_files[cid] = [file]
            if cid == self._selected_conversation:
                self.selected_conversation_files_changed.emit()
        else:
            file_is_known = False
            for known_file in self._conversation_files[cid]:
                if fid == known_file.id:
                    file_is_known = True
            if not file_is_known:
                self._conversation_files[cid].append(file)
                if cid == self._selected_conversation:
                    self.selected_conversation_files_changed.emit()

    def conversation_files(self, id: ConversationId) -> List[File]:
        default: List[File] = []
        return self._conversation_files.get(id, default)

    def file(self, id: FileId) -> Optional[File]:
        return self._files.get(id, None)

    def record_file_download(self, id: FileId) -> None:
        if id not in self._files.keys():
            pass
        else:
            self._files[id].is_downloaded = True
            self.selected_conversation_files_changed.emit()

    def _get_selected_conversation(self) -> Optional[ConversationId]:
        return self._selected_conversation

    def set_selected_conversation(self, id: Optional[ConversationId]) -> None:
        self._selected_conversation = id
        self.selected_conversation_files_changed.emit()

    def _get_selected_conversation_has_downloadable_files(self) -> bool:
        print("Checking downloadable files in selected conversation")
        default: List[File] = []
        for f in self._conversation_files.get(self._selected_conversation, default):
            print(f.is_downloaded)
            if not f.is_downloaded:
                print("has downloadable files")
                return True
        return False

    selected_conversation = property(
        fget=_get_selected_conversation,
        fset=set_selected_conversation,
        fdel=None,
        doc="The identifier of the currently selected conversation, or None",
    )

    selected_conversation_has_downloadable_files = property(
        fget=_get_selected_conversation_has_downloadable_files,
        fset=None,
        fdel=None,
        doc="Whether the selected conversation has any files that are not alredy downloaded",
    )
