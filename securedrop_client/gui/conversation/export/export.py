from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Export(QObject):
    def __init__(self) -> None:
        super().__init__()

