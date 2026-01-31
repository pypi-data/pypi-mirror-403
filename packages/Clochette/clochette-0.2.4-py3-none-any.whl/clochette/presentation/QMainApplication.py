import signal
import sys

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

from clochette import log
from clochette.application.i18n.I18nService import I18nService
from clochette.res import resource_rc


class SysArgvProvider:
    def __call__(self) -> list[str]:
        return sys.argv


class QMainApplication:
    _application: QApplication
    _translator: QTranslator
    _i18n_service: I18nService

    def __init__(self, sys_argv_provider: SysArgvProvider, i18n_service: I18nService) -> None:
        _ = resource_rc.qt_resource_data
        # https://stackoverflow.com/questions/5160577/ctrl-c-doesnt-work-with-pyqt
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._application = QApplication(sys_argv_provider())

        self._translator = QTranslator()
        self._application.installTranslator(self._translator)

        i18n_service.load_translations(self._translator)

    def stop(self) -> None:
        log.info("Stopping QT application")
        self._application.exit(1)

    def exec(self) -> None:
        """Start the application"""
        log.info("Starting QT application")
        self._application.exec()
