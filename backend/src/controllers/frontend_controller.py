from __future__ import annotations

import mimetypes
from pathlib import Path

from backend.src.routes.http_response import HttpResponse, file_response, not_found_response


class FrontendController:
    def __init__(self, frontend_root: Path) -> None:
        self._frontend_root = frontend_root.resolve()

    def get_index(self) -> HttpResponse:
        return self._serve_file(self._frontend_root / "index.html", cache_control="no-cache")

    def get_asset(self, path: str) -> HttpResponse:
        requested_path = (self._frontend_root / path.lstrip("/")).resolve()
        if not self._is_within_root(requested_path) or not requested_path.is_file():
            return not_found_response()

        cache_control = "public, max-age=3600"
        if requested_path.name in {"app.js", "styles.css"}:
            cache_control = "no-cache"

        return self._serve_file(requested_path, cache_control=cache_control)

    def _serve_file(self, path: Path, cache_control: str) -> HttpResponse:
        mime_type, _ = mimetypes.guess_type(path.name)
        content_type = mime_type or "application/octet-stream"

        return file_response(
            "{content_type}; charset=utf-8".format(content_type=content_type)
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}
            else content_type,
            path.read_bytes(),
            cache_control=cache_control,
        )

    def _is_within_root(self, path: Path) -> bool:
        try:
            path.relative_to(self._frontend_root)
        except ValueError:
            return False
        return True
