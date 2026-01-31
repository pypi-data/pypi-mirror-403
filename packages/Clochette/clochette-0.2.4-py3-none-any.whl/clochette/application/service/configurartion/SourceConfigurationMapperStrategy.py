from configparser import SectionProxy
from dataclasses import dataclass

from reactivex import Observable, operators as ops

from clochette.application.service.provider.dto.ProviderDTO import ProviderDTO
from clochette.application.store.ProviderStore import ProviderStore
from clochette.domain.entity.ISourceCalendar import ISourceCalendar


@dataclass
class SourceConfigurationMapperStrategy:
    _provider_store: ProviderStore

    def read(self, section: SectionProxy) -> Observable[ISourceCalendar]:

        def find_provider_for_section(providers: list[ProviderDTO], section: SectionProxy) -> ProviderDTO | None:
            """Find the provider whose mapper matches this section."""
            for provider_dto in providers:
                if provider_dto.provider_configuration_mapper.match(section):
                    return provider_dto
            return None

        def check_result(result: ISourceCalendar | None) -> ISourceCalendar:
            if result is None:
                raise Exception("Failed to parse calendar configuration, no matching provider found")
            return result

        return self._provider_store.providers.pipe(
            ops.take(1),
            ops.map(lambda providers: find_provider_for_section(providers, section)),
            ops.map(lambda p: p.provider_configuration_mapper.read(section) if p else None),
            ops.map(check_result),
        )

    def write(self, source: ISourceCalendar) -> Observable[dict[str, str]]:

        def find_provider_for_source(providers: list[ProviderDTO], source: ISourceCalendar) -> ProviderDTO | None:
            """Find the provider that matches this source's provider type."""
            for provider_dto in providers:
                if source.provider_type == provider_dto.provider_type:
                    return provider_dto
            return None

        def check_result(result: dict[str, str] | None) -> dict[str, str]:
            if result is None:
                raise Exception(f"Unsupported provider type: {source.provider_type}")
            return result

        return self._provider_store.providers.pipe(
            ops.take(1),
            ops.map(lambda providers: find_provider_for_source(providers, source)),
            ops.map(lambda p: p.provider_configuration_mapper.write(source) if p else None),
            ops.map(check_result),
        )
