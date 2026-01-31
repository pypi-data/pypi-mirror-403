from typing import TypeVar, Callable

from PySide6.QtCore import QObject
from reactivex import Observable
from reactivex.abc import DisposableBase

from clochette import log
from clochette.framework.qt.Signal import InSolidSignal
from clochette.framework.rx.Scheduler import scheduler

_T = TypeVar("_T")


class Link:
    """
    Helper class to link an Observable to a handler method via an InSignal for thread safety.

    Automatically handles:
    - Creating an InSignal to make the handler thread-safe
    - Subscribing the Observable to the InSignal
    - Disposing the subscription when the widget is destroyed

    Example:
        Link(
            observable=store.some_observable,
            handler=self._on_value_changed,
            widget=self._view
        )
    """

    _disposable: DisposableBase

    def __init__(
        self,
        observable: Observable[_T],
        handler: Callable[[_T], None],
        widget: QObject,
    ):
        """
        Link an Observable to a handler method via an InSignal.

        Args:
            observable: The Observable to subscribe to
            handler: The method to call when the Observable emits (will be wrapped in InSignal)
            widget: The widget whose destroyed signal will trigger cleanup
        """
        # Create an InSignal to make the handler thread-safe
        in_signal = InSolidSignal(handler)

        # Subscribe the Observable to call the InSignal
        self._disposable = observable.subscribe(
            on_next=lambda value: in_signal(value),
            on_error=lambda e: log.warning("Error in link", exc_info=e),
            scheduler=scheduler,
        )

        # Connect disposal to widget destruction
        widget.destroyed.connect(self._disposable.dispose)
