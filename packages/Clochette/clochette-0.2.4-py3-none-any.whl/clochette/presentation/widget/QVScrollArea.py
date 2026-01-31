from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QWidget, QStyle
from typing_extensions import override


class QVScrollArea(QScrollArea):
    """Vertical-only scroll area with automatic width management to prevent scrollbar overlap"""

    def __init__(self):
        super().__init__()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

    @override
    def setWidget(self, widget: QWidget) -> None:
        """Set the widget and automatically adjust minimum width to account for scrollbar"""
        super().setWidget(widget)

        # Calculate minimum width: widget's size hint + scrollbar width
        scrollbar_width = self.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
        self.setMinimumWidth(widget.sizeHint().width() + scrollbar_width)
