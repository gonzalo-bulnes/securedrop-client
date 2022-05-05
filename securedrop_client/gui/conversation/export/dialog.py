"""
Conversation export dialog.
"""
from gettext import gettext as _
from gettext import ngettext

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QPushButton, QVBoxLayout, QWidget

from securedrop_client.db import File, Message, Reply
from securedrop_client.gui.base import ModalDialog, PasswordEdit, SecureQLabel


class ExportConversationDialog(ModalDialog):
    """
    Shown to confirm export of all files from a conversation.

    Also responsible for obtaining the passphrase of the destination drive.
    """

    PASSPHRASE_LABEL_SPACING = 0.5
    NO_MARGIN = 0

    passphrase_submitted = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__(show_header=False, dangerous=False)

        self.body.setText(self.make_body_text())

        # Passphrase Form
        self.passphrase_form = QWidget()
        self.passphrase_form.setObjectName("ExportDialog_passphrase_form")
        passphrase_form_layout = QVBoxLayout()
        passphrase_form_layout.setContentsMargins(
            self.NO_MARGIN, self.NO_MARGIN, self.NO_MARGIN, self.NO_MARGIN
        )
        self.passphrase_form.setLayout(passphrase_form_layout)
        passphrase_label = SecureQLabel(_("Passphrase"))
        font = QFont()
        font.setLetterSpacing(QFont.AbsoluteSpacing, self.PASSPHRASE_LABEL_SPACING)
        passphrase_label.setFont(font)
        self.passphrase_field = PasswordEdit(self)
        self.passphrase_field.setEchoMode(QLineEdit.Password)
        effect = QGraphicsDropShadowEffect(self)
        effect.setOffset(0, -1)
        effect.setBlurRadius(4)
        effect.setColor(QColor("#aaa"))
        self.passphrase_field.setGraphicsEffect(effect)
        passphrase_form_layout.addWidget(passphrase_label)
        passphrase_form_layout.addWidget(self.passphrase_field)
        self.body_layout.addWidget(self.passphrase_form)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(lambda: self._on_submit_button_clicked())

        self.body_layout.addWidget(self.submit_button)
        self.continue_button.setText(_("YES, DELETE FILES AND MESSAGES"))
        self.continue_button.setFocus()

        self.adjustSize()

    def _on_submit_button_clicked(self) -> None:
        self.passphrase_submitted.emit(self.passphrase_field.text())

    def make_body_text(self) -> str:
        return "lorem ispum"
        files = 0
        messages = 0
        replies = 0
        for submission in self.source.collection:
            if isinstance(submission, Message):
                messages += 1
            if isinstance(submission, Reply):
                replies += 1
            elif isinstance(submission, File):
                files += 1

        message_tuple = (
            "<style>li {{line-height: 150%;}}</li></style>",
            "<p>",
            _(
                "You would like to delete {files_to_delete}, {replies_to_delete}, "
                "{messages_to_delete} from the source account for {source}?"
            ),
            "</p>",
            "<p>",
            _(
                "Preserving the account will retain its metadata, and the ability for {source} "
                "to log in to your SecureDrop again."
            ),
            "</p>",
        )

        files_to_delete = ngettext("one file", "{file_count} files", files).format(file_count=files)

        replies_to_delete = ngettext("one reply", "{reply_count} replies", replies).format(
            reply_count=replies
        )

        messages_to_delete = ngettext("one message", "{message_count} messages", messages).format(
            message_count=messages
        )

        source = "<b>{}</b>".format(self.source.journalist_designation)

        return "".join(message_tuple).format(
            files_to_delete=files_to_delete,
            messages_to_delete=messages_to_delete,
            replies_to_delete=replies_to_delete,
            source=source,
        )

    def exec(self) -> None:
        # Refresh counters
        self.body.setText(self.make_body_text())
        super().exec()
