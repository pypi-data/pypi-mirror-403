from dataclasses import dataclass, field

from clochette.application.service.provider.dto.ProviderType import ProviderType
from clochette.domain.entity.ISourceCalendar import ISourceCalendar
from clochette.provider.public.dto.PublicProviderType import PublicProviderType


@dataclass(frozen=True, eq=True)
class PublicURLSource(ISourceCalendar):
    url: str
    provider_type: ProviderType = field(default_factory=PublicProviderType, init=False, compare=False)

    def __post_init__(self):
        if not self.url:
            raise ValueError(f"URL cannot be empty: {self.url}")
