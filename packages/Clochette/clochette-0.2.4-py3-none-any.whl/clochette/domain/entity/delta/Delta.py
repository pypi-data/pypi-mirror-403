from abc import ABC, abstractmethod
from datetime import timedelta


class Delta(ABC):
    """Abstract base class for timedelta wrappers"""

    @abstractmethod
    def get_timedelta(self) -> timedelta:
        """Get the underlying timedelta value"""
        pass
