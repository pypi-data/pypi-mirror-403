from dataclasses import dataclass

from clochette.domain.entity.CalendarEvent import EventID
from clochette.domain.entity.Trigger import Trigger


@dataclass(frozen=True, eq=True)
class Occurrence:
    event_id: EventID
    trigger: Trigger
