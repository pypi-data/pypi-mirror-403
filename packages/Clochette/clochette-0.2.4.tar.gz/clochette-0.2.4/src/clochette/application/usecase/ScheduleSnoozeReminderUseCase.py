from dataclasses import dataclass
from datetime import timedelta


from clochette import log
from clochette.application.store.SnoozeScheduleStore import SnoozeScheduleStore
from clochette.application.usecase.CheckForSnoozeUseCase import CheckForSnoozeUseCase
from clochette.infrastructure.schedule.SchedulerService import SchedulerService


@dataclass
class ScheduleSnoozeReminderUseCase:
    """Use case to schedule snooze reminder checks."""

    _snooze_schedule_store: SnoozeScheduleStore
    _check_for_snooze_use_case: CheckForSnoozeUseCase
    _scheduler_service: SchedulerService

    def schedule_snooze_reminders(self) -> None:
        """Schedule periodic snooze reminder checks."""
        log.info("Scheduling snooze reminder checks")

        task_id = self._scheduler_service.schedule_at_interval(
            timedelta(seconds=10),
            self._check_for_snooze_use_case.check_for_snoozes,
        )

        self._snooze_schedule_store.set_schedule_id(task_id)
        log.debug(f"Scheduled snooze reminder checks, task_id: {task_id}")
