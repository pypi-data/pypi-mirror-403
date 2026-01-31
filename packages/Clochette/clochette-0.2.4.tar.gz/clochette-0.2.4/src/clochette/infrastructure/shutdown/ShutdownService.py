import sys
from typing import Callable, Tuple

from clochette import log


class ShutdownService:
    _closeables: list[Tuple[str, Callable[[], None]]]

    def __init__(self) -> None:
        self._closeables = []

    def register(self, name: str, closeable: Callable[[], None]) -> None:
        self._closeables.append((name, closeable))

    def close(self) -> None:
        log.info("Shutting down application")
        for closeable_tuple in self._closeables:
            name, closeable = closeable_tuple
            try:
                closeable()
            except Exception:
                log.error(f"Failed to close closeable: {name}", exc_info=True)
        sys.exit(0)
