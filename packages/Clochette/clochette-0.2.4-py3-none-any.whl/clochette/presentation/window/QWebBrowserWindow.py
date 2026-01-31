import os
from typing import override

from PySide6.QtCore import QUrl
from PySide6.QtGui import QCloseEvent, QAction, QIcon
from PySide6.QtWebEngineCore import QWebEngineCertificateError
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QToolBar, QLineEdit

from clochette.framework.qt.Link import Link
from clochette.framework.qt.Signal import InHollowSignal, InSolidSignal, OutHollowSignal
from clochette.presentation.theme.ThemeService import ThemeService
from clochette.presentation.window.QAbstractWindow import QAbstractWindow

# it doesn't seem to work on my environment without this
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"


def on_cert_error(e: QWebEngineCertificateError) -> None:
    """
    Accept certificates no matter what, useful for clochette tu use https servers on localhost with self-signed certs
    :param e:
    :return:
    """
    e.acceptCertificate()


class QWebBrowserWindow(QAbstractWindow):
    _web_view: QWebEngineView
    _address_bar: QLineEdit
    _back_action: QAction
    _forward_action: QAction
    _reload_action: QAction

    hide_browser: InHollowSignal
    show_browser: InHollowSignal
    load_url: InSolidSignal[str]

    on_browser_closed: OutHollowSignal

    def __init__(self, theme_service: ThemeService) -> None:
        super().__init__(theme_service.icon_window, self.tr("Clochette - Web Browser"))

        self.hide_browser = InHollowSignal(super().hide)
        self.show_browser = InHollowSignal(super().show)
        self.load_url = InSolidSignal(self._load_url)
        self.on_browser_closed = OutHollowSignal()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Navigation toolbar
        navigation_toolbar = QToolBar(self.tr("Navigation"))
        navigation_toolbar.setIconSize(navigation_toolbar.iconSize() * 0.7)
        layout.addWidget(navigation_toolbar)

        # Back button
        self._back_action = QAction(QIcon(), self.tr("Back"), self)
        self._back_action.setStatusTip(self.tr("Back to previous page"))
        self._back_action.triggered.connect(self._on_back)
        navigation_toolbar.addAction(self._back_action)

        # Forward button
        self._forward_action = QAction(QIcon(), self.tr("Forward"), self)
        self._forward_action.setStatusTip(self.tr("Forward to next page"))
        self._forward_action.triggered.connect(self._on_forward)
        navigation_toolbar.addAction(self._forward_action)

        # Reload button
        self._reload_action = QAction(QIcon(), self.tr("Reload"), self)
        self._reload_action.setStatusTip(self.tr("Reload page"))
        self._reload_action.triggered.connect(self._on_reload)
        navigation_toolbar.addAction(self._reload_action)

        # Subscribe to icon observables with thread-safe signals
        Link(
            observable=theme_service.icon_browser_back,
            handler=lambda icon: self._back_action.setIcon(icon),
            widget=self,
        )
        Link(
            observable=theme_service.icon_browser_forward,
            handler=lambda icon: self._forward_action.setIcon(icon),
            widget=self,
        )
        Link(
            observable=theme_service.icon_browser_reload,
            handler=lambda icon: self._reload_action.setIcon(icon),
            widget=self,
        )

        # Address bar
        self._address_bar = QLineEdit()
        self._address_bar.returnPressed.connect(self._on_navigate_to_url)
        navigation_toolbar.addWidget(self._address_bar)

        # Web view
        self._web_view = QWebEngineView()
        self._web_view.page().certificateError.connect(on_cert_error)
        self._web_view.urlChanged.connect(self._on_url_changed)

        self.resize(600, 800)
        layout.addWidget(self._web_view)

    def _load_url(self, url: str) -> None:
        self._web_view.load(QUrl(url))
        self._address_bar.setText(url)

    def _on_back(self) -> None:
        self._web_view.back()

    def _on_forward(self) -> None:
        self._web_view.forward()

    def _on_reload(self) -> None:
        self._web_view.reload()

    def _on_navigate_to_url(self) -> None:
        url = self._address_bar.text()
        self._web_view.load(QUrl(url))

    def _on_url_changed(self, url: QUrl) -> None:
        self._address_bar.setText(url.toString())

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        self.on_browser_closed.send()
        super().closeEvent(event)
