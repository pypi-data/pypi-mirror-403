from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from clochette import log
from clochette.framework.qt.Signal import OutHollowSignal


class QSystray(QSystemTrayIcon):
    on_exit_clicked: OutHollowSignal
    on_settings_clicked: OutHollowSignal
    on_icon_clicked: OutHollowSignal

    def __init__(self) -> None:
        super().__init__()

        self.on_exit_clicked = OutHollowSignal()
        self.on_settings_clicked = OutHollowSignal()
        self.on_icon_clicked = OutHollowSignal()

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.setToolTip(self.tr("Clochette"))

            self._tray_menu = QMenu()

            settings_action = QAction(self.tr("Settings"), self)
            exit_action = QAction(self.tr("Exit"), self)

            settings_action.triggered.connect(self.on_settings_clicked.send)
            exit_action.triggered.connect(self.on_exit_clicked.send)

            self._tray_menu.addAction(settings_action)
            self._tray_menu.addAction(exit_action)

            self.setContextMenu(self._tray_menu)

            self.activated.connect(self._on_activated)
        else:
            log.error("No system tray available")

    def _on_activated(self, _: QSystemTrayIcon.ActivationReason) -> None:
        self.on_icon_clicked.send()

    def set_icon(self, icon: QIcon) -> None:
        """Thread-safe handler for icon updates."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.setIcon(icon)

    def show(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            super().show()
        else:
            log.error("No system tray available")
