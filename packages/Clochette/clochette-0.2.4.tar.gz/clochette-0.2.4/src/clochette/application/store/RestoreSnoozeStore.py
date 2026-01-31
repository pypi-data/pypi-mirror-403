from dataclasses import dataclass

from clochette.domain.entity.CalendarID import CalendarID
from clochette.infrastructure.data_structure.AtomicSet import AtomicSet


@dataclass
class RestoreSnoozeStore:
    """Store for tracking which calendars have had their snoozes restored.

    Uses AtomicSet for thread-safe storage without RxPY since simple set operations
    are already thread-safe via AtomicSet's internal locking.
    """

    _atomic_set: AtomicSet[CalendarID]

    def mark_restored(self, calendar_id: CalendarID) -> bool:
        """Mark a calendar as having its snoozes restored.

        Returns:
            True if the calendar was already marked as restored
            False if this is the first time marking it as restored
        """
        return self._atomic_set.contains_or_add(calendar_id)
