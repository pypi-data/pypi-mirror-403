from configparser import SectionProxy

from clochette import log


def read_int(section: SectionProxy, key_name: str, fallback: int) -> int:
    try:
        return int(section.get(key_name, str(fallback)))
    except Exception:
        log.warning(f"Failed to parse config item: {key_name}, using fallback: {fallback}", exc_info=True)
        return fallback


def read_str(section: SectionProxy, key_name: str, fallback: str) -> str:
    try:
        return section.get(key_name, fallback)
    except Exception:
        log.warning(f"Failed to parse config item: {key_name}, using fallback: {fallback}", exc_info=True)
        return fallback


def read_bool(section: SectionProxy, key_name: str, fallback: bool) -> bool:
    try:
        return section.get(key_name, str(fallback)).upper() == "TRUE"
    except Exception:
        log.warning(f"Failed to parse config item: {key_name}, using fallback: {fallback}", exc_info=True)
        return fallback
