from __future__ import annotations

import json
import logging
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.src.config.settings import Settings


LOGGER = logging.getLogger(__name__)


class TflClientError(Exception):
    """Raised when the TfL API request flow fails."""


class TflClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_stop_points(self) -> list[dict]:
        stop_points: list[dict] = []
        page = 1
        total = None
        page_size = None

        while total is None or len(stop_points) < total:
            payload = self._request_json(
                "/StopPoint/Mode/{modes}".format(modes=self._settings.scoped_modes_query),
                {"page": page},
            )

            if not isinstance(payload, dict) or not isinstance(payload.get("stopPoints"), list):
                raise TflClientError("TfL stop-point response was not in the expected format")

            page_items = payload["stopPoints"]
            total = int(payload.get("total", len(page_items)))
            page_size = int(payload.get("pageSize", len(page_items) or 1))
            stop_points.extend(page_items)

            LOGGER.info(
                "fetched TfL stop-points page=%s page_size=%s collected=%s total=%s",
                page,
                page_size,
                len(stop_points),
                total,
            )

            if not page_items:
                break
            page += 1

        return stop_points

    def _request_json(self, path: str, query: dict[str, object] | None = None) -> object:
        params = dict(query or {})
        if self._settings.tfl_app_key:
            params["app_key"] = self._settings.tfl_app_key

        url = "{base}{path}".format(base=self._settings.tfl_base_url.rstrip("/"), path=path)
        if params:
            url = "{url}?{query}".format(url=url, query=urlencode(params))

        last_error: Exception | None = None
        attempt_count = self._settings.tfl_retry_count + 1

        for attempt in range(1, attempt_count + 1):
            request = Request(url, headers={"User-Agent": "tube-backend/0.1"})
            try:
                with urlopen(request, timeout=self._settings.tfl_timeout_seconds) as response:
                    return json.load(response)
            except (HTTPError, URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
                last_error = exc
                LOGGER.warning("TfL request failed attempt=%s url=%s error=%s", attempt, url, exc)
                if attempt == attempt_count:
                    break
                time.sleep(0.25 * attempt)

        raise TflClientError("failed to fetch TfL data: {error}".format(error=last_error))
