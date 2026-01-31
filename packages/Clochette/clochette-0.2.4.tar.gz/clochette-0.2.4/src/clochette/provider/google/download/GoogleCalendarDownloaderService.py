from dataclasses import dataclass

from reactivex import Observable, from_iterable, defer
from reactivex import operators as ops

from clochette import log
from clochette.application.service.provider.dto.IDownloadCalendar import IDownloadCalendar
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler
from clochette.provider.google.configuration.GoogleSource import GoogleSource
from clochette.provider.google.download.GoogleService import GoogleService


@dataclass
class GoogleCalendarDownloaderService(IDownloadCalendar):
    _google_service: GoogleService

    def download(self, calendar_configuration: CalendarConfiguration) -> Observable[str | None]:
        return defer(lambda _: self._download(calendar_configuration))

    def _download(self, calendar_configuration: CalendarConfiguration) -> Observable[str | None]:
        source = calendar_configuration.source
        if not isinstance(source, GoogleSource):
            raise TypeError(f"Expected GoogleSource, got {type(source)}")

        log.info(f"Downloading Google calendar, name: {calendar_configuration.name}")

        return from_iterable(source.selected_calendars, scheduler=scheduler).pipe(
            ops.do_action(on_next=lambda x: log.debug(f"Downloading Google Calendar with ID: {x}")),
            ops.flat_map(
                lambda cal: self._google_service.download_calendar(
                    calendar_configuration.id, cal, calendar_configuration.http_timeout
                )
            ),
        )
