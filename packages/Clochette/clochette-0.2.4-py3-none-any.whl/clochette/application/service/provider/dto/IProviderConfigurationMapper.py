from abc import ABC, abstractmethod
from configparser import SectionProxy
from typing import Generic, TypeVar

_T = TypeVar("_T")


class IProviderConfigurationMapper(ABC, Generic[_T]):
    @abstractmethod
    def match(self, section: SectionProxy) -> bool:
        """Check if this mapper can handle the given configuration section"""
        pass

    @abstractmethod
    def read(self, section: SectionProxy) -> _T:
        pass

    @abstractmethod
    def write(self, source: _T) -> dict[str, str]:
        pass
