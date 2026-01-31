from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, eq=True)
class CalendarID:
    id: str

    def __post_init__(self):
        if not self.id:
            raise Exception("id cannot be empty")

    @staticmethod
    def new():
        return CalendarID(str(uuid4()))
