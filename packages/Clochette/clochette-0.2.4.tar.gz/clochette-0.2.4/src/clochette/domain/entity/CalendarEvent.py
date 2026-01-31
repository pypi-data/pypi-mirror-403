from dataclasses import dataclass
from datetime import datetime, date

from clochette.domain.entity.EventID import EventID
from clochette.domain.entity.Trigger import Trigger
from clochette.infrastructure.data_structure.PeekableIterator import PeekableIterator


@dataclass(frozen=True, eq=True)
class CalendarEvent:
    event_id: EventID
    start: date | datetime
    end: date | datetime
    trigger_iterator: PeekableIterator[Trigger]
    raw: str

    def __hash__(self) -> int:
        return hash(self.event_id)

    def __str__(self) -> str:
        return f"CalendarEvent(uid={self.event_id}, start={self.start}, end={self.end}, raw=\n{self.raw})"
