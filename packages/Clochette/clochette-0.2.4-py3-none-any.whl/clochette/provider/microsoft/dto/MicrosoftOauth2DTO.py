from dataclasses import dataclass


@dataclass
class MicrosoftOauth2DTO:
    token: str
    cancelled: bool = False
