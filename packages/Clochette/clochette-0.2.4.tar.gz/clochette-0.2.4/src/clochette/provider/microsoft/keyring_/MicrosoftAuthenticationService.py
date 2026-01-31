import json
from dataclasses import dataclass

from clochette.application.repository.CalendarAuthenticationRepository import CalendarAuthenticationRepository
from clochette.domain.entity.CalendarID import CalendarID
from clochette.provider.microsoft.dto.MicrosoftOauth2DTO import MicrosoftOauth2DTO


@dataclass
class MicrosoftAuthenticationService:
    _calendar_authentication_repository: CalendarAuthenticationRepository

    def store_auth(self, calendar_id: CalendarID, auth: MicrosoftOauth2DTO) -> None:
        self._calendar_authentication_repository.store_value(calendar_id, json.dumps(auth, default=vars))

    def retrieve_auth(self, calendar_id: CalendarID) -> MicrosoftOauth2DTO | None:
        value = self._calendar_authentication_repository.get_value(calendar_id)
        if value:
            json_value = json.loads(value)
            return MicrosoftOauth2DTO(json_value.get("token"))

        return None
