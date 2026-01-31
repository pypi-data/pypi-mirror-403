from __future__ import annotations
from typing import TypeVar, Generic, Iterator, Iterable, Callable

_T = TypeVar("_T")


class PeekableIterator(Generic[_T]):
    _iterator: Iterator[_T]
    _buffer: list[_T]

    def __init__(self, iterable: Iterable[_T]) -> None:
        self._iterator: Iterator[_T] = iter(iterable)
        self._buffer: list[_T] = []

    def __iter__(self) -> Iterator[_T]:
        return self

    def __next__(self) -> _T:
        if self._buffer:
            return self._buffer.pop()
        return next(self._iterator)

    def _peek(self) -> _T:
        if not self._buffer:
            try:
                trigger = next(self._iterator)
                self._buffer.append(trigger)
            except StopIteration:
                raise StopIteration("No more items to peek")
        return self._buffer[-1]


def take_while(iterator: PeekableIterator[_T], predicate: Callable[[_T], bool]) -> list[_T]:
    result: list[_T] = []
    while True:
        current_value = peek(iterator)
        if current_value is None:
            break

        if predicate(current_value):
            result.append(next(iterator))
        else:
            break

    return result


def peek(iterator: PeekableIterator):
    try:
        return iterator._peek()
    except StopIteration:
        return None
