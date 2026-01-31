from datetime import datetime

from clochette.domain.entity.EventID import EventID
from clochette.domain.entity.Occurrence import Occurrence
from clochette.domain.entity.Snooze import Snooze
from clochette.infrastructure.data_structure.AtomicDict import AtomicDict


class SnoozeQuery:
    _snoozes: AtomicDict[EventID, Snooze]

    def __init__(self):
        self._snoozes = AtomicDict({})

    def before(self, now: datetime) -> list[Occurrence]:
        occurrences = []

        for _, snooze in self._snoozes.items():
            trigger = snooze.trigger

            if trigger.trigger > now:
                continue

            occurrences.append(Occurrence(snooze.event_id, trigger))

        return occurrences

    def add(self, snooze: Snooze) -> None:
        self._snoozes[snooze.event_id] = snooze
