from dataclasses import dataclass

from reactivex import operators as ops, Observable

from clochette import log
from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.application.usecase.PersistConfigurationUseCase import PersistConfigurationUseCase
from clochette.domain.entity.configuration.ThemeConfiguration import ThemeConfiguration
from clochette.framework.rx.Scheduler import scheduler


@dataclass
class UpdateThemeUseCase:
    """Use case to update theme configuration in the store."""

    _general_configuration_store: GeneralConfigurationStore
    _persist_configuration_usecase: PersistConfigurationUseCase

    def update_theme(self, theme: ThemeConfiguration) -> Observable[None]:
        """Update both window and systray icon themes."""
        log.info(f"Updating themes: {theme}")
        self._general_configuration_store.set_theme(theme)

        # Persist to disk
        return self._persist_configuration_usecase.persist_configuration().pipe(
            ops.do_action(
                on_error=lambda e: log.error(f"Failed to persist theme configuration", exc_info=e),
            ),
            ops.subscribe_on(scheduler=scheduler),
        )
