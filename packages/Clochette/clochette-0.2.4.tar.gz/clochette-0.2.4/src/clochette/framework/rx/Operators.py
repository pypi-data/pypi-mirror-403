from typing import Optional, Callable, TypeVar

from reactivex import Observable, just, throw
from reactivex import operators as ops

from clochette import log

_T = TypeVar("_T")


def retry_with_delay(
    delay_ms: float,
    retry_count: Optional[int] = None,
) -> Callable[[Observable[_T]], Observable[_T]]:
    def delay(ex: Exception, _: Observable[_T]) -> Observable[_T]:
        log.debug("retry_with_delay", exc_info=ex)
        return just(0).pipe(
            ops.delay(delay_ms),
            ops.flat_map(lambda _: throw(ex)),
        )

    def retry(source: Observable[_T]) -> Observable[_T]:
        return source.pipe(
            ops.catch(handler=delay),
            ops.retry(retry_count),
        )

    return retry
