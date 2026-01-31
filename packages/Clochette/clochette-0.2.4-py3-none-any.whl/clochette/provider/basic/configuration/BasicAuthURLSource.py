from dataclasses import dataclass, field

from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.provider.basic.dto.BasicProviderType import BasicProviderType


@dataclass(frozen=True, eq=True)
class BasicAuthURLSource(ISourceCalendar):
    url: str
    provider_type: ProviderType = field(default_factory=BasicProviderType, init=False, compare=False)

    def __post_init__(self):
        if not self.url:
            raise ValueError(f"URL cannot be empty: {self.url}")
