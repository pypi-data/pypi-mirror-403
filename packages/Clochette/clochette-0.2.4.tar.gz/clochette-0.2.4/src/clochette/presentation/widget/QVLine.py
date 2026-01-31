from PySide6.QtWidgets import QFrame


class QVLine(QFrame):
    def __init__(self):

        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
