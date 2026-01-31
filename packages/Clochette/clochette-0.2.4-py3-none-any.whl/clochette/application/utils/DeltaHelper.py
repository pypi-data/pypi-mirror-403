from datetime import timedelta
from typing import TypeAlias, Literal

from PySide6.QtCore import QCoreApplication

from clochette.application.i18n.LangHelper import precise_delta
from clochette.domain.entity.delta.AlarmDelta import AlarmDelta
from clochette.domain.entity.delta.Delta import Delta
from clochette.domain.entity.delta.SnoozeDelta import SnoozeDelta

TimeUnitLiteral: TypeAlias = Literal["minutes", "hours", "days"]

time_unit_enum: tuple[TimeUnitLiteral, ...] = ("minutes", "hours", "days")


def make_timedelta(time: int, unit: TimeUnitLiteral) -> timedelta:
    """
    Create a timedelta object from a numeric value and a time unit.

    Parameters:
    - time: int, the amount of time.
    - unit: str, the unit of time ("minutes", "hours", "days").

    Returns:
    - timedelta object representing the duration.
    """
    if unit == "minutes":
        return timedelta(minutes=time)
    elif unit == "hours":
        return timedelta(hours=time)
    else:  # unit == "days"
        return timedelta(days=time)


def snooze_display(delta: SnoozeDelta) -> str:
    """Compute display string for snooze delta."""
    timedelta_value = delta.get_timedelta()
    if timedelta_value.total_seconds() == 0:
        return QCoreApplication.translate("DeltaHelper", "at start")

    precise = precise_delta(timedelta_value)
    if timedelta_value.total_seconds() < 0:
        return QCoreApplication.translate("DeltaHelper", "%s before start") % precise
    else:
        return QCoreApplication.translate("DeltaHelper", "for %s") % precise


def alarm_display(delta: AlarmDelta) -> str:
    """Compute display string for alarm delta."""
    timedelta_value = delta.get_timedelta()
    if timedelta_value.total_seconds() == 0:
        return QCoreApplication.translate("DeltaHelper", "at start")

    precise = precise_delta(timedelta_value)
    if timedelta_value.total_seconds() < 0:
        return QCoreApplication.translate("DeltaHelper", "%s before start") % precise
    else:
        return QCoreApplication.translate("DeltaHelper", "%s after start") % precise


def delta_display(delta: Delta) -> str:
    """Get display text for a delta using DeltaHelper."""
    if isinstance(delta, SnoozeDelta):
        return snooze_display(delta)
    elif isinstance(delta, AlarmDelta):
        return alarm_display(delta)
    else:
        # Fallback for unknown delta types
        return str(delta.get_timedelta())
