from reactivex import Subject

from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration


class CalendarNavigationModel:
    show_calendar_list: Subject[bool] = Subject()
    edit_calendar: Subject[CalendarConfiguration] = Subject()
    add_calendar: Subject[bool] = Subject()
