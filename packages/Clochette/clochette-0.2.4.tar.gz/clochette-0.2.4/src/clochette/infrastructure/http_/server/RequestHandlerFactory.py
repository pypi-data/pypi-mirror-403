from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import BaseRequestHandler
from typing import Any, Callable, TypeAlias

HttpRequestHandler: TypeAlias = Callable[[BaseHTTPRequestHandler], None]
HttpRequestHandlerBuilder: TypeAlias = Callable[[Any, Any, HTTPServer], BaseRequestHandler]


class RequestHandlerFactory:
    _request_handler: HttpRequestHandler

    def __init__(self, request_handler: HttpRequestHandler):
        self._request_handler = request_handler

    def __call__(self, request: Any, client_address: Any, server: HTTPServer) -> BaseHTTPRequestHandler:
        class CustomRequestHandler(BaseHTTPRequestHandler):
            _request_handler: HttpRequestHandler

            def log_message(self, format: str, *args: Any) -> None:
                # Override this method to disable logging
                pass

            def __init__(self, *args: Any, request_handler: HttpRequestHandler, **kwargs: Any) -> None:
                self._request_handler = request_handler
                super().__init__(*args, **kwargs)

            def do_GET(self) -> None:
                return self._request_handler(self)

        return CustomRequestHandler(request, client_address, server, request_handler=self._request_handler)
