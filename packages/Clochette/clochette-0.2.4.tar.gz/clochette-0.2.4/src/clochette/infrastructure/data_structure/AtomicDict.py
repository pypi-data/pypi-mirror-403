import threading
from typing import Generic, TypeVar, Any, Iterator, ItemsView, KeysView, ValuesView

_K = TypeVar("_K")
_V = TypeVar("_V")


class AtomicDict(Generic[_K, _V]):
    _lock: threading.Lock
    _dict: dict[_K, _V]

    def __init__(self, initial_dict: dict[_K, _V]):
        self._lock = threading.Lock()
        self._dict = initial_dict

    def __getitem__(self, key: _K) -> _V:
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key: _K, _Value: _V) -> None:
        with self._lock:
            self._dict[key] = _Value

    def __delitem__(self, key: _K) -> None:
        with self._lock:
            del self._dict[key]

    def __contains__(self, key: _K) -> bool:
        with self._lock:
            return key in self._dict

    def get(self, key: _K, default: _V | None = None) -> _V | None:
        with self._lock:
            return self._dict.get(key, default)

    def pop(self, key: _K, *args: Any) -> _V:
        with self._lock:
            return self._dict.pop(key, *args)

    def __len__(self) -> int:
        with self._lock:
            return len(self._dict)

    def __iter__(self) -> Iterator[_K]:
        with self._lock:
            return iter(self._dict.copy())

    def items(self) -> ItemsView[_K, _V]:
        with self._lock:
            return self._dict.copy().items()

    def keys(self) -> KeysView[_K]:
        with self._lock:
            return self._dict.copy().keys()

    def _values(self) -> ValuesView[_V]:
        with self._lock:
            return self._dict.copy().values()
