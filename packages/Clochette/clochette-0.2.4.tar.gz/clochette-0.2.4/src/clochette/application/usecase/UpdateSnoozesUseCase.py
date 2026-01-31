from dataclasses import dataclass

from reactivex import Observable
from reactivex import operators as ops

from clochette import log
from clochette.application.store.GeneralConfigurationStore import GeneralConfigurationStore
from clochette.application.usecase.PersistConfigurationUseCase import PersistConfigurationUseCase
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta
from clochette.framework.rx.Scheduler import scheduler


@dataclass
class UpdateSnoozesUseCase:
    """Use case to update snooze configuration in the store."""

    _general_configuration_store: GeneralConfigurationStore
    _persist_configuration_usecase: PersistConfigurationUseCase

    def update_snoozes(self, snoozes: list[SnoozeDelta]) -> Observable[None]:
        """Update snooze deltas and persist to disk."""
        log.info(f"Updating snoozes: {snoozes}")
        self._general_configuration_store.set_snoozes(snoozes)

        # Persist to disk
        return self._persist_configuration_usecase.persist_configuration().pipe(
            ops.map(lambda _: None),
            ops.do_action(on_error=lambda e: log.error(f"Failed to persist snooze configuration", exc_info=e)),
            ops.subscribe_on(scheduler=scheduler),
        )
