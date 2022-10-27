from typing import List, Optional

from securedrop_client import db as database

from .items import Item
from .items import transcribe as transcribe_item


def transcribe(record: database.Base) -> Optional[Item]:
    return transcribe_item(record)


class Transcript:
    def __init__(self, conversation: database.Source) -> None:

        self._items: List[Item] = []

    def __str__(self) -> str:
        return "FIXME"
