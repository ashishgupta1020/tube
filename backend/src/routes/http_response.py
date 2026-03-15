from __future__ import annotations

from dataclasses import dataclass


JSON_CONTENT_TYPE = "application/json; charset=utf-8"


@dataclass(frozen=True)
class HttpResponse:
    """Represents an HTTP response before it is written to the socket."""

    status_code: int
    headers: dict[str, str]
    body: bytes | dict


def json_response(
    status_code: int,
    body: dict,
    *,
    cache_control: str = "no-store",
) -> HttpResponse:
    """Build a JSON response with standard headers."""

    return HttpResponse(
        status_code=status_code,
        headers={
            "Content-Type": JSON_CONTENT_TYPE,
            "Cache-Control": cache_control,
        },
        body=body,
    )


def file_response(content_type: str, body: bytes, *, cache_control: str) -> HttpResponse:
    """Build a file response with the provided content type and cache policy."""

    return HttpResponse(
        status_code=200,
        headers={
            "Content-Type": content_type,
            "Cache-Control": cache_control,
        },
        body=body,
    )


def not_found_response() -> HttpResponse:
    """Build the common API 404 response."""

    return json_response(404, {"error": "not found"})


def service_unavailable_response(message: str) -> HttpResponse:
    """Build the common API 503 response."""

    return json_response(503, {"error": message})
