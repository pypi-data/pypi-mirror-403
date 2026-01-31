from dataclasses import dataclass
from uuid import UUID

from reactivex import operators as ops, Observable

from clochette import log
from clochette.application.store.DownloadScheduleStore import DownloadScheduleStore
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler
from clochette.infrastructure.schedule.SchedulerService import SchedulerService


@dataclass
class UnscheduleCalendarDownloadUseCase:
    """Use case to unschedule downloads for a calendar."""

    _download_schedule_store: DownloadScheduleStore
    _scheduler_service: SchedulerService

    def unschedule_calendar(self, calendar: CalendarConfiguration) -> Observable[None]:
        """Unschedule downloads for a calendar."""
        log.info(f"Unscheduling downloads for calendar: {calendar.name}")

        def handle_task_id(task_id: UUID | None) -> None:
            if task_id is None:
                log.warning(f"Task ID not found when unscheduling calendar named: {calendar.name}")
            else:
                self._scheduler_service.unsubscribe(task_id)
                log.debug(f"Unscheduled calendar download: {calendar.name}, task_id: {task_id}")

        return self._download_schedule_store.remove_schedule_id(calendar.id).pipe(
            ops.do_action(
                on_next=lambda tasks_id: handle_task_id(tasks_id),
                on_error=lambda e: log.error(f"Failed to unschedule calendar named: {calendar.name}", exc_info=e),
            ),
            ops.map(lambda _: None),
            ops.subscribe_on(scheduler=scheduler),
        )
