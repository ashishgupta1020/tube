import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from backend.src.app.container import build_container
from backend.src.routes.http_response import HttpResponse


LOGGER = logging.getLogger(__name__)


class AppRequestHandler(BaseHTTPRequestHandler):
    server_version = "TubeBackend/0.1"

    def do_GET(self) -> None:
        self._dispatch(write_body=True)

    def do_HEAD(self) -> None:
        self._dispatch(write_body=False)

    def _dispatch(self, write_body: bool) -> None:
        parsed = urlparse(self.path)
        response: HttpResponse = self.server.router.dispatch("GET", parsed.path)  # type: ignore[attr-defined]
        body = response.body if isinstance(response.body, bytes) else json.dumps(response.body).encode("utf-8")

        self.send_response(response.status_code)
        for header_name, header_value in response.headers.items():
            self.send_header(header_name, header_value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if write_body:
            self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)


def run_server() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    container = build_container()
    server = ThreadingHTTPServer(
        (container.settings.host, container.settings.port),
        AppRequestHandler,
    )
    server.router = container.router  # type: ignore[attr-defined]

    container.refresh_job.start()

    LOGGER.info(
        "starting backend server on http://%s:%s",
        container.settings.host,
        container.settings.port,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("shutting down backend server")
    finally:
        container.refresh_job.stop()
        server.server_close()
