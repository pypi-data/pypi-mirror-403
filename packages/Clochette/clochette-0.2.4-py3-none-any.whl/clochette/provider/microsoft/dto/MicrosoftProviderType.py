from dataclasses import dataclass

from clochette.application.service.provider.dto.ProviderType import ProviderType


@dataclass(frozen=True, eq=True)
class MicrosoftProviderType(ProviderType):
    def get_id(self) -> str:
        return "microsoft"
