from dataclasses import dataclass
from datetime import timedelta

from clochette.domain.entity.Contact import Contact


@dataclass(frozen=True, eq=True)
class EventDetails:
    summary: str
    description: str | None
    location: str | None
    organizer: Contact | None
    attendees: list[Contact]
    raw: str
    duration: timedelta
