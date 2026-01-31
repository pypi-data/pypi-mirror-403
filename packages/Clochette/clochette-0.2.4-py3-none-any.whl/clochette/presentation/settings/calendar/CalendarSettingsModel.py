from dataclasses import dataclass, field

from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


@dataclass
class CalendarSettingsModel:
    """Model for calendar-specific settings"""

    edit_calendar: CalendarConfiguration | None = field(default=None)
