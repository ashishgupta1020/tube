from __future__ import annotations

import mimetypes
from pathlib import Path


class FrontendController:
    def __init__(self, frontend_root: Path) -> None:
        self._frontend_root = frontend_root.resolve()

    def get_index(self) -> tuple[int, dict[str, str], bytes]:
        return self._serve_file(self._frontend_root / "index.html", cache_control="no-cache")

    def get_asset(self, path: str) -> tuple[int, dict[str, str], bytes | dict]:
        requested_path = (self._frontend_root / path.lstrip("/")).resolve()
        if not self._is_within_root(requested_path) or not requested_path.is_file():
            return (
                404,
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Cache-Control": "no-store",
                },
                {"error": "not found"},
            )

        cache_control = "public, max-age=3600"
        if requested_path.name in {"app.js", "styles.css"}:
            cache_control = "no-cache"

        return self._serve_file(requested_path, cache_control=cache_control)

    def _serve_file(self, path: Path, cache_control: str) -> tuple[int, dict[str, str], bytes]:
        mime_type, _ = mimetypes.guess_type(path.name)
        content_type = mime_type or "application/octet-stream"

        return (
            200,
            {
                "Content-Type": "{content_type}; charset=utf-8".format(content_type=content_type)
                if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}
                else content_type,
                "Cache-Control": cache_control,
            },
            path.read_bytes(),
        )

    def _is_within_root(self, path: Path) -> bool:
        try:
            path.relative_to(self._frontend_root)
        except ValueError:
            return False
        return True
