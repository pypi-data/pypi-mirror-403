from datetime import timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QFormLayout, QGroupBox

from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout


class QCalendarGeneralSettingsView(QWidget):
    """Widget for general calendar settings: download interval, reminder window, and HTTP timeouts"""

    _download_interval_spinbox: QSpinBox
    _missed_reminders_spinbox: QSpinBox
    _connection_timeout_spinbox: QSpinBox
    _read_timeout_spinbox: QSpinBox

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(main_layout)

        # General Settings Group
        general_group = QGroupBox(self.tr("Calendar Settings"))
        general_layout = QFormLayout()

        self._download_interval_spinbox = QSpinBox()
        self._download_interval_spinbox.setMinimum(1)
        self._download_interval_spinbox.setMaximum(1440)  # Max 24 hours
        self._download_interval_spinbox.setSuffix(self.tr(" minutes"))
        self._download_interval_spinbox.setValue(5)
        general_layout.addRow(self.tr("Download Interval:"), self._download_interval_spinbox)

        self._missed_reminders_spinbox = QSpinBox()
        self._missed_reminders_spinbox.setMinimum(-168)  # -7 days
        self._missed_reminders_spinbox.setMaximum(0)
        self._missed_reminders_spinbox.setSuffix(self.tr(" hours"))
        self._missed_reminders_spinbox.setValue(-24)
        general_layout.addRow(self.tr("Missed Reminders Window:"), self._missed_reminders_spinbox)

        general_group.setLayout(general_layout)
        main_layout.addWidget(general_group)

        # HTTP Timeout Group
        timeout_group = QGroupBox(self.tr("HTTP Timeout"))
        timeout_layout = QFormLayout()

        self._connection_timeout_spinbox = QSpinBox()
        self._connection_timeout_spinbox.setMinimum(1)
        self._connection_timeout_spinbox.setMaximum(300)
        self._connection_timeout_spinbox.setSuffix(self.tr(" seconds"))
        self._connection_timeout_spinbox.setValue(5)
        timeout_layout.addRow(self.tr("Connection Timeout:"), self._connection_timeout_spinbox)

        self._read_timeout_spinbox = QSpinBox()
        self._read_timeout_spinbox.setMinimum(1)
        self._read_timeout_spinbox.setMaximum(300)
        self._read_timeout_spinbox.setSuffix(self.tr(" seconds"))
        self._read_timeout_spinbox.setValue(30)
        timeout_layout.addRow(self.tr("Read Timeout:"), self._read_timeout_spinbox)

        timeout_group.setLayout(timeout_layout)
        main_layout.addWidget(timeout_group)

    def set_from_configuration(self, config: CalendarConfiguration) -> None:
        """Update form fields from a CalendarConfiguration"""
        download_interval_minutes = int(config.download_interval.total_seconds() / 60)
        self._download_interval_spinbox.setValue(download_interval_minutes)

        missed_reminders_hours = int(config.missed_reminders_past_window.total_seconds() / 3600)
        self._missed_reminders_spinbox.setValue(missed_reminders_hours)

        self._connection_timeout_spinbox.setValue(config.http_timeout.connection_timeout)
        self._read_timeout_spinbox.setValue(config.http_timeout.read_timeout)

    def get_download_interval(self) -> timedelta:
        """Get download interval as timedelta"""
        return timedelta(minutes=self._download_interval_spinbox.value())

    def get_missed_reminders_past_window(self) -> timedelta:
        """Get missed reminders window as timedelta"""
        return timedelta(hours=self._missed_reminders_spinbox.value())

    def get_http_timeout(self) -> HttpTimeout:
        """Get HTTP timeout configuration"""
        return HttpTimeout(
            connection_timeout=self._connection_timeout_spinbox.value(),
            read_timeout=self._read_timeout_spinbox.value(),
        )

    def clear(self) -> None:
        """Reset all fields to defaults"""
        self._download_interval_spinbox.setValue(5)
        self._missed_reminders_spinbox.setValue(-24)
        self._connection_timeout_spinbox.setValue(5)
        self._read_timeout_spinbox.setValue(30)
