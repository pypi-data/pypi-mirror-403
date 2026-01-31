from abc import abstractmethod, ABC


class AuthCalendar(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def summary(self) -> str:
        pass
