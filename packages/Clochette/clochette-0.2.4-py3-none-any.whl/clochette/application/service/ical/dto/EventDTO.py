from dataclasses import dataclass, field
from datetime import timedelta, datetime
from typing import Generic

from clochette.infrastructure.clock.Generics import DateOrDatetimeType


@dataclass
class EventDTO(Generic[DateOrDatetimeType]):
    uid: str
    dtstart: DateOrDatetimeType
    dtend: DateOrDatetimeType
    rrule: str | None
    raw: str
    exdates: list[datetime]
    rdates: list[datetime]
    alarms: list[timedelta] = field(default_factory=list)
