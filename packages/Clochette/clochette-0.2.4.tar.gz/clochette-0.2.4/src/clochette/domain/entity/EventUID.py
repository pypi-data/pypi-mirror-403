from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class EventUID:
    id: str
