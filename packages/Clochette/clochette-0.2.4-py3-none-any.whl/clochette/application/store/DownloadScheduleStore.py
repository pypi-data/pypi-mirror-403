from uuid import UUID

from reactivex import Observable, operators as ops
from reactivex.subject import BehaviorSubject

from clochette import log
from clochette.domain.entity.CalendarID import CalendarID
from clochette.framework.rx.Scheduler import scheduler


class DownloadScheduleStore:
    """Store for managing download schedule task IDs mapped to calendar IDs using RxPY subjects."""

    _schedule_ids: BehaviorSubject[dict[CalendarID, UUID]]

    def __init__(self):
        self._schedule_ids = BehaviorSubject({})

    @property
    def schedule_ids(self) -> Observable[dict[CalendarID, UUID]]:
        """Observable for the schedule IDs dictionary."""
        return self._schedule_ids

    def set_schedule_id(self, calendar_id: CalendarID, task_id: UUID) -> None:
        """Store a scheduler task ID for a calendar."""
        self._schedule_ids.pipe(
            ops.take(1),
        ).subscribe(
            on_next=lambda current_dict: self._schedule_ids.on_next({**current_dict, calendar_id: task_id}),
            on_error=lambda e: log.error(f"Error while storing schedule ID: {e}", exc_info=e),
            scheduler=scheduler,
        )

    def remove_schedule_id(self, calendar_id: CalendarID) -> Observable[UUID | None]:
        """Remove and return an Observable of the scheduler task ID for a calendar, or None if not found."""

        def remove_and_emit(current_dict: dict[CalendarID, UUID]) -> UUID | None:
            new_dict = current_dict.copy()
            removed_task_id = new_dict.pop(calendar_id, None)
            self._schedule_ids.on_next(new_dict)
            return removed_task_id

        return self._schedule_ids.pipe(
            ops.take(1),
            ops.map(remove_and_emit),
        )
