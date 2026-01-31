from dataclasses import dataclass
from typing import Type, override

from clochette.application.service.provider.dto.IAuthenticationComponent import IAuthenticationComponent
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.framework.qt.QComponent import QComponent
from clochette.framework.rx.Scheduler import scheduler
from clochette.presentation.settings.calendar.authentication.AuthenticationConfigurationModel import (
    AuthenticationConfigurationModel,
)
from clochette.provider.google.configuration.GoogleSource import GoogleSource
from clochette.provider.google.download.GoogleService import GoogleService
from clochette.provider.google.dto.GoogleCalendar import GoogleCalendar
from clochette.provider.google.ui.QGoogleOAuth2Panel import QGoogleOAuth2Panel


@dataclass(frozen=True)
class GoogleValues:
    selected_calendars: dict[GoogleCalendar, bool]


@dataclass
class QGoogleOAuth2Component(QComponent[QGoogleOAuth2Panel], IAuthenticationComponent[GoogleSource, GoogleValues]):
    _view: QGoogleOAuth2Panel
    _model: AuthenticationConfigurationModel
    _google_service: GoogleService

    def __post_init__(self):
        super().__init__(self._view)
        self._view.setTitle("OAuth2 Google Options")
        self._view.on_authenticate.link(self._google_auth)

    def _google_auth(self):
        try:
            calendar_id = self._model.calendar_id
            self._google_service.list_calendars(calendar_id, HttpTimeout.default()).subscribe(
                on_next=lambda c: self._authentication_successful(c),
                on_error=lambda e: self._view.set_authentication_failed(e),
                scheduler=scheduler,
            )

        except Exception as e:
            self._view.set_authentication_failed(e)

    def _authentication_successful(self, calendars: list[GoogleCalendar]):
        cals = {cal: False for cal in calendars}
        self._view.set_selected_calendars(cals)
        self._view.set_authentication_success()

    @override
    def clear(self) -> None:
        self._view.clear()

    @override
    def get_values(self) -> GoogleValues:
        calendars = self._view.selected_calendars
        selected_calendars = {cal.id: checked for cal, checked in calendars.items()}
        return GoogleValues(selected_calendars)

    @override
    def get_source(self) -> GoogleSource:
        # Convert dict[CheckBoxItem[GoogleCalendar], bool] to dict[GoogleCalendar, bool]
        calendars = {item.id: checked for item, checked in self._view.selected_calendars.items()}
        return GoogleSource(calendars)

    @property
    @override
    def source_type(self) -> Type[GoogleSource]:
        return GoogleSource

    @override
    def set_values(self, calendar_id: CalendarID, source: GoogleSource) -> None:
        self._view.set_selected_calendars(source.calendars)

    @override
    def validate(self) -> bool:
        if all(not value for value in self._view.selected_calendars.values()):
            self._view.set_error("Please authenticate and select calendars")
            return False
        return True
