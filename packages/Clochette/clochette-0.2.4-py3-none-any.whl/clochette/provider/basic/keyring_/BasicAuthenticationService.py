import json
from dataclasses import dataclass

from clochette.application.repository.CalendarAuthenticationRepository import CalendarAuthenticationRepository
from clochette.domain.entity.CalendarID import CalendarID
from clochette.provider.basic.dto.BasicAuthDTO import BasicAuthDTO


@dataclass
class BasicAuthenticationService:
    _calendar_authentication_repository: CalendarAuthenticationRepository

    def store_auth(self, calendar_id: CalendarID, auth: BasicAuthDTO) -> None:
        self._calendar_authentication_repository.store_value(calendar_id, json.dumps(auth, default=vars))

    def retrieve_auth(self, calendar_id: CalendarID) -> BasicAuthDTO | None:
        value = self._calendar_authentication_repository.get_value(calendar_id)
        if value:
            json_value = json.loads(value)
            return BasicAuthDTO(json_value.get("username"), json_value.get("password"), json_value.get("cancelled"))

        return None
