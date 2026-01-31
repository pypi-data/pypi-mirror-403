from uuid import UUID

from reactivex import Observable, Subject


class EventScheduleStore:
    """Store for managing the event reminder schedule task ID using RxPY subjects."""

    _schedule_id: Subject[UUID]

    def __init__(self):
        self._schedule_id = Subject()

    @property
    def schedule_id(self) -> Observable[UUID]:
        """Observable for the schedule ID."""
        return self._schedule_id

    def set_schedule_id(self, task_id: UUID) -> None:
        """Store the scheduler task ID for event reminders."""
        self._schedule_id.on_next(task_id)
