from dataclasses import dataclass

from clochette import log
from clochette.application.service.download.DownloaderService import DownloaderService
from clochette.application.store.DownloadScheduleStore import DownloadScheduleStore
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.infrastructure.schedule.SchedulerService import SchedulerService


@dataclass
class ScheduleCalendarDownloadUseCase:
    """Use case to schedule downloads for a single calendar."""

    _download_schedule_store: DownloadScheduleStore
    _scheduler_service: SchedulerService
    _downloader_service: DownloaderService

    def schedule_calendar(self, calendar: CalendarConfiguration) -> None:
        """Schedule downloads for a calendar."""
        log.info(f"Scheduling downloads for calendar: {calendar.name}")

        task_id = self._scheduler_service.schedule_at_interval(
            calendar.download_interval,
            self._downloader_service.download_and_notify(calendar),
        )

        self._download_schedule_store.set_schedule_id(calendar.id, task_id)
        log.debug(f"Scheduled calendar download: {calendar.name}, task_id: {task_id}")
