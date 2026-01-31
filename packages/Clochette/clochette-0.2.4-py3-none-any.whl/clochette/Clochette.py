from dataclasses import dataclass

from clochette import log
from clochette.application.service.provider.ProviderRegisterService import ProviderRegisterService
from clochette.application.usecase.InitializeReminderWindowUseCase import InitializeReminderWindowUseCase
from clochette.application.usecase.LoadConfigurationUseCase import LoadConfigurationUseCase
from clochette.application.usecase.ScheduleEventReminderUseCase import ScheduleEventReminderUseCase
from clochette.application.usecase.ScheduleSnoozeReminderUseCase import ScheduleSnoozeReminderUseCase
from clochette.infrastructure.schedule.SchedulerService import SchedulerService
from clochette.infrastructure.shutdown.ShutdownService import ShutdownService
from clochette.persist.database.DatabaseMigrationService import DatabaseMigrationService
from clochette.presentation.QMainApplication import QMainApplication
from clochette.presentation.systray.SystrayComponent import SystrayComponent


@dataclass
class Clochette:
    _database_migration_service: DatabaseMigrationService
    _scheduler_service: SchedulerService
    _main_application: QMainApplication
    _shutdown_service: ShutdownService
    _provider_register_service: ProviderRegisterService
    _schedule_event_reminder_use_case: ScheduleEventReminderUseCase
    _schedule_snooze_reminder_use_case: ScheduleSnoozeReminderUseCase
    _initialize_reminder_window_use_case: InitializeReminderWindowUseCase
    _systray_component: SystrayComponent
    _load_configuration_use_case: LoadConfigurationUseCase

    def start(self) -> None:
        log.info("Starting Clochette")
        self._shutdown_service.register("Scheduler", self._scheduler_service.stop)
        self._shutdown_service.register("Clochette", self._main_application.stop)

        self._database_migration_service.migrate()
        self._provider_register_service.register_providers()
        self._load_configuration_use_case.load_configuration().subscribe()

        self._schedule_event_reminder_use_case.schedule_event_reminders()
        self._schedule_snooze_reminder_use_case.schedule_snooze_reminders()
        self._initialize_reminder_window_use_case.initialize()
        self._systray_component.show()
        self._main_application.exec()
