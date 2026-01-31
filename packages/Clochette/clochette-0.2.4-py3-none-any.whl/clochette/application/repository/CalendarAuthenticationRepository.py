from dataclasses import dataclass

from clochette.domain.entity.CalendarID import CalendarID
from clochette.persist.keyring_.KeyringService import KeyringService


@dataclass
class CalendarAuthenticationRepository:
    _keyring_service: KeyringService
    _calendar_id_key = "#calendar_ids#"
    _calendar_prefix = "calendar_"

    def store_value(self, calendar_id: CalendarID, value: str) -> None:
        """Store a value for a calendar in the keyring"""
        self._add_calendar(calendar_id)
        self._keyring_service.store_value(f"{self._calendar_prefix}{calendar_id.id}", value)

    def get_value(self, calendar_id: CalendarID) -> str | None:
        """Retrieve a value for a calendar from the keyring"""
        return self._keyring_service.get_value(f"{self._calendar_prefix}{calendar_id.id}")

    def delete_auth(self, calendar_id: CalendarID) -> None:
        """Delete authentication data for a calendar"""
        self._keyring_service.delete_value(f"{self._calendar_prefix}{calendar_id.id}")

    def cleanup_calendars(self, to_keep: list[CalendarID]) -> None:
        """Remove authentication data for calendars not in the to_keep list"""
        used_calendars_str = list(map(lambda x: x.id, to_keep))
        saved_calendars = self._get_calendar_ids()

        unused = [item for item in saved_calendars if item not in used_calendars_str]

        for to_delete in unused:
            self._keyring_service.delete_value(self._calendar_prefix + to_delete)

        calendars = [item for item in saved_calendars if item not in unused]
        self._keyring_service.store_value(self._calendar_id_key, ",".join(calendars))

    def _get_calendar_ids(self) -> set[str]:
        """Get the set of calendar IDs stored in the keyring"""
        calendars_str = self._keyring_service.get_value(self._calendar_id_key)
        if calendars_str:
            return set(calendars_str.split(","))
        else:
            return set()

    def _add_calendar(self, calendar_id: CalendarID) -> None:
        """Add a calendar ID to the tracked list"""
        calendars = self._get_calendar_ids()
        calendars.add(calendar_id.id)
        self._keyring_service.store_value(self._calendar_id_key, ",".join(calendars))
