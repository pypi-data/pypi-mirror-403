from dataclasses import dataclass
from typing import Type, override

from clochette.application.service.provider.dto.IAuthenticationComponent import IAuthenticationComponent
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.framework.qt.QComponent import QComponent
from clochette.presentation.settings.calendar.authentication.AuthenticationConfigurationModel import (
    AuthenticationConfigurationModel,
)
from clochette.provider.basic.configuration.BasicAuthURLSource import BasicAuthURLSource
from clochette.provider.basic.download.BasicAuthService import BasicAuthService, Credentials
from clochette.provider.basic.keyring_.BasicAuthenticationService import BasicAuthenticationService
from clochette.provider.basic.ui.QBasicAuthView import QBasicAuthView


@dataclass(frozen=True)
class BasicValues:
    url: str
    username: str
    password: str


@dataclass
class QBasicAuthComponent(QComponent[QBasicAuthView], IAuthenticationComponent[BasicAuthURLSource, BasicValues]):
    _view: QBasicAuthView
    _model: AuthenticationConfigurationModel
    _basic_auth_service: BasicAuthService
    _basic_authentication_service: BasicAuthenticationService

    def __post_init__(self):
        super().__init__(self._view)
        self._view.on_authenticate.link(self._basic_auth)

    def _basic_auth(self):
        try:
            calendar_id = self._model.calendar_id
            self._basic_auth_service.download(
                calendar_id,
                BasicAuthURLSource(self._view.url),
                HttpTimeout.default(),
                Credentials(self._view.username, self._view.password),
            )
            self._view.set_authentication_success()
        except Exception as e:
            self._view.set_authentication_failed(e)

    @override
    def clear(self):
        self._view.clear()

    @override
    def get_values(self) -> BasicValues:
        return BasicValues(self._view.url, self._view.username, self._view.password)

    @override
    def get_source(self) -> BasicAuthURLSource:
        return BasicAuthURLSource(self._view.url)

    @property
    @override
    def source_type(self) -> Type[BasicAuthURLSource]:
        return BasicAuthURLSource

    @override
    def set_values(self, calendar_id: CalendarID, source: BasicAuthURLSource) -> None:
        self._view.set_url(source.url)

        # Retrieve credentials from keyring
        auth = self._basic_authentication_service.retrieve_auth(calendar_id)
        if auth is None:
            self._view.set_username("")
            self._view.set_password("")
        else:
            self._view.set_username(auth.username)
            self._view.set_password(auth.password)

    @override
    def validate(self) -> bool:
        if not self._view.url:
            self._view.set_error("URL cannot be empty")
            return False
        return True
