from dataclasses import dataclass

from reactivex import operators as ops, Observable

from clochette import log
from clochette.application.repository.CalendarAuthenticationRepository import CalendarAuthenticationRepository
from clochette.application.repository.CalendarRepository import CalendarRepository
from clochette.application.store.CalendarConfigurationStore import CalendarConfigurationStore
from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.application.usecase.ScheduleAllCalendarsDownloadUseCase import ScheduleAllCalendarsDownloadUseCase
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.framework.rx.Scheduler import scheduler
from clochette.infrastructure.mapper.Mapper import Mapper
from clochette.persist.configuration.ConfigurationReaderService import ConfigurationReaderService
from clochette.persist.configuration.dto.GlobalConfigurationDTO import GlobalConfigurationDTO


@dataclass
class LoadConfigurationUseCase:
    """Use case to load configuration from disk and populate the configuration stores."""

    _configuration_reader_service: ConfigurationReaderService
    _calendar_configuration_store: CalendarConfigurationStore
    _general_configuration_store: GeneralConfigurationStore
    _calendar_authentication_repository: CalendarAuthenticationRepository
    _calendar_repository: CalendarRepository
    _schedule_all_calendars_download_usecase: ScheduleAllCalendarsDownloadUseCase
    _mapper: Mapper

    def load_configuration(self) -> Observable[None]:
        return self._configuration_reader_service.read().pipe(
            ops.do_action(
                on_next=lambda x: self._load_configuration(x),
                on_error=lambda e: log.error(f"Failed to reade configuration", exc_info=e),
            ),
            ops.subscribe_on(scheduler=scheduler),
            ops.map(lambda _: None),
        )

    def _load_configuration(self, global_config_dto: GlobalConfigurationDTO) -> None:
        calendars = [
            self._mapper.map(CalendarConfiguration, calendar_dto) for calendar_dto in global_config_dto.calendars
        ]
        self._general_configuration_store.set_snoozes(global_config_dto.snoozes)
        self._general_configuration_store.set_theme(global_config_dto.theme)
        self._calendar_configuration_store.set_calendars(calendars)
        self._cleanup_calendars(calendars)
        self._update_calendar_repository(calendars)
        self._schedule_all_calendars_download_usecase.schedule_all_calendars(calendars)

    def _cleanup_calendars(self, calendars: list[CalendarConfiguration]):
        ids_to_keep = [calendar.id for calendar in calendars]
        self._calendar_authentication_repository.cleanup_calendars(ids_to_keep)

    def _update_calendar_repository(self, calendars: list[CalendarConfiguration]) -> None:
        """Update calendar repository with the given calendar configurations."""
        if not calendars:
            log.warning("No calendars found in the configuration.")

        log.info(f"Updating calendar repository. Calendars: {calendars}")
        self._calendar_repository.set_calendars(calendars)
