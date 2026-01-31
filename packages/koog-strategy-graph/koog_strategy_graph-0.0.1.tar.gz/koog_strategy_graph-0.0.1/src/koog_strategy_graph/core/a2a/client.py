from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict

from .types import A2AEndpoint, A2ARequest, A2AResponse


def _normalize_a2a_response(raw: Any) -> A2AResponse:
    """
    Convert an untyped JSON-decoded payload into an `A2AResponse` TypedDict.
    """
    out: A2AResponse = {}
    if not isinstance(raw, dict):
        out["ok"] = False
        out["error"] = "Invalid response shape"
        return out

    # Optional identifiers
    rid = raw.get("request_id")
    if isinstance(rid, str):
        out["request_id"] = rid
    aid = raw.get("agent_id")
    if isinstance(aid, str):
        out["agent_id"] = aid
    sid = raw.get("session_id")
    if isinstance(sid, str):
        out["session_id"] = sid

    ok = raw.get("ok")
    if isinstance(ok, bool):
        out["ok"] = ok

    if "output" in raw:
        out["output"] = raw.get("output")

    msgs = raw.get("messages")
    if isinstance(msgs, list):
        # Keep as-is (wire type is a TypedDict list; runtime validation is best-effort here).
        out["messages"] = msgs  # type: ignore[assignment]

    err = raw.get("error")
    if isinstance(err, str):
        out["error"] = err

    # Default ok=false if the server didn't provide it.
    if "ok" not in out:
        out["ok"] = False
    return out


@dataclass
class A2AClient:
    """
    Minimal stdlib HTTP client for A2A.

    This is intentionally synchronous and dependency-free.
    """

    endpoint: A2AEndpoint

    def execute(self, request: A2ARequest) -> A2AResponse:
        payload = json.dumps(dict(request or {}), ensure_ascii=False, sort_keys=True).encode("utf-8")
        http_req = urllib.request.Request(url=self.endpoint.execute_url(), data=payload, method="POST")
        http_req.add_header("Content-Type", "application/json")
        http_req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(http_req, timeout=self.endpoint.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                raw = json.loads(body) if body else {}
                return _normalize_a2a_response(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp is not None else ""
            http_err_resp: A2AResponse = {"ok": False, "error": f"HTTP {e.code}: {body}"}
            return http_err_resp
        except urllib.error.URLError as e:
            url_err_resp: A2AResponse = {"ok": False, "error": f"Request failed: {e}"}
            return url_err_resp

