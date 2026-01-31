from dataclasses import dataclass

from reactivex import Observable, from_callable

from clochette import log
from clochette.application.service.provider.dto.IDownloadCalendar import IDownloadCalendar
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.framework.rx.Scheduler import scheduler
from clochette.provider.basic.configuration.BasicAuthURLSource import BasicAuthURLSource
from clochette.provider.basic.download.BasicAuthService import BasicAuthService


@dataclass
class BasicAuthCalendarDownloaderService(IDownloadCalendar):
    _basic_auth_service: BasicAuthService

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
    ) -> str | None:
        source = calendar_configuration.source
        if not isinstance(source, BasicAuthURLSource):
            raise TypeError(f"Expected BasicAuthURLSource, got {type(source)}")

        log.info(f"Downloading calendar: {calendar_name}")

        return self._basic_auth_service.download(calendar_configuration.id, source, http_timeout)
