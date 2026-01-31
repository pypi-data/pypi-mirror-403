from dataclasses import dataclass

from oauthlib.oauth2 import OAuth2Token
from reactivex import Observable

from clochette.provider.shared.oauth2.OAuth2Service import OAuth2Service

GOOGLE_REMOTE_SERVER_URL = "https://66qc7wp4gq626iuufa76exbnri0okjiw.lambda-url.ap-southeast-2.on.aws/"


@dataclass
class GoogleOAuth2Service:
    _oauth2_service: OAuth2Service

    def __post_init__(self):
        self._remote_server_url = GOOGLE_REMOTE_SERVER_URL

    def refresh_token(self, token: OAuth2Token) -> OAuth2Token:
        return self._oauth2_service.refresh_token(self._remote_server_url, token)

    def authenticate(self) -> Observable[OAuth2Token]:
        return self._oauth2_service.authenticate(self._remote_server_url)

    def has_expired(self, token: OAuth2Token) -> bool:
        return self._oauth2_service.has_expired(token)
