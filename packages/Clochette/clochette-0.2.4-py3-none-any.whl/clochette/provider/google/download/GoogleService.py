from dataclasses import dataclass
from urllib.parse import quote

from oauthlib.oauth2 import OAuth2Token
from reactivex import Observable, operators as op, just

from clochette import log
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.infrastructure.http_.client.HttpService import HttpService
from clochette.provider.google.download.GoogleOAuth2Service import GoogleOAuth2Service
from clochette.provider.google.dto.GoogleCalendar import GoogleCalendar
from clochette.provider.google.dto.GoogleOauth2DTO import GoogleOauth2DTO
from clochette.provider.google.keyring_.GoogleAuthenticationService import GoogleAuthenticationService
from clochette.provider.shared.oauth2.OAuth2Mapper import OAuth2Mapper


@dataclass
class GoogleService:
    _google_oauth2_service: GoogleOAuth2Service
    _oauth2_mapper: OAuth2Mapper
    _http_service: HttpService
    _google_authentication_service: GoogleAuthenticationService

    def _authenticate(self, calendar_id: CalendarID) -> Observable[OAuth2Token]:
        def store_token(token: OAuth2Token) -> None:
            log.debug("Storing Google token")
            token_str = self._oauth2_mapper.from_oauth2_token(token)

            self._google_authentication_service.store_auth(calendar_id, GoogleOauth2DTO(token_str))

        def retrieve(auth: GoogleOauth2DTO | None) -> Observable[OAuth2Token]:
            if auth is None:
                return self._google_oauth2_service.authenticate().pipe(
                    op.do_action(lambda t: store_token(t)),
                )
            else:
                return just(self._oauth2_mapper.to_oauth2_token(auth.token))

        def refresh_if_needed(token: OAuth2Token) -> OAuth2Token:
            if self._google_oauth2_service.has_expired(token):
                log.info("Google token has expired, refreshing")
                token = self._google_oauth2_service.refresh_token(token)
                store_token(token)
            return token

        return just(self._google_authentication_service.retrieve_auth(calendar_id)).pipe(
            op.flat_map(retrieve),
            op.map(refresh_if_needed),
        )

    def list_calendars(self, calendar_id: CalendarID, http_timeout: HttpTimeout) -> Observable[list[GoogleCalendar]]:
        def download(token: OAuth2Token) -> list[GoogleCalendar]:
            headers = {"Authorization": f"Bearer {token.get("access_token")}", "Accept": "application/json"}

            response = self._http_service.get(
                "https://www.googleapis.com/calendar/v3/users/me/calendarList", headers, http_timeout
            )

            json = response.content_json

            if json is None or not response.is_successful():
                raise Exception(f"failed to list calendars, http status: {response.status_code}")
            else:
                items = json.get("items", [])
                return [GoogleCalendar(item.get("id"), item.get("summary")) for item in items]

        return self._authenticate(calendar_id).pipe(
            op.map(download),
        )

    def download_calendar(
        self, calendar_id: CalendarID, cal: GoogleCalendar, http_timeout: HttpTimeout
    ) -> Observable[str]:
        def download(token: OAuth2Token) -> str:
            headers = {"Authorization": f"Bearer {token.get("access_token")}"}

            id = quote(cal.id)
            response = self._http_service.get(
                f"https://apidata.googleusercontent.com/caldav/v2/{id}/events", headers, http_timeout
            )

            if response.is_successful():
                return response.content_utf8 or ""
            else:
                raise Exception(f"Failed to download calendar: {cal.id}, https status: {response.status_code}")

        return self._authenticate(calendar_id).pipe(op.map(download))
