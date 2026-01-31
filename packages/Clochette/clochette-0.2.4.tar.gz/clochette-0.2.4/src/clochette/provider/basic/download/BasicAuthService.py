import base64
from dataclasses import dataclass

from clochette import log
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.infrastructure.http_.client.HttpService import HttpService
from clochette.provider.basic.configuration.BasicAuthURLSource import BasicAuthURLSource
from clochette.provider.basic.keyring_.BasicAuthenticationService import BasicAuthenticationService
from clochette.provider.basic.dto.BasicAuthDTO import BasicAuthDTO


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True)
class BasicAuthService:
    _http_service: HttpService
    _basic_authentication_service: BasicAuthenticationService

    def download(
        self,
        calendar_id: CalendarID,
        source: BasicAuthURLSource,
        http_timeout: HttpTimeout,
        credentials: Credentials | None = None,
    ) -> str | None:

        if credentials is None:
            auth = self._basic_authentication_service.retrieve_auth(calendar_id)
        else:
            auth = BasicAuthDTO(credentials.username, credentials.password, False)
            self._basic_authentication_service.store_auth(calendar_id, auth)

        if auth is None:
            raise Exception("Failed to download calendar. empty credentials")

        return self._download_calendar(auth, source, http_timeout, calendar_id)

    def _download_calendar(
        self, auth: BasicAuthDTO, source: BasicAuthURLSource, http_timeout: HttpTimeout, calendar_id: CalendarID
    ) -> str:
        token = f"{auth.username}:{auth.password}"
        encoded_token = base64.b64encode(token.encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {encoded_token}"}

        response = self._http_service.get(source.url, headers, http_timeout)

        if response.is_successful():
            log.debug("Downloading calendar was successful")
            return response.content_utf8 or ""
        else:
            log.debug(f"Downloading calendar was failed, http status: {response.status_code}")
            raise Exception(f"Failed to download calendar: {calendar_id}, https status: {response.status_code}")
