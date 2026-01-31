from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict


# -------------------------
# Wire shapes (JSON payload)
# -------------------------


class A2AMessage(TypedDict, total=False):
    role: str
    content: str
    # Optional tool-call metadata (when transferring tool events between agents)
    tool: str
    tool_call_id: str
    args: Dict[str, Any]
    result: Any
    # List of tool calls for multi-tool interactions
    tool_calls: List[Dict[str, Any]]


class A2ARequest(TypedDict, total=False):
    # Identifier for tracing/debug; caller-generated
    request_id: str
    # Logical agent_id on the server (optional)
    agent_id: str
    # If provided, the server may restore/continue a session
    session_id: str
    # Prompt/messages for the run
    messages: List[A2AMessage]
    # Optional input payload for agent.run(...)
    input: Any


class A2AResponse(TypedDict, total=False):
    request_id: str
    agent_id: str
    session_id: str
    ok: bool
    # Output from agent.run(...)
    output: Any
    # Updated message history after execution
    messages: List[A2AMessage]
    error: str


# -------------------------
# Internal convenience types
# -------------------------


@dataclass(frozen=True)
class A2AEndpoint:
    base_url: str  # e.g. http://localhost:8080
    # path for execute endpoint
    execute_path: str = "/a2a/execute"
    timeout_s: float = 60.0

    def execute_url(self) -> str:
        return self.base_url.rstrip("/") + self.execute_path

