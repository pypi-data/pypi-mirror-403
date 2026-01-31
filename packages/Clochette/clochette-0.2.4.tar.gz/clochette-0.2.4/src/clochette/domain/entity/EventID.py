from dataclasses import dataclass

from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.EventUID import EventUID


@dataclass(frozen=True, eq=True)
class EventID:
    event_uid: EventUID
    calendar_id: CalendarID
