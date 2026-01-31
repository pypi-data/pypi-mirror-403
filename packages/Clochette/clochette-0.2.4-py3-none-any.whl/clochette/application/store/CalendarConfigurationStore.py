from reactivex import Observable, Subject
from reactivex.subject import ReplaySubject

from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


class CalendarConfigurationStore:
    """Store for calendar configuration state using RxPY subjects."""

    _calendars: ReplaySubject[list[CalendarConfiguration]]
    _new_calendar: Subject[CalendarConfiguration]
    _calendar_deleted: Subject[CalendarConfiguration]
    _calendar_updated: Subject[CalendarConfiguration]

    def __init__(self):
        self._calendars = ReplaySubject(buffer_size=1)
        self._new_calendar = Subject()
        self._calendar_deleted = Subject()
        self._calendar_updated = Subject()

    @property
    def calendars(self) -> Observable[list[CalendarConfiguration]]:
        """Observable for the list of all calendar configurations."""
        return self._calendars

    @property
    def new_calendar(self) -> Observable[CalendarConfiguration]:
        """Observable for newly added calendar configurations."""
        return self._new_calendar

    @property
    def calendar_deleted(self) -> Observable[CalendarConfiguration]:
        """Observable for deleted calendar configurations."""
        return self._calendar_deleted

    @property
    def calendar_updated(self) -> Observable[CalendarConfiguration]:
        """Observable for updated calendar configurations."""
        return self._calendar_updated

    def set_calendars(self, calendars: list[CalendarConfiguration]) -> None:
        """Set the list of all calendars."""
        self._calendars.on_next(calendars)

    def add_calendar(self, calendar: CalendarConfiguration) -> None:
        """Emit a newly added calendar."""
        self._new_calendar.on_next(calendar)

    def delete_calendar(self, calendar: CalendarConfiguration) -> None:
        """Emit a deleted calendar."""
        self._calendar_deleted.on_next(calendar)

    def update_calendar(self, calendar: CalendarConfiguration) -> None:
        """Emit an updated calendar."""
        self._calendar_updated.on_next(calendar)
