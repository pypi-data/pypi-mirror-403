from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


class AuthenticationConfigurationModel:
    _calendar_id: CalendarID
    _edit_calendar: CalendarConfiguration | None

    def __init__(self):
        self._calendar_id = CalendarID.new()
        self._edit_calendar = None

    @property
    def edit_calendar(self):
        return self._edit_calendar

    @edit_calendar.setter
    def edit_calendar(self, calendar: CalendarConfiguration | None):
        self._edit_calendar = calendar
        if calendar is None:
            self._calendar_id = CalendarID.new()

    @property
    def calendar_id(self) -> CalendarID:
        if self._edit_calendar is None:
            return self._calendar_id
        else:
            return self._edit_calendar.id
