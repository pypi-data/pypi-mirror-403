from dataclasses import dataclass
from urllib.parse import quote

from oauthlib.oauth2 import OAuth2Token
from reactivex import Observable, operators as op, just

from clochette import log
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.infrastructure.http_.client.HttpService import HttpService
from clochette.provider.microsoft.keyring_.MicrosoftAuthenticationService import MicrosoftAuthenticationService
from clochette.provider.microsoft.download.MicrosoftOAuth2Service import MicrosoftOAuth2Service
from clochette.provider.microsoft.dto.MicrosoftCalendar import MicrosoftCalendar
from clochette.provider.microsoft.dto.MicrosoftOauth2DTO import MicrosoftOauth2DTO
from clochette.provider.shared.oauth2.OAuth2Mapper import OAuth2Mapper


@dataclass
class MicrosoftService:
    _microsoft_oauth2_service: MicrosoftOAuth2Service
    _oauth2_mapper: OAuth2Mapper
    _http_service: HttpService
    _microsoft_authentication_service: MicrosoftAuthenticationService

    def _authenticate(self, calendar_id: CalendarID) -> Observable[OAuth2Token]:
        def store_token(token: OAuth2Token) -> None:
            log.debug("Storing Microsoft token")
            token_str = self._oauth2_mapper.from_oauth2_token(token)

            self._microsoft_authentication_service.store_auth(calendar_id, MicrosoftOauth2DTO(token_str))

        def retrieve(auth: MicrosoftOauth2DTO | None) -> Observable[OAuth2Token]:
            if auth is None:
                return self._microsoft_oauth2_service.authenticate().pipe(
                    op.do_action(lambda t: store_token(t)),
                )
            else:
                return just(self._oauth2_mapper.to_oauth2_token(auth.token))

        def refresh_if_needed(token: OAuth2Token) -> OAuth2Token:
            if self._microsoft_oauth2_service.has_expired(token):
                log.info("Microsoft token has expired, refreshing")
                token = self._microsoft_oauth2_service.refresh_token(token)
                store_token(token)
            return token

        return just(self._microsoft_authentication_service.retrieve_auth(calendar_id)).pipe(
            op.flat_map(retrieve),
            op.map(refresh_if_needed),
        )

    def list_calendars(self, calendar_id: CalendarID, http_timeout: HttpTimeout) -> Observable[list[MicrosoftCalendar]]:
        def download(token: OAuth2Token) -> list[MicrosoftCalendar]:
            headers = {"Authorization": f"Bearer {token.get("access_token")}", "Accept": "application/json"}

            response = self._http_service.get("https://graph.microsoft.com/v1.0/me/calendars", headers, http_timeout)

            json = response.content_json

            if json is None or not response.is_successful():
                raise Exception(f"failed to list calendars, http status: {response.status_code}")
            else:
                items = json.get("value", [])
                return [MicrosoftCalendar(item.get("id"), item.get("name")) for item in items]

        return self._authenticate(calendar_id).pipe(op.map(download))

    # https://learn.microsoft.com/en-us/graph/api/calendar-list-events?view=graph-rest-1.0&tabs=http
    def download_calendar(
        self, calendar_id: CalendarID, cal: MicrosoftCalendar, http_timeout: HttpTimeout
    ) -> Observable[str]:
        def download(token: OAuth2Token) -> str:
            headers = {"Authorization": f"Bearer {token.get("access_token")}"}

            id = quote(cal.id)
            response = self._http_service.get(
                f"https://graph.microsoft.com/v1.0/me/calendars/{id}/events", headers, http_timeout
            )

            if response.is_successful():
                return response.content_utf8 or ""
            else:
                raise Exception(f"Failed to download calendar: {cal.id}, https status: {response.status_code}")

        return self._authenticate(calendar_id).pipe(
            op.map(download),
        )
