from dataclasses import dataclass
from datetime import datetime
from typing import Generic

from clochette.infrastructure.clock.DateTimeUtils import DateTimeUtils
from clochette.infrastructure.clock.Generics import DateOrDatetimeType


@dataclass(frozen=True, eq=True)
class Trigger(Generic[DateOrDatetimeType]):
    trigger: datetime  # datetime when to notify of an event, must have a TZ
    start: DateOrDatetimeType  # start date/time of the event

    def __post_init__(self):
        if not DateTimeUtils.is_datetime(self.trigger):
            raise ValueError(f"trigger_utc should be of type datetime, {self.trigger}")

        if not self.trigger.tzinfo:
            raise ValueError(f"trigger doesn't have a timezone, {self.trigger}")
