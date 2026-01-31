from dataclasses import dataclass


@dataclass
class GoogleOauth2DTO:
    token: str
    cancelled: bool = False
