from datetime import datetime

from clochette.domain.entity.Occurrence import Occurrence
from clochette.domain.entity.Snooze import Snooze
from clochette.domain.entity.SnoozeQuery import SnoozeQuery
from clochette import log


class SnoozeModel:
    _snooze_query: SnoozeQuery

    def __init__(self) -> None:
        self._snooze_query = SnoozeQuery()

    def add_snooze(self, snooze: Snooze) -> None:
        log.debug(f"Adding new snooze to the model: {snooze}")
        self._snooze_query.add(snooze)

    def query_occurrences(self, now: datetime) -> list[Occurrence]:
        log.debug(f"Querying snoozed occurrences up to: {now}")

        return self._snooze_query.before(now)
