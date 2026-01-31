from dataclasses import dataclass


@dataclass(frozen=True)
class BasicAuthDTO:
    username: str
    password: str
    cancelled: bool = False
