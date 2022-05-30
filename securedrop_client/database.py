# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright © 2022 The Freedom of the Press Foundation.
from typing import List

from sqlalchemy.orm.session import Session

from securedrop_client.db import File, Message
from securedrop_client.storage import get_local_files, get_local_messages


class Database:
    """Provide an interface to the database while abstracting session details."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def get_files(self) -> List[File]:
        return get_local_files(self.session)

    def get_messages(self) -> List[Message]:
        return get_local_messages(self.session)
