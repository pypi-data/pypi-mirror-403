from datetime import datetime

from clochette.infrastructure.data_structure.AtomicDict import AtomicDict
from clochette.domain.entity.CalendarEvent import CalendarEvent
from clochette.domain.entity.CalendarEventQuery import CalendarEventQuery
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.EventID import EventID
from clochette.domain.entity.Occurrence import Occurrence
from clochette import log


class EventModel:
    _calendar_queries: AtomicDict[CalendarID, CalendarEventQuery]

    def __init__(self) -> None:
        self._calendar_queries = AtomicDict({})

    def add_query(self, calendar_id: CalendarID, query: CalendarEventQuery) -> None:
        log.debug(f"Adding new model for calendar: {calendar_id}")
        self._calendar_queries[calendar_id] = query

    def query_occurrences(self, now: datetime) -> list[Occurrence]:
        log.debug(f"Querying occurrences up to: {now}")
        query_results: list[Occurrence] = []
        for _, query in self._calendar_queries.items():
            occurrences = query.before(now)
            query_results += occurrences

        return query_results

    def get_event(self, event_id: EventID) -> CalendarEvent | None:
        calendar = self._calendar_queries[event_id.calendar_id]

        if not calendar:
            log.error(f"No calendar found with id: {event_id.calendar_id}")
            return None

        event = calendar.get_event(event_id)

        if event:
            log.debug(f"Found event with id: {event_id}")
        else:
            log.error(f"No event found with id: {event_id}")

        return event
