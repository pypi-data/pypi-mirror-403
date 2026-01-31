from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class Contact:
    cn: str
    mailto: str
    accepted: bool
