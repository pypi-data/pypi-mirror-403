from dataclasses import dataclass
from datetime import timedelta
from typing import Callable
from uuid import UUID, uuid4

from reactivex import Observable, interval, from_callable
from reactivex import operators as ops

from clochette import log
from clochette.framework.rx.Scheduler import scheduler
from clochette.application.store.ScheduleStore import ScheduleStore


@dataclass
class SchedulerService:
    _scheduler_store: ScheduleStore

    def schedule_at_interval(
        self,
        inter: timedelta,
        task: Callable[[], None] | Observable[None],
    ) -> UUID:
        """Schedule a task to run at the given interval. Returns the task ID."""
        task_id = uuid4()
        interval_seconds = inter.total_seconds()
        task_obs = self._make_task_observable(task)

        log.debug(f"Schedule new task at interval: {inter}, task_id: {task_id}")

        subscription = (
            interval(interval_seconds, scheduler=scheduler)
            .pipe(
                ops.start_with(0),  # Emit immediately instead of waiting for first interval
                ops.flat_map(lambda _: task_obs),
            )
            .subscribe(
                on_next=lambda _: log.debug(f"Running scheduled task: {task_id}"),
                on_error=lambda e: log.error(f"Scheduled task failed, task_id: {task_id}", exc_info=e),
                scheduler=scheduler,
            )
        )

        self._scheduler_store.store_subscription(task_id, subscription)
        self._scheduler_store.store_task(task_id, task_obs)
        return task_id

    def unsubscribe(self, task_id: UUID) -> bool:
        """Unsubscribe a task by its ID. Returns True if the task was found and unsubscribed."""
        subscription = self._scheduler_store.remove_subscription(task_id)
        if subscription:
            try:
                subscription.dispose()
                log.debug(f"Unsubscribed task, task_id: {task_id}")
                return True
            except Exception:
                log.error(f"Failed to dispose subscription, task_id: {task_id}", exc_info=True)
                return False
        else:
            log.warning(f"Task not found for unsubscribe, task_id: {task_id}")
            return False

    def execute_task(self, task_id: UUID) -> None:
        """Execute a scheduled task once by its ID."""
        task = self._scheduler_store.get_task(task_id)
        if task:
            log.debug(f"Manually executing task: {task_id}")
            task.subscribe(
                on_error=lambda e: log.error(f"Task execution failed, task_id: {task_id}", exc_info=e),
                scheduler=scheduler,
            )
        else:
            log.warning(f"Task not found for execution, task_id: {task_id}")

    def stop(self) -> None:
        """Stop all scheduled tasks."""
        log.info("Stopping scheduler")
        self._scheduler_store.clear_all_subscriptions()

    def _make_task_observable(self, task: Callable[[], None] | Observable[None]) -> Observable[None]:
        # Create a function that returns an Observable for each interval tick
        if isinstance(task, Observable):
            return task
        else:
            return from_callable(task, scheduler=scheduler)
