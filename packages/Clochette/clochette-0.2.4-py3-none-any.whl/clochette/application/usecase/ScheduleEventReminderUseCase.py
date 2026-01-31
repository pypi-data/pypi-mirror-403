from dataclasses import dataclass
from datetime import timedelta

from clochette import log
from clochette.application.store.EventScheduleStore import EventScheduleStore
from clochette.application.usecase.CheckForEventUseCase import CheckForEventUseCase
from clochette.infrastructure.schedule.SchedulerService import SchedulerService


@dataclass
class ScheduleEventReminderUseCase:
    """Use case to schedule event reminder checks."""

    _event_schedule_store: EventScheduleStore
    _check_for_event_use_case: CheckForEventUseCase
    _scheduler_service: SchedulerService

    def schedule_event_reminders(self) -> None:
        """Schedule periodic event reminder checks."""
        log.info("Scheduling event reminder checks")

        task_id = self._scheduler_service.schedule_at_interval(
            timedelta(seconds=10),
            self._check_for_event_use_case.check_for_events,
        )

        self._event_schedule_store.set_schedule_id(task_id)
        log.debug(f"Scheduled event reminder checks, task_id: {task_id}")
