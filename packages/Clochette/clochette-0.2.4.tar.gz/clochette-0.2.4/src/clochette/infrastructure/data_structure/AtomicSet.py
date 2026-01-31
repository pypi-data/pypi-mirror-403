import threading
from typing import Generic, TypeVar

_T = TypeVar("_T")


class AtomicSet(Generic[_T]):
    def __init__(self):
        self._set = set()
        self._lock = threading.Lock()

    def contains_or_add(self, element: _T) -> bool:
        with self._lock:
            if element in self._set:
                return True
            else:
                self._set.add(element)
                return False
