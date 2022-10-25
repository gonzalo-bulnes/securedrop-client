from typing import List, Optional, Union

from securedrop_client import db as database


def digest(conversation: List[Union[database.Message, database.Reply, database.File]]) -> str:
    separator = "------\n"
    if len(conversation) <= 0:
        return "No messages."

    items = []

    previous_sender: Optional[str] = None

    for item in conversation:
        item_digest = ""
        if isinstance(item, database.Message):
            sender = item.source.journalist_designation
            item_digest += f"{sender} wrote:\n"
        if isinstance(item, database.File):
            sender = item.source.journalist_designation
            item_digest += f"{sender} sent:\n"
        if isinstance(item, database.Reply):
            sender = item.journalist.username
            item_digest += f"{sender} wrote:\n"

        if previous_sender is not None and sender == previous_sender:
            item_digest = ""

        item_digest += str(item) + "\n"

        items.append(item_digest)

        previous_sender = sender

    return separator.join(items)
