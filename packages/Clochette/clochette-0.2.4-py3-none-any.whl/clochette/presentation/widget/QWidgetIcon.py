from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QLabel


class QWidgetIcon(QLabel):
    def __init__(self, image_path: str, size: QSize) -> None:
        super().__init__()
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(scaled_pixmap)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
