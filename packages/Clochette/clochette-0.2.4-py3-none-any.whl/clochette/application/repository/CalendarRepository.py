from dataclasses import dataclass
from datetime import datetime

from clochette import log
from clochette.domain.entity.Calendar import Calendar
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.CalendarConfiguration import CalendarConfiguration
from clochette.persist.database.dao.CalendarDAO import CalendarDAO
from clochette.persist.database.model.Calendar import CalendarDTO


@dataclass
class CalendarRepository:
    _calendar_dao: CalendarDAO

    def get_calendars(self) -> list[Calendar]:
        log.debug("Retrieving calendars")
        calendars = self._calendar_dao.get_all()
        return list(map(self._to_calendar, calendars))

    def set_calendars(self, calendars_conf: list[CalendarConfiguration]) -> None:
        log.debug("Setting calendars")
        new_calendars = {calendar.name: calendar for calendar in calendars_conf}
        old_calendars = {calendar.id: calendar for calendar in self._calendar_dao.get_all()}

        to_add = {calendar for name, calendar in new_calendars.items() if name not in old_calendars}
        to_delete = {calendar for name, calendar in old_calendars.items() if name not in new_calendars}

        for old_cal in to_delete:
            self._calendar_dao.delete_by_id(old_cal.id)

        for new_cal in to_add:
            self._calendar_dao.insert(new_cal.id.id)

    def add_calendar(self, calendar: CalendarConfiguration) -> None:
        log.debug(f"Adding calendar, calendar_id: {calendar.id}")
        self._calendar_dao.insert(calendar.id.id)

    def delete_calendar(self, calendar: CalendarConfiguration) -> None:
        log.debug(f"Adding calendar, calendar_id: {calendar.id}")
        self._calendar_dao.delete_by_id(calendar.id.id)

    def update_calendar_last_download(self, calendar_id: CalendarID, last_download: datetime) -> None:
        log.debug(f"Updating last download, calendar_id: {calendar_id}, last_download: {last_download}")
        if not last_download.tzinfo:
            raise ValueError(f"last_download should have timezone: {last_download}")
        self._calendar_dao.update_last_download(calendar_id.id, last_download)

    def get_calendar(self, calendar_id: CalendarID) -> Calendar:
        log.debug(f"Retrieving calendar, calendar_id: {calendar_id}")
        calendar = self._calendar_dao.get_by_id(calendar_id.id)
        return self._to_calendar(calendar)

    def _to_calendar(self, cal: CalendarDTO) -> Calendar:
        return Calendar(CalendarID(cal.id), cal.last_download)
