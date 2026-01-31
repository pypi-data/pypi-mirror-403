from dataclasses import dataclass

from reactivex import Observable, operators as ops

from clochette.application.service.provider.dto.IDownloadCalendar import IDownloadCalendar
from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.application.store.ProviderStore import ProviderStore
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


@dataclass
class CalendarDownloaderStrategy(IDownloadCalendar):
    _provider_store: ProviderStore

    def download(self, calendar_configuration: CalendarConfiguration) -> Observable[str | None]:
        # Get providers from store and chain to download
        return self._provider_store.providers.pipe(
            ops.take(1),
            ops.flat_map(lambda x: self._find_and_download(calendar_configuration, x)),
        )

    def _find_and_download(
        self,
        calendar_configuration: CalendarConfiguration,
        providers_list: list[ProviderDTO],
    ) -> Observable[str | None]:
        source = calendar_configuration.source
        # Find the provider that matches this source's provider type
        for provider_dto in providers_list:
            if source.provider_type == provider_dto.provider_type:
                return provider_dto.download_calendar.download(calendar_configuration)

        raise Exception(f"Unsupported provider type: {source.provider_type}")
