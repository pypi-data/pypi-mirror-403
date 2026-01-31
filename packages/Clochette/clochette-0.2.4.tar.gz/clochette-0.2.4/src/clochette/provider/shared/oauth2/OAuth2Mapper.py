import json

from oauthlib.oauth2 import OAuth2Token


class OAuth2Mapper:

    def to_oauth2_token(self, token: str) -> OAuth2Token:
        return OAuth2Token(json.loads(token))

    def from_oauth2_token(self, token: OAuth2Token) -> str:
        return json.dumps(token)
