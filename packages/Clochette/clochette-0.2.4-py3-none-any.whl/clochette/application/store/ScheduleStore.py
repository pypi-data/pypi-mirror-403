from uuid import UUID

from reactivex import Observable
from reactivex.abc import DisposableBase

from clochette import log


class ScheduleStore:
    """Store for managing scheduler subscriptions and tasks."""

    _subscriptions: dict[UUID, DisposableBase]
    _tasks: dict[UUID, Observable[None]]

    def __init__(self):
        self._subscriptions = {}
        self._tasks = {}

    def store_subscription(self, task_id: UUID, subscription: DisposableBase) -> None:
        """Store a subscription with the given task ID."""
        self._subscriptions[task_id] = subscription

    def store_task(self, task_id: UUID, task: Observable[None]) -> None:
        """Store a task Observable with the given task ID."""
        self._tasks[task_id] = task

    def get_subscription(self, task_id: UUID) -> DisposableBase | None:
        """Retrieve a subscription by task ID."""
        return self._subscriptions.get(task_id)

    def get_task(self, task_id: UUID) -> Observable[None] | None:
        """Retrieve a task Observable by task ID."""
        return self._tasks.get(task_id)

    def remove_subscription(self, task_id: UUID) -> DisposableBase | None:
        """Remove and return a subscription by task ID."""
        self._tasks.pop(task_id, None)  # Also remove the task
        return self._subscriptions.pop(task_id, None)

    def get_all_subscriptions(self) -> dict[UUID, DisposableBase]:
        """Get all subscriptions."""
        return self._subscriptions.copy()

    def clear_all_subscriptions(self) -> None:
        """Clear all subscriptions and tasks."""
        for task_id, subscription in self._subscriptions.items():
            try:
                subscription.dispose()
            except Exception:
                log.error(f"Failed to dispose subscription, task_id: {task_id}", exc_info=True)

        self._subscriptions.clear()
        self._tasks.clear()
