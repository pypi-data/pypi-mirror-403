from dataclasses import dataclass, field

from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.provider.google.dto.GoogleCalendar import GoogleCalendar
from clochette.provider.google.dto.GoogleProviderType import GoogleProviderType


@dataclass(frozen=True, eq=True)
class GoogleSource(ISourceCalendar):
    calendars: dict[GoogleCalendar, bool]
    provider_type: ProviderType = field(default_factory=GoogleProviderType, init=False, compare=False)

    @property
    def selected_calendars(self) -> list[GoogleCalendar]:
        return [cal for cal, checked in self.calendars.items() if checked]
