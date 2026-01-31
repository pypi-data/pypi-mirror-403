from datetime import datetime

from clochette import log
from clochette.domain.entity.CalendarEvent import CalendarEvent
from clochette.domain.entity.EventID import EventID
from clochette.domain.entity.Occurrence import Occurrence
from clochette.infrastructure.data_structure.AtomicDict import AtomicDict
from clochette.infrastructure.data_structure.PeekableIterator import peek


class CalendarEventQuery:
    _events: AtomicDict[EventID, CalendarEvent]

    def __init__(self, events: dict[EventID, CalendarEvent]) -> None:
        self._events = AtomicDict(events)

    def before(self, now: datetime) -> list[Occurrence]:
        log.debug(f"Listing events until now: {now}")
        occurrences = []

        for event_id, event in self._events.items():
            triggers = event.trigger_iterator

            while True:
                trigger = peek(triggers)
                log.debug(f"Query event: {event_id}, trigger: {trigger}, now: {now}")

                if not trigger:
                    break

                if trigger.trigger > now:
                    break

                _ = next(triggers)
                occurrences.append(Occurrence(event.event_id, trigger))

        return occurrences

    def get_event(self, event_id: EventID) -> CalendarEvent | None:
        return self._events.get(event_id, None)
