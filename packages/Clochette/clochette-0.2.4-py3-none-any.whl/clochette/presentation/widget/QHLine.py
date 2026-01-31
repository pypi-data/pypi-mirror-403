from PySide6.QtWidgets import QFrame


class QHLine(QFrame):
    def __init__(self):

        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
