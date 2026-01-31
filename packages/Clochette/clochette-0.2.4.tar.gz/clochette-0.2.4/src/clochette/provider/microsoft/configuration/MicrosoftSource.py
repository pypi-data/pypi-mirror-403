from dataclasses import dataclass, field

from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.provider.microsoft.dto.MicrosoftCalendar import MicrosoftCalendar
from clochette.provider.microsoft.dto.MicrosoftProviderType import MicrosoftProviderType


@dataclass(frozen=True, eq=True)
class MicrosoftSource(ISourceCalendar):
    calendars: dict[MicrosoftCalendar, bool]
    provider_type: ProviderType = field(default_factory=MicrosoftProviderType, init=False, compare=False)

    @property
    def selected_calendars(self) -> list[MicrosoftCalendar]:
        return [cal for cal, checked in self.calendars.items() if checked]
