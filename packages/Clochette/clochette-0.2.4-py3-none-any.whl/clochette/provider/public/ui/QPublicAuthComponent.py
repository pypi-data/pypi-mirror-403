from dataclasses import dataclass
from typing import Type, override

from clochette.application.service.provider.dto.IAuthenticationComponent import IAuthenticationComponent
from clochette.domain.entity.CalendarID import CalendarID
from clochette.framework.qt.QComponent import QComponent
from clochette.infrastructure.http_.client.HttpService import HttpService
from clochette.provider.public.configuration.PublicURLSource import PublicURLSource
from clochette.provider.public.ui.QPublicAuthPanel import QPublicAuthPanel


@dataclass(frozen=True)
class PublicValues:
    url: str


@dataclass
class QPublicAuthComponent(QComponent[QPublicAuthPanel], IAuthenticationComponent[PublicURLSource, PublicValues]):
    _view: QPublicAuthPanel
    _http_service: HttpService

    def __post_init__(self):
        super().__init__(self._view)
        self._view.on_authenticate.link(self._public_auth)

    def _public_auth(self):
        try:
            self._http_service.get(self._view.url)
            self._view.set_authentication_success()
        except Exception as e:
            self._view.set_authentication_failed(e)

    @override
    def clear(self):
        self._view.clear()

    @override
    def get_values(self) -> PublicValues:
        return PublicValues(self._view.url)

    @override
    def get_source(self) -> PublicURLSource:
        return PublicURLSource(self._view.url)

    @property
    @override
    def source_type(self) -> Type[PublicURLSource]:
        return PublicURLSource

    @override
    def set_values(self, calendar_id: CalendarID, source: PublicURLSource) -> None:
        self._view.set_url(source.url)

    @override
    def validate(self) -> bool:
        if not self._view.url:
            self._view.set_error("URL cannot be empty")
            return False
        return True
