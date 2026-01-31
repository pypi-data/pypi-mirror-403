from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from reactivex import operators as ops, Observable, defer, just

from clochette import log
from clochette.application.service.EventModel import EventModel
from clochette.application.service.ical.ICalendarService import ICalendarService
from clochette.application.usecase.RestoreSnoozeUseCase import RestoreSnoozeUseCase
from clochette.domain.entity.CalendarEventQuery import CalendarEventQuery
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Operators import retry_with_delay
from clochette.infrastructure.clock.ClockService import ClockService
from clochette.application.repository.CalendarCacheRepository import CalendarCacheRepository
from clochette.application.repository.CalendarRepository import CalendarRepository
from clochette.application.service.download.CalendarDownloaderStrategyService import CalendarDownloaderStrategy


@dataclass
class DownloaderService:
    _calendar_downloader_strategy: CalendarDownloaderStrategy
    _icalendar_service: ICalendarService
    _event_model: EventModel
    _calendar_repository: CalendarRepository
    _calendar_cache_repository: CalendarCacheRepository
    _clock_service: ClockService
    _restore_snooze_use_case: RestoreSnoozeUseCase
    _retry_delay: float = field(default=10.0)

    def download_and_notify(self, calendar_configuration: CalendarConfiguration) -> Observable:
        return defer(lambda _: self._download_and_notify(calendar_configuration))

    def _download_and_notify(self, calendar_configuration: CalendarConfiguration) -> Observable:
        log.debug(f"Downloading calendar, id: {calendar_configuration.id}, name: {calendar_configuration.name}")
        calendar = self._calendar_repository.get_calendar(calendar_configuration.id)
        now = self._clock_service.utc_now()

        def get_last_download() -> datetime:
            if calendar.last_download < now + calendar_configuration.missed_reminders_past_window:
                latest = now + calendar_configuration.missed_reminders_past_window
                log.info(
                    f"Clochette hasn't downloaded this calendar for a while,"
                    f" processing events since: {latest}, calendar: {calendar_configuration.name}"
                )
                return latest
            else:
                log.debug(
                    f"Downloading calendar and processing event since: {calendar.last_download},"
                    f" calendar: {calendar_configuration.name}"
                )
                return calendar.last_download

        def update_model(query: CalendarEventQuery | None) -> None:
            if query is not None:
                self._event_model.add_query(calendar.calendar_id, query)

        def parse_ics(ics: str | None) -> CalendarEventQuery | None:
            if ics is not None:
                last_download = get_last_download()
                calendar_event_query = self._icalendar_service.parse_calendar(
                    calendar_configuration, ics, last_download, calendar.calendar_id
                )
                self._calendar_repository.update_calendar_last_download(calendar.calendar_id, now)
                return calendar_event_query
            return None

        def restore_snoozes(_: Any) -> None:
            self._restore_snooze_use_case.restore_snooze(calendar.calendar_id)

        def cache_calendar(ics_content: str | None) -> None:
            """Cache the downloaded ICS content if successful."""
            if ics_content is not None:
                self._calendar_cache_repository.cache_calendar(calendar_configuration.id, ics_content)

        def handle_download_failed(ex: Exception, __: Any) -> Observable[str | None]:
            """Fallback to cached content when download fails."""
            log.warning(
                f"Download failed for calendar '{calendar_configuration.name}', attempting cache fallback.",
                exc_info=ex,
            )
            cache = self._calendar_cache_repository.get_calendar_cache(calendar_configuration.id)
            if cache:
                log.info(f"Using cached content for calendar '{calendar_configuration.name}'")
                return just(cache)
            else:
                log.error(f"No cached content found for calendar '{calendar_configuration.name}'")
                return just(None)

        def download() -> Observable[str | None]:
            return self._calendar_downloader_strategy.download(calendar_configuration).pipe(
                retry_with_delay(self._retry_delay, 3),
                ops.do_action(on_next=cache_calendar),
                ops.catch(handle_download_failed),
            )

        log.info(f"Start downloading the ics file, calendar: {calendar_configuration.name}")
        return download().pipe(
            ops.map(parse_ics),
            ops.do_action(on_next=restore_snoozes),
            ops.do_action(on_next=update_model),
            ops.do_action(
                on_error=lambda e: log.error(f"Failed to process calendar: {calendar_configuration.name}", exc_info=e)
            ),
        )
