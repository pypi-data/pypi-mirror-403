from typing import Any

import requests

from clochette import log
from clochette.domain.entity.configuration.HttpTimeout import HttpTimeout
from clochette.infrastructure.http_.client.HttpResponse import HttpResponse


class HttpService:

    def get(
        self,
        url: str,
        headers: None | dict[str, Any] = None,
        http_timeout: HttpTimeout = HttpTimeout.default(),
    ) -> HttpResponse:
        if headers is None:
            headers = {}

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=(http_timeout.connection_timeout, http_timeout.read_timeout),
            )
            return HttpResponse(response)
        except Exception as e:
            log.warning(f"Failed to download {url}")
            raise e

    def post(
        self,
        url: str,
        body: str,
        headers: None | dict[str, Any] = None,
        http_timeout: HttpTimeout = HttpTimeout.default(),
        allow_redirects: bool = False,
    ) -> HttpResponse:
        if headers is None:
            headers = {}

        try:
            response = requests.post(
                url,
                data=body,
                headers=headers,
                timeout=(http_timeout.connection_timeout, http_timeout.read_timeout),
                allow_redirects=allow_redirects,
            )

            return HttpResponse(response)
        except Exception as e:
            log.warning(f"Failed to download {url}")
            raise e
