from gettext import gettext as _

from securedrop_client import db as database

from .item import Item


class File(Item):
    def __init__(self, record: database.File):
        super().__init__()

        self.filename = record.filename
        self.sender = record.source.journalist_designation

    def metadata(self) -> str:
        return _("{username} sent:").format(username=self.sender)

    def transcript(self) -> str:
        return _("File: {filename}").format(filename=self.filename)
