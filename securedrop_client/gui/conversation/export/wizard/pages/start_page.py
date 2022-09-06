from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QWizardPage


class StartPage(QWizardPage):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setTitle("Disclaimer")

        content = QLabel("Please be aware that exporting files carries some <b>risks</b>.")
        content.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(content)
        self.setLayout(layout)
