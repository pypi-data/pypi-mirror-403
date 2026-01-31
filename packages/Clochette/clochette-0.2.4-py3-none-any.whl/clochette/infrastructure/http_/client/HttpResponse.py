import json
from dataclasses import dataclass
from typing import Any

from requests import Response
from requests.structures import CaseInsensitiveDict


@dataclass(frozen=True)
class HttpResponse:
    _response: Response

    @property
    def content_utf8(self) -> str | None:
        if self._response.content is None:
            return None
        return self._response.content.decode("utf-8")

    @property
    def content_json(self) -> Any | None:
        if self._response.content is None:
            return None
        return json.loads(self._response.content)

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> CaseInsensitiveDict[str]:  # shouldn't leak CaseInsensitiveDict, but, oh well...
        return self._response.headers

    def is_successful(self) -> bool:
        return self.status_code >= 200 and self.status_code < 300
