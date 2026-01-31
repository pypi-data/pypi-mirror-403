from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Tuple, List

from ..agent import AIAgent
from ..messages import Prompt, ToolCallMessage, ToolResultMessage, AssistantMessage, SystemMessage, UserMessage
from .types import A2ARequest, A2AResponse, A2AMessage


def _prompt_from_a2a_messages(messages: list[A2AMessage]) -> Prompt:
    prompt = Prompt()
    for m in messages or []:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        
        # Check for tool info
        tool_calls = m.get("tool_calls")
        tool_name = m.get("tool")
        tool_call_id = m.get("tool_call_id")
        tool_args = m.get("args")
        tool_result = m.get("result")

        if role == "system":
            prompt.append(SystemMessage(text=content))
        elif role == "assistant":
            if content:
                prompt.append(AssistantMessage(text=content))
                
            # Handle new tool_calls list
            if tool_calls:
                for tc in tool_calls:
                    t_id = tc.get("id") or tc.get("tool_call_id")
                    t_name = tc.get("name") or (tc.get("function") or {}).get("name")
                    t_args = tc.get("args") or (tc.get("function") or {}).get("arguments")
                    # Args might be dict or json string
                    if isinstance(t_args, str):
                        try:
                            t_args = json.loads(t_args)
                        except:
                            pass
                    prompt.append(ToolCallMessage(tool_call_id=str(t_id), tool=str(t_name), args=t_args or {}))
            
            # Handle legacy flat tool call (if present)
            elif tool_name:
                prompt.append(ToolCallMessage(
                    tool_call_id=str(tool_call_id or ""), 
                    tool=tool_name, 
                    args=tool_args or {}
                ))

        elif role == "tool":
            prompt.append(ToolResultMessage(tool_call_id=str(tool_call_id), result=tool_result))
            
        else:
            prompt.append(UserMessage(text=content))
    return prompt


def _a2a_messages_from_prompt(prompt: Prompt) -> list[A2AMessage]:
    out: list[A2AMessage] = []
    
    for m in prompt.messages:
        if isinstance(m, SystemMessage):
            out.append({"role": "system", "content": m.text})
        elif isinstance(m, AssistantMessage):
            out.append({"role": "assistant", "content": m.text})
        elif isinstance(m, ToolCallMessage):
            # Append as assistant message with tool_calls
            # If previous was assistant, we could merge, but for now append valid A2AMessage
            out.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": m.tool_call_id,
                    "type": "function",
                    "function": {"name": m.tool, "arguments": m.args}
                }],
                # Populate legacy flat fields for compatibility if needed? 
                # Let's populate minimal required.
            })
        elif isinstance(m, ToolResultMessage):
            out.append({
                "role": "tool",
                "tool_call_id": m.tool_call_id,
                "result": m.result,
                "content": str(m.result)
            })
        elif isinstance(m, UserMessage):
            out.append({"role": "user", "content": m.text})
            
    return out


@dataclass
class A2AServerConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    path_execute: str = "/a2a/execute"


def make_handler(*, agent: AIAgent, config: A2AServerConfig) -> type[BaseHTTPRequestHandler]:
    """
    Create a stdlib HTTP handler bound to a specific `AIAgent`.
    """

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, code: int, obj: Dict[str, Any]) -> None:
            body = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != config.path_execute:
                self._send_json(404, {"ok": False, "error": f"Unknown path: {self.path}"})
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else ""
            try:
                req = json.loads(raw) if raw else {}
            except Exception:
                self._send_json(400, {"ok": False, "error": "Invalid JSON"})
                return

            if not isinstance(req, dict):
                self._send_json(400, {"ok": False, "error": "Invalid request shape"})
                return

            request: A2ARequest = req  # type: ignore[assignment]
            request_id = str(request.get("request_id") or "")
            try:
                msgs = list(request.get("messages") or [])
                prompt = _prompt_from_a2a_messages(msgs)

                # Reuse existing agent session/prompt by copying in the provided prompt.
                agent.session.prompt = prompt

                input_value = request.get("input")
                # If input missing, try last user message
                if input_value is None and prompt.messages and isinstance(prompt.messages[-1], UserMessage):
                     input_value = prompt.messages[-1].text
                
                out = agent.run(input_value)
                ok_resp: A2AResponse = {
                    "ok": True,
                    "request_id": request_id,
                    "agent_id": agent.agent_id,
                    "messages": _a2a_messages_from_prompt(agent.session.prompt),
                    "output": out,
                }
                self._send_json(200, dict(ok_resp))
            except Exception as e:
                err_resp: A2AResponse = {
                    "ok": False,
                    "request_id": request_id,
                    "agent_id": agent.agent_id,
                    "error": str(e),
                }
                self._send_json(500, dict(err_resp))

        def log_message(self, fmt: str, *args: Any) -> None:
            # Keep stdlib handler quiet by default (tests/dev can wrap if needed).
            _ = fmt
            _ = args
            return

    return Handler


try:
    from http.server import ThreadingHTTPServer
except ImportError:
    from http.server import HTTPServer as ThreadingHTTPServer

def serve(*, agent: AIAgent, config: Optional[A2AServerConfig] = None) -> HTTPServer:
    """
    Create (but do not block on) an HTTPServer for the given agent.
    Caller controls `server.serve_forever()` / shutdown.
    """
    cfg = config or A2AServerConfig()
    handler = make_handler(agent=agent, config=cfg)
    # Use ThreadingHTTPServer to allow parallel A2A calls.
    return ThreadingHTTPServer((cfg.host, int(cfg.port)), handler)
