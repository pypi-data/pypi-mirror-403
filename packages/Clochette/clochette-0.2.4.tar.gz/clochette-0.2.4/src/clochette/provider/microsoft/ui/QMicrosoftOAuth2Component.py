from dataclasses import dataclass
from typing import Type

from typing_extensions import override

from clochette.application.service.provider.dto.IAuthenticationComponent import IAuthenticationComponent
from clochette.domain.entity.CalendarID import CalendarID
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.framework.qt.QComponent import QComponent
from clochette.framework.rx.Scheduler import scheduler
from clochette.presentation.settings.calendar.authentication.AuthenticationConfigurationModel import (
    AuthenticationConfigurationModel,
)
from clochette.provider.microsoft.configuration.MicrosoftSource import MicrosoftSource
from clochette.provider.microsoft.download.MicrosoftService import MicrosoftService
from clochette.provider.microsoft.dto.MicrosoftCalendar import MicrosoftCalendar
from clochette.provider.microsoft.ui.QMicrosoftOAuth2Panel import QMicrosoftOAuth2Panel


@dataclass(frozen=True)
class MicrosoftValues:
    selected_calendars: dict[MicrosoftCalendar, bool]


@dataclass
class QMicrosoftOAuth2Component(
    QComponent[QMicrosoftOAuth2Panel], IAuthenticationComponent[MicrosoftSource, MicrosoftValues]
):
    _view: QMicrosoftOAuth2Panel
    _model: AuthenticationConfigurationModel
    _microsoft_service: MicrosoftService

    def __post_init__(self):
        super().__init__(self._view)
        self._view.setTitle("OAuth2 Microsoft Options")
        self._view.on_authenticate.link(self._microsoft_auth)

    def _microsoft_auth(self):
        try:
            calendar_id = self._model.calendar_id
            self._microsoft_service.list_calendars(calendar_id, HttpTimeout.default()).subscribe(
                on_next=lambda c: self._authentication_successful(c),
                on_error=lambda e: self._view.set_authentication_failed(e),
                scheduler=scheduler,
            )

        except Exception as e:
            self._view.set_authentication_failed(e)

    def _authentication_successful(self, calendars: list[MicrosoftCalendar]):
        cals = {cal: False for cal in calendars}
        self._view.set_selected_calendars(cals)
        self._view.set_authentication_success()

    @override
    def clear(self) -> None:
        self._view.clear()

    @override
    def get_values(self) -> MicrosoftValues:
        calendars = self._view.selected_calendars
        selected_calendars = {cal.id: checked for cal, checked in calendars.items()}
        return MicrosoftValues(selected_calendars)

    @override
    def get_source(self) -> MicrosoftSource:
        # Convert dict[CheckBoxItem[MicrosoftCalendar], bool] to dict[MicrosoftCalendar, bool]
        calendars = {item.id: checked for item, checked in self._view.selected_calendars.items()}
        return MicrosoftSource(calendars)

    @property
    @override
    def source_type(self) -> Type[MicrosoftSource]:
        return MicrosoftSource

    @override
    def set_values(self, calendar_id: CalendarID, source: MicrosoftSource) -> None:
        self._view.set_selected_calendars(source.calendars)

    @override
    def validate(self) -> bool:
        if all(not value for value in self._view.selected_calendars.values()):
            self._view.set_error("Please authenticate and select calendars")
            return False
        return True
