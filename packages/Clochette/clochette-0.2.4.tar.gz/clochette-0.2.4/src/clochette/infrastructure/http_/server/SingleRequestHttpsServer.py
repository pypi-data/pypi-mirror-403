import ssl
import threading
from http.server import HTTPServer
from tempfile import NamedTemporaryFile

from PySide6.QtCore import QFile

from clochette.infrastructure.http_.server.RequestHandlerFactory import HttpRequestHandlerBuilder
from clochette.res.ResUtils import read_file


class SingleRequestHttpsServer:
    HOSTNAME = "localhost"

    _event: threading.Event
    _request_handler_builder: HttpRequestHandlerBuilder
    _http_server: HTTPServer
    _port: int

    def __init__(self, request_handler_builder: HttpRequestHandlerBuilder, port: int = 0):
        self._event = threading.Event()
        self._request_handler_builder = request_handler_builder
        self._port = port

    def _start_server(self) -> None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.check_hostname = False

        # https://github.com/encode/httpx/discussions/2037#discussioncomment-2006795
        with NamedTemporaryFile(mode="w+b") as cert_file, NamedTemporaryFile(mode="w+b") as key_file:
            cert_file.write(read_file(QFile(":/cert.pem")))
            cert_file.seek(0)

            key_file.write(read_file(QFile(":/key.pem")))
            key_file.seek(0)

            context.load_cert_chain(certfile=cert_file.name, keyfile=key_file.name)

        with HTTPServer(
            (SingleRequestHttpsServer.HOSTNAME, self._port), self._request_handler_builder
        ) as self._http_server:
            self._http_server.socket = context.wrap_socket(self._http_server.socket, server_side=True)
            # handle a single request
            self._event.set()
            self._http_server.serve_forever()

    def start(self) -> None:
        server_thread = threading.Thread(target=self._start_server)
        server_thread.daemon = True
        server_thread.start()
        # wait till the server has been started
        self._event.wait()

    def _stop_server(self) -> None:
        self._http_server.shutdown()

    def stop(self) -> None:
        server_thread = threading.Thread(target=self._stop_server)
        server_thread.daemon = True
        server_thread.start()

    def get_url(self) -> str:
        return f"https://{SingleRequestHttpsServer.HOSTNAME}:{self._http_server.server_port}"
