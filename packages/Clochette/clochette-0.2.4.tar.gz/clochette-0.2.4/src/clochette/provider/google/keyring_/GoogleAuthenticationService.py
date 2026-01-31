import json
from dataclasses import dataclass

from clochette.application.repository.CalendarAuthenticationRepository import CalendarAuthenticationRepository
from clochette.domain.entity.CalendarID import CalendarID
from clochette.provider.google.dto.GoogleOauth2DTO import GoogleOauth2DTO


@dataclass
class GoogleAuthenticationService:
    _calendar_authentication_repository: CalendarAuthenticationRepository

    def store_auth(self, calendar_id: CalendarID, auth: GoogleOauth2DTO) -> None:
        self._calendar_authentication_repository.store_value(calendar_id, json.dumps(auth, default=vars))

    def retrieve_auth(self, calendar_id: CalendarID) -> GoogleOauth2DTO | None:
        value = self._calendar_authentication_repository.get_value(calendar_id)
        if value:
            json_value = json.loads(value)
            return GoogleOauth2DTO(json_value.get("token"))

        return None
