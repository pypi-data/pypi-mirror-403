from dataclasses import dataclass
from datetime import timedelta

from isodate import duration_isoformat

from clochette.domain.entity.delta.Delta import Delta


@dataclass(frozen=True)
class SnoozeDelta(Delta):
    """Snooze duration wrapper"""

    _timedelta: timedelta

    def get_timedelta(self) -> timedelta:
        return self._timedelta

    def is_positive(self):
        return self._timedelta.total_seconds() > 0

    def __str__(self) -> str:
        return duration_isoformat(self._timedelta)

    def __repr__(self) -> str:
        return duration_isoformat(self._timedelta)