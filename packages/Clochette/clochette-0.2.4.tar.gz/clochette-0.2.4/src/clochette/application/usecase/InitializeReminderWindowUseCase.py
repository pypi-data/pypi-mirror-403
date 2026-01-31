from dataclasses import dataclass

from clochette.presentation.reminder_window.ReminderWindowComponent import (
    ReminderWindowComponent,
)


@dataclass
class InitializeReminderWindowUseCase:
    """Use case to initialize and start the reminder window component."""

    _reminder_window_component: ReminderWindowComponent

    def initialize(self) -> None:
        """Initialize the reminder window by subscribing to occurrence updates."""
        self._reminder_window_component.start()
