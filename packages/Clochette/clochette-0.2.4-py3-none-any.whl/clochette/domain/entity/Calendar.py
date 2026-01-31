from dataclasses import dataclass
from datetime import datetime

from clochette.domain.entity.CalendarID import CalendarID


@dataclass(frozen=True, eq=True)
class Calendar:
    calendar_id: CalendarID
    last_download: datetime
