# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright © 2022 The Freedom of the Press Foundation.
"""
The types relevant to the internal state of the SecureDrop Client.
"""
from typing import NewType

ConversationId = NewType("ConversationId", str)


class SourceId(str):
    pass


class FileId(str):
    """Identifies a file without making assumptions about it.

    Once a file has been downloaded and is available locally, please use DownloadedFileId.
    """

    pass


class File:
    def __init__(self, id: FileId) -> None:
        self._id: str = id
        self._is_downloaded: bool = False

    def _get_id(self) -> str:
        return self._id

    def _get_is_downloaded(self) -> bool:
        return self._is_downloaded

    def _set_is_downloaded(self, value: bool) -> None:
        self._is_downloaded = value

    id = property(
        fget=_get_id,
        fset=None,
        fdel=None,
        doc="A unique identifier file set by the server (opaque string).",
    )

    is_downloaded = property(
        fget=_get_is_downloaded,
        fset=_set_is_downloaded,
        fdel=None,
        doc="Whether the file is available locally.",
    )
