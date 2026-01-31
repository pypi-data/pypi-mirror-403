from dataclasses import dataclass

from reactivex import combine_latest, operators as ops, Observable

from clochette import log
from clochette.application.store.CalendarConfigurationStore import CalendarConfigurationStore
from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration
from clochette.framework.rx.Scheduler import scheduler
from clochette.infrastructure.mapper.Mapper import Mapper
from clochette.persist.configuration.ConfigurationWriterService import ConfigurationWriterService
from clochette.persist.configuration.dto.CalendarConfigurationDTO import CalendarConfigurationDTO
from clochette.persist.configuration.dto.GlobalConfigurationDTO import GlobalConfigurationDTO


@dataclass
class PersistConfigurationUseCase:
    """Use case to persist calendar configuration to disk."""

    _calendar_configuration_store: CalendarConfigurationStore
    _general_configuration_store: GeneralConfigurationStore
    _configuration_writer_service: ConfigurationWriterService
    _mapper: Mapper

    def persist_configuration(self) -> Observable[None]:
        """Retrieve current configuration from stores and persist to disk."""

        return combine_latest(
            self._calendar_configuration_store.calendars.pipe(ops.take(1)),
            self._general_configuration_store.snoozes.pipe(ops.take(1)),
            self._general_configuration_store.theme.pipe(ops.take(1)),
        ).pipe(
            ops.map(self._build_global_config_dto),
            ops.flat_map(self._configuration_writer_service.write),
            ops.do_action(on_error=lambda e: log.error(f"Failed to persist configuration", exc_info=e)),
            ops.subscribe_on(scheduler=scheduler),
        )

    def _build_global_config_dto(
        self, values: tuple[list[CalendarConfiguration], list[SnoozeDelta], ThemeConfiguration]
    ) -> GlobalConfigurationDTO:
        """Build GlobalConfigurationDTO from store values."""
        calendars, snoozes, theme = values
        calendar_dtos = [self._mapper.map(CalendarConfigurationDTO, cal) for cal in calendars]
        return GlobalConfigurationDTO(snoozes=snoozes, calendars=calendar_dtos, theme=theme)
