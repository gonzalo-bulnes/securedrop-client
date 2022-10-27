from gettext import gettext as _
from typing import Union

from securedrop_client import db as database

from .item import Item


class Message(Item):
    def __init__(self, record: Union[database.Message, database.Reply]):
        super().__init__()

        self.content = record.content

        if isinstance(record, database.Message):
            self.sender = record.source.journalist_designation
        else:
            self.sender = record.journalist.username

    def metadata(self) -> str:
        return _("{username} wrote:").format(username=self.sender)

    def transcript(self) -> str:
        return self.content
