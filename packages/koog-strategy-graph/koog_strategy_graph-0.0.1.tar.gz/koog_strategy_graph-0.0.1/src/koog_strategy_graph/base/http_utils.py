from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import IO, Any, Iterator


def json_dumps_compact(obj: Any) -> str:
    """
    Provider-agnostic JSON serializer intended for HTTP payloads.

    - Stable key order (sort_keys=True) to make tests/traces reproducible
    - Compact encoding to reduce payload size
    """

    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def iter_sse_data(resp: IO[bytes]) -> Iterator[str]:
    """
    Iterate Server-Sent Events payloads.

    Yields the `data: ...` content (decoded as utf-8) per event.
    Also tolerates some proxy/gateway behaviors that return one JSON object per line
    even when the Content-Type is `text/event-stream`.
    """

    while True:
        line_b = resp.readline()
        if not line_b:
            break
        line = line_b.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        # Standard SSE
        if line.startswith("data:"):
            yield line[len("data:") :].strip()
            continue

        # Some proxies/gateways return JSON objects one-per-line even when the Content-Type
        # is text/event-stream. Accept those as "event payloads" too.
        if line == "[DONE]":
            yield line
            continue
        if line.startswith("{") or line.startswith("["):
            yield line
            continue


def http_post_json(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_s: float,
    error_prefix: str = "",
) -> dict[str, Any]:
    """
    Provider-agnostic stdlib HTTP POST helper for JSON APIs.

    - Uses `urllib.request`
    - Serializes payload with `json_dumps_compact`
    - Parses JSON response body into a dict
    - Raises RuntimeError with helpful body snippets on HTTP errors
    """

    data = json_dumps_compact(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method="POST")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    req.add_header("Content-Type", "application/json")

    prefix = (error_prefix or "").strip()
    prefix = f"{prefix} " if prefix else ""

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp is not None else ""
        raise RuntimeError(f"{prefix}HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"{prefix}request failed: {e}") from e

