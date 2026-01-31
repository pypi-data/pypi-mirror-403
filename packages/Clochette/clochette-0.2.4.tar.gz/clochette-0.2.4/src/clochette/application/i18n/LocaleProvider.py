from PySide6.QtCore import QLocale


class LocaleProvider:
    """Service for providing the system locale.

    This service exists to make locale retrieval mockable in tests,
    since QLocale.system() is static and difficult to mock directly.
    """

    def get_system_locale(self) -> QLocale:
        """Get the system locale.

        Returns:
            The current system locale.
        """
        return QLocale.system()
