from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QWizardPage


class ReviewDataPage(QWizardPage):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.setTitle("Review file list")

        content = QLabel("The following files will be exported: ...")
        content.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(content)
        self.setLayout(layout)
