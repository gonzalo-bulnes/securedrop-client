from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget, QWizardPage

from securedrop_client import export


class Progress(QWidget):
    def __init__(self) -> None:
        super().__init__()

        hint = QLabel("<i>Depending on the number of files, this may take some time.</i>")
        hint.setWordWrap(True)
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(0)

        layout = QVBoxLayout()
        layout.addWidget(bar)
        layout.addWidget(hint)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class ExportPage(QWizardPage):
    def __init__(self, export_service: export.Service, parent: QWidget = None):
        super().__init__(parent)

        self._export_service = export_service

        self.setTitle("Export")

        self._is_complete = False
        self.completeChanged.emit()

        content = QLabel("Your export will start shortly...")
        content.setWordWrap(True)

        progress = Progress()
        progress.hide()

        layout = QVBoxLayout()
        layout.addWidget(content)
        layout.addWidget(progress)
        self.setLayout(layout)

        self._content = content
        self._progress = progress

    def isComplete(self) -> bool:
        return self._is_complete

    def initializePage(self) -> None:
        super().initializePage()
        self._connect_export_service()
        self._export_service.start()

    @pyqtSlot()
    def _on_export_started(self) -> None:
        self._content.setText("<p>Exporting files...</p>")
        self._progress.show()
        self._is_complete = False
        self.completeChanged.emit()

    @pyqtSlot()
    def _on_export_succeeded(self) -> None:
        self._content.setText("The files were exported successfully.")
        self._progress.hide()
        self._is_complete = True
        self.completeChanged.emit()
        self._disconnect_export_service()

    @pyqtSlot()
    def _on_export_failed(self) -> None:
        self._content.setText(
            "<p>An error happened and the files were <b>not</b> exported successfully.</p><p>Please be aware that it is possible that some of the data was written to the USB device.</p><p>You can attempt exporting again.</p>"  # noqa: E501
        )
        self._is_complete = True
        self._progress.hide()
        self.completeChanged.emit()
        self._disconnect_export_service()

    def _connect_export_service(self) -> None:
        self._export_service.succeeded.connect(self._on_export_succeeded)
        self._export_service.failed.connect(self._on_export_failed)
        self._export_service.started.connect(self._on_export_started)

    def _disconnect_export_service(self) -> None:
        # This is a it of a hack. By the time we do this, we'd be better off
        # using a state machine.
        self._export_service.succeeded.disconnect(self._on_export_succeeded)
        self._export_service.failed.disconnect(self._on_export_failed)
        self._export_service.started.disconnect(self._on_export_started)
