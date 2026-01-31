from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict


class ACPMessage(TypedDict, total=False):
    role: str
    content: str
    tool_calls: List[Dict[str, Any]]
    tool_result: Any
    tool_call_id: str


class ACPSession(TypedDict, total=False):
    session_id: str
    messages: List[ACPMessage]
    metadata: Dict[str, Any]


class ACPRequest(TypedDict, total=False):
    request_id: str
    client_id: str
    session_id: str
    messages: List[ACPMessage]
    input: Any
    metadata: Dict[str, Any]


class ACPResponse(TypedDict, total=False):
    request_id: str
    session_id: str
    ok: bool
    output: Any
    messages: List[ACPMessage]
    error: str


@dataclass(frozen=True)
class ACPEndpoint:
    base_url: str
    execute_path: str = "/acp/execute"
    timeout_s: float = 60.0

    def execute_url(self) -> str:
        return self.base_url.rstrip("/") + self.execute_path

