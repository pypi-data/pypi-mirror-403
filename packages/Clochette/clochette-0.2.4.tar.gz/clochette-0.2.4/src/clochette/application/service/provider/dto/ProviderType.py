from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class ProviderType(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass
