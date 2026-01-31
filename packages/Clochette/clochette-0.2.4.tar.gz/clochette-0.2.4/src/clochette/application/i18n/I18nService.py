from PySide6.QtCore import QTranslator

from clochette import log
from clochette.application.i18n.LangHelper import apply_i18n
from clochette.application.i18n.LocaleProvider import LocaleProvider

_SUPPORTED_LANGUAGES = {
    "vi_VN": "clochette_vi.qm",
    "fr_FR": "clochette_fr.qm",
}
_DEFAULT_LANGUAGE = "en_GB"


class I18nService:
    """Service for loading and managing application translations."""

    def __init__(self, locale_provider: LocaleProvider):
        self._locale_provider = locale_provider

    def load_translations(self, translator: QTranslator) -> None:
        """Load appropriate translation based on system locale."""
        system_locale = self._locale_provider.get_system_locale().name()
        translation_file = _SUPPORTED_LANGUAGES.get(system_locale, None)

        if system_locale == _DEFAULT_LANGUAGE:
            apply_i18n(_DEFAULT_LANGUAGE)
            log.info(f"Loaded {system_locale} translation")
        elif translation_file is not None:
            resource_path = f":/translations/{translation_file}"
            self._load_translation(translator, resource_path)
            apply_i18n(system_locale)
            log.info(f"Loaded {system_locale} translation")
            return
        else:
            log.info(f"Language '{system_locale}' not supported, using default ({_DEFAULT_LANGUAGE})")
            apply_i18n(_DEFAULT_LANGUAGE)

    def _load_translation(self, translator: QTranslator, path: str) -> None:
        if translator.load(path):
            log.info(f"Loaded translation from Qt resources: {path}")
        else:
            log.warning(f"Failed to load translation from Qt resources: {path}")
