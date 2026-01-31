from dataclasses import dataclass

from clochette import log
from clochette.domain.entity.Snooze import Snooze
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.EventID import EventID
from clochette.domain.entity.EventUID import EventUID
from clochette.domain.entity.Trigger import Trigger
from clochette.persist.database.dao.SnoozeDAO import SnoozeDAO
from clochette.persist.database.model.Snooze import SnoozeDTO


@dataclass
class SnoozeRepository:
    _snooze_dao: SnoozeDAO

    def delete_snooze(self, id: int) -> None:
        log.debug(f"Deleting snooze with ID: {id}")
        self._snooze_dao.delete_snooze(id)

    def delete_snoozes(self, event_ids: list[EventID]):
        for event_id in event_ids:
            self._snooze_dao.delete_snooze_by_event_id(event_id.event_uid.id, event_id.calendar_id.id)

    def add_snooze(self, snooze: Snooze) -> Snooze:
        log.debug(f"Saving snooze: {snooze}")
        id = self._snooze_dao.add_snooze(
            snooze.event_id.event_uid.id, snooze.event_id.calendar_id.id, snooze.trigger.trigger, snooze.trigger.start
        )
        return Snooze(id, snooze.event_id, snooze.trigger)

    def get_snoozes_by_calendar(self, calendar_id: CalendarID) -> list[Snooze]:
        log.debug("Retrieving snoozes")
        snoozes = self._snooze_dao.get_snoozes_by_calendar(calendar_id.id)
        return list(map(self._to_snooze, snoozes))

    def _to_snooze(self, snooze: SnoozeDTO) -> Snooze:
        return Snooze(
            snooze.id,
            EventID(EventUID(snooze.event_uid), CalendarID(snooze.calendar_id)),
            Trigger(snooze.trigger, snooze.trigger_start),
        )
