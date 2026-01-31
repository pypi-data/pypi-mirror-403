import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler

from oauthlib.oauth2 import OAuth2Token
from reactivex import Subject, Observable, defer
from reactivex import operators as ops

from clochette import log
from clochette.infrastructure.clock.ClockService import ClockService
from clochette.infrastructure.http_.client.HttpService import HttpService
from clochette.infrastructure.http_.server.RequestHandlerFactory import RequestHandlerFactory
from clochette.infrastructure.http_.server.SingleRequestHttpsServer import SingleRequestHttpsServer
from clochette.presentation.window.QWebBrowserWindow import QWebBrowserWindow


@dataclass(frozen=True)
class OAuth2Service:
    _http_service: HttpService
    _clock_service: ClockService
    _web_browser_window: QWebBrowserWindow
    _port: int = 0

    def refresh_token(self, remote_server_url: str, token: OAuth2Token) -> OAuth2Token:
        headers = {"Content-Type": "application/json"}

        body = {"action": "refresh_token", "refresh_token": token.get("refresh_token")}

        response = self._http_service.post(remote_server_url, json.dumps(body), headers)

        json_response = response.content_json
        if json_response is None or not response.is_successful():
            raise Exception(f"Failed to refresh token, http status: {response.status_code}")
        else:
            return OAuth2Token(json_response)

    def authenticate(self, remote_server_url: str) -> Observable[OAuth2Token]:
        return defer(lambda _: self._authenticate(remote_server_url))

    def _authenticate(self, remote_server_url: str):
        log.info("Retrieving a valid token")
        authorization_subject: Subject[str] = Subject()

        def do_get(request_handler: BaseHTTPRequestHandler) -> None:
            log.debug("Authorization received")
            request_handler.send_response(200)
            request_handler.send_header("Content-type", "text/html")
            request_handler.end_headers()
            request_handler.wfile.write(b"Oauth2 callback received")
            authorization_subject.on_next(request_handler.path)

        http_server = SingleRequestHttpsServer(RequestHandlerFactory(do_get), self._port)
        http_server.start()

        redirect_uri = http_server.get_url() + "/callback"

        location = self._retrieve_location(remote_server_url, redirect_uri)
        log.debug("Location retrieved, opening Web Browser")
        self._web_browser_window.show_browser()
        self._web_browser_window.load_url(location)
        self._web_browser_window.on_browser_closed.link(
            lambda: authorization_subject.on_error(Exception("Closed the browser before authenticating"))
        )

        def cleanup() -> None:
            http_server.stop()
            self._web_browser_window.hide_browser()

        return authorization_subject.pipe(
            ops.do_action(lambda _: cleanup()),
            ops.map(lambda r: self._fetch_token(remote_server_url, r, redirect_uri)),
        )

    def _retrieve_location(self, remote_server_url: str, redirect_uri: str) -> str:
        log.info(f"Authenticating to URI: {remote_server_url}")
        headers = {"Content-Type": "application/json"}

        body = {"action": "authenticate", "redirect_uri": redirect_uri}

        response = self._http_service.post(remote_server_url, json.dumps(body), headers)
        location = response.headers.get("location", None)

        if not location:
            raise Exception("No location received during authentication")

        return location

    def _fetch_token(self, remote_server_url: str, authorization_response: str, redirect_uri: str) -> OAuth2Token:
        log.info("Fetching token")
        headers = {"Content-Type": "application/json"}

        body = {"action": "fetch_token", "authorization_response": authorization_response, "redirect_uri": redirect_uri}
        response = self._http_service.post(remote_server_url, json.dumps(body), headers)

        json_response = response.content_json
        if json_response is None or not response.is_successful():
            raise Exception(f"Failed to authenticate, http status: {response.status_code}")
        else:
            return OAuth2Token(json_response)

    def has_expired(self, token: OAuth2Token) -> bool:
        return self._clock_service.epoch() > int(token["expires_at"])
