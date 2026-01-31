from dataclasses import dataclass
from datetime import timedelta

from isodate import duration_isoformat

from clochette.domain.entity.delta.Delta import Delta


@dataclass(frozen=True)
class AlarmDelta(Delta):
    """Alarm offset wrapper"""

    _timedelta: timedelta

    def get_timedelta(self) -> timedelta:
        return self._timedelta

    def __str__(self) -> str:
        return duration_isoformat(self._timedelta)

    def __repr__(self) -> str:
        return duration_isoformat(self._timedelta)
