from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .types import ACPEndpoint, ACPRequest, ACPResponse


def _normalize_acp_response(raw: object) -> ACPResponse:
    out: ACPResponse = {}
    if not isinstance(raw, dict):
        out["ok"] = False
        out["error"] = "Invalid response shape"
        return out

    rid = raw.get("request_id")
    if isinstance(rid, str):
        out["request_id"] = rid
        
    sid = raw.get("session_id")
    if isinstance(sid, str):
        out["session_id"] = sid
        
    ok = raw.get("ok")
    if isinstance(ok, bool):
        out["ok"] = ok
        
    output = raw.get("output")
    if output is not None:
        out["output"] = output

    msgs = raw.get("messages")
    if isinstance(msgs, list):
        out["messages"] = msgs  # type: ignore[assignment]
        
    err = raw.get("error")
    if isinstance(err, str):
        out["error"] = err

    if "ok" not in out:
        out["ok"] = False
    return out


@dataclass
class ACPClient:
    """
    Minimal stdlib HTTP client for ACP (contract-level parity).
    """

    endpoint: ACPEndpoint

    def execute(self, request: ACPRequest) -> ACPResponse:
        payload = json.dumps(dict(request or {}), ensure_ascii=False, sort_keys=True).encode("utf-8")
        http_req = urllib.request.Request(url=self.endpoint.execute_url(), data=payload, method="POST")
        http_req.add_header("Content-Type", "application/json")
        http_req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(http_req, timeout=self.endpoint.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                raw = json.loads(body) if body else {}
                return _normalize_acp_response(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp is not None else ""
            http_err_resp: ACPResponse = {"ok": False, "error": f"HTTP {e.code}: {body}"}
            return http_err_resp
        except urllib.error.URLError as e:
            url_err_resp: ACPResponse = {"ok": False, "error": f"Request failed: {e}"}
            return url_err_resp

