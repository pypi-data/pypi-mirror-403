from dataclasses import dataclass

from clochette.application.service.provider.dto.ProviderType import ProviderType


@dataclass(frozen=True, eq=True)
class GoogleProviderType(ProviderType):
    def get_id(self) -> str:
        return "google"
