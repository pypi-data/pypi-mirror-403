from dataclasses import dataclass
from typing import Generic

from clochette.infrastructure.clock.Generics import DateOrDatetimeType


@dataclass(frozen=True)
class ExclusionDTO(Generic[DateOrDatetimeType]):
    uid: str
    exclusion: DateOrDatetimeType
    inclusion: DateOrDatetimeType
    raw: str
