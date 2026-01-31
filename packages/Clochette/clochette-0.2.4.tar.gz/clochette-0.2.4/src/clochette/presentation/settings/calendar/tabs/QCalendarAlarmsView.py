from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from clochette.domain.entity.delta.AlarmDelta import AlarmDelta
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.presentation.widget.QTimedeltaListWidget import QTimedeltaListWidget
from clochette.presentation.widget.QTitle import QTitle


class QCalendarAlarmsView(QWidget):
    """Widget for calendar alarm settings: force alarms and default alarms for events and all-day events"""

    _force_alarms_widget: QTimedeltaListWidget[AlarmDelta]
    _force_alarms_dates_widget: QTimedeltaListWidget[AlarmDelta]
    _default_alarms_widget: QTimedeltaListWidget[AlarmDelta]
    _default_alarms_dates_widget: QTimedeltaListWidget[AlarmDelta]

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Force Alarms Section
        main_layout.addWidget(
            QTitle(
                self.tr("Force Alarms"),
                self.tr("Always append this alarm to the event whether it has alarms already or not"),
            )
        )

        # Force alarms for normal events
        force_alarms_label = QLabel(self.tr("Normal Events"))
        main_layout.addWidget(force_alarms_label)
        self._force_alarms_widget = QTimedeltaListWidget(AlarmDelta)
        main_layout.addWidget(self._force_alarms_widget)

        # Force alarms for all-day events
        force_alarms_dates_label = QLabel(self.tr("All-Day Events"))
        main_layout.addWidget(force_alarms_dates_label)
        self._force_alarms_dates_widget = QTimedeltaListWidget(AlarmDelta)
        main_layout.addWidget(self._force_alarms_dates_widget)

        # Default Alarms Section
        main_layout.addWidget(QTitle(self.tr("Default Alarms"), self.tr("Appended to event with no alarms")))

        # Default alarms for normal events
        default_alarms_label = QLabel(self.tr("Normal Events"))
        main_layout.addWidget(default_alarms_label)
        self._default_alarms_widget = QTimedeltaListWidget(AlarmDelta)
        main_layout.addWidget(self._default_alarms_widget)

        # Default alarms for all-day events
        default_alarms_dates_label = QLabel(self.tr("All-Day Events"))
        main_layout.addWidget(default_alarms_dates_label)
        self._default_alarms_dates_widget = QTimedeltaListWidget(AlarmDelta)
        main_layout.addWidget(self._default_alarms_dates_widget)

        main_layout.addStretch()

    def set_from_configuration(self, config: CalendarConfiguration) -> None:
        """Update alarm widgets from a CalendarConfiguration"""
        self._force_alarms_widget.set_deltas(config.force_alarms)
        self._force_alarms_dates_widget.set_deltas(config.force_alarms_dates)
        self._default_alarms_widget.set_deltas(config.default_alarms)
        self._default_alarms_dates_widget.set_deltas(config.default_alarms_dates)

    def get_force_alarms(self) -> list[AlarmDelta]:
        """Get force alarms for regular events"""
        return self._force_alarms_widget.get_deltas()

    def get_force_alarms_dates(self) -> list[AlarmDelta]:
        """Get force alarms for all-day events"""
        return self._force_alarms_dates_widget.get_deltas()

    def get_default_alarms(self) -> list[AlarmDelta]:
        """Get default alarms for regular events"""
        return self._default_alarms_widget.get_deltas()

    def get_default_alarms_dates(self) -> list[AlarmDelta]:
        """Get default alarms for all-day events"""
        return self._default_alarms_dates_widget.get_deltas()

    def clear(self) -> None:
        """Clear all alarm lists"""
        self._force_alarms_widget.set_deltas([])
        self._force_alarms_dates_widget.set_deltas([])
        self._default_alarms_widget.set_deltas([])
        self._default_alarms_dates_widget.set_deltas([])
