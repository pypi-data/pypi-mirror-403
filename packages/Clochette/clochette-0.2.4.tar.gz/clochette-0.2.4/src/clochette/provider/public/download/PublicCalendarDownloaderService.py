from dataclasses import dataclass

from reactivex import Observable, from_callable

from clochette import log
from clochette.application.service.provider.dto.IDownloadCalendar import IDownloadCalendar
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.framework.rx.Scheduler import scheduler
from clochette.infrastructure.http_.client.HttpService import HttpService
from clochette.provider.public.configuration.PublicURLSource import PublicURLSource


@dataclass
class PublicCalendarDownloaderService(IDownloadCalendar):
    _http_service: HttpService

    def download(self, calendar_configuration: CalendarConfiguration) -> Observable[str | None]:
        return from_callable(
            lambda: self._download(
                calendar_configuration,
                calendar_configuration.http_timeout,
                calendar_configuration.name,
            ),
            scheduler=scheduler,
        )

    def _download(
        self,
        calendar_configuration: CalendarConfiguration,
        http_timeout: HttpTimeout,
        calendar_name: str,
    ) -> str:
        source = calendar_configuration.source
        if not isinstance(source, PublicURLSource):
            raise TypeError(f"Expected PublicURLSource, got {type(source)}")

        log.info(f"Downloading calendar on public url: {source.url}")

        response = self._http_service.get(source.url, http_timeout=http_timeout)

        if response.is_successful():
            return response.content_utf8 or ""
        else:
            log.error(
                f"Failed to download calendar: {calendar_name}, https status: {response.status_code}",
                exc_info=True,
            )
            raise Exception(f"Failed to download calendar: {calendar_name}, https status: {response.status_code}")
