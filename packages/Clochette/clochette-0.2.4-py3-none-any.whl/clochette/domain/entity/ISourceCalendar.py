from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clochette.application.service.provider.dto.ProviderType import ProviderType


class ISourceCalendar(ABC):
    """Base interface for calendar sources

    All implementations must include a 'provider_type: ProviderType' field.
    """

    # Type hint for static analysis - all implementations must have this field
    provider_type: "ProviderType"
