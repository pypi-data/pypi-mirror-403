from __future__ import annotations

import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional, Tuple

from ..agent import AIAgent
from ..messages import Prompt, AssistantMessage, SystemMessage, UserMessage, ToolCallMessage, ToolResultMessage
from .types import ACPRequest, ACPResponse, ACPMessage


def _prompt_from_acp_messages(messages: List[ACPMessage]) -> Prompt:
    prompt = Prompt()
    for m in messages or []:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        tool_calls = m.get("tool_calls")
        tool_result = m.get("tool_result")
        tool_call_id = m.get("tool_call_id")

        if role == "system":
            prompt.append(SystemMessage(text=content))
        elif role == "assistant":
            # If we have tool calls, we construct one or more ToolCallMessages
            # Note: ACPMessage structure groups content + tool_calls.
            # Koog Prompt separates text+calls conceptually but AssistantMessage can hold text.
            # Koog's ToolCallMessage holds the tool calls.
            if tool_calls:
                # If there's content, add it first
                if content:
                    prompt.append(AssistantMessage(text=content))
                for tc in tool_calls:
                   # Attempt to extract correct fields
                   t_name = tc.get("function", {}).get("name") or tc.get("name")
                   t_args = tc.get("function", {}).get("arguments") or tc.get("args")
                   t_id = tc.get("id") or tc.get("tool_call_id")
                   
                   # Depending on how clients send it, arguments might be a JSON string or dict
                   if isinstance(t_args, str):
                       try:
                           t_args = json.loads(t_args)
                       except:
                           pass
                           
                   prompt.append(ToolCallMessage(tool_call_id=str(t_id), tool=str(t_name), args=t_args or {}))
            else:
                prompt.append(AssistantMessage(text=content))

        elif role == "tool":
            prompt.append(ToolResultMessage(tool_call_id=str(tool_call_id), result=tool_result))
        else:
            prompt.append(UserMessage(text=content))
    return prompt


def _acp_messages_from_prompt(prompt: Prompt) -> List[ACPMessage]:
    out: List[ACPMessage] = []
    # This is a simplification. A robust implementation would coalesce adjacent tool calls 
    # into a single assistant message if the protocol expects that.
    # For now, we map 1:1 where possible, or flatten.
    
    current_assistant_msg: Optional[ACPMessage] = None

    for m in prompt.messages:
        if isinstance(m, SystemMessage):
            out.append({"role": "system", "content": m.text})
        elif isinstance(m, AssistantMessage):
            # Pure text assistant message or mixed?
            # Koog AssistantMessage is text-only usually. Tool calls are separate messages.
            out.append({"role": "assistant", "content": m.text})
        elif isinstance(m, ToolCallMessage):
            # We need to look back and see if we can attach this to the previous assistant message
            # or creates a new one. 
            # For simplicity, let's create a new structure or append to list.
            # ACP often expects tool calls to be part of an assistant message.
            
            # If last message was assistant, append to it
            if out and out[-1]["role"] == "assistant":
                 last = out[-1]
                 if "tool_calls" not in last:
                     last["tool_calls"] = []
                 last["tool_calls"].append({
                     "id": m.tool_call_id,
                     "type": "function",
                     "function": {
                         "name": m.tool,
                         "arguments": m.args
                     }
                 })
            else:
                # new assistant message for tool call
                out.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": m.tool_call_id,
                        "type": "function",
                        "function": {
                            "name": m.tool,
                            "arguments": m.args
                        }
                    }]
                })

        elif isinstance(m, ToolResultMessage):
            out.append({
                "role": "tool", 
                "tool_call_id": m.tool_call_id, 
                "tool_result": m.result,
                "content": str(m.result) # text representation
            })
        elif isinstance(m, UserMessage):
             out.append({"role": "user", "content": m.text})
             
    return out


@dataclass
class ACPServerConfig:
    host: str = "127.0.0.1"
    port: int = 8081
    path_execute: str = "/acp/v1/query"


def make_handler(*, agent: AIAgent, config: ACPServerConfig) -> type[BaseHTTPRequestHandler]:
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

            request: ACPRequest = req  # type: ignore[assignment]
            rid = str(request.get("request_id") or "")
            sid = str(request.get("session_id") or "") # TODO: Handle session lookup

            try:
                # 1. Parse incoming messages
                # If session exists, we might merge? For now, stateless or full-history-in-request is common for simple servers.
                # Assuming full history passed for now or simple stateless.
                input_msgs = list(request.get("messages") or [])
                prompt = _prompt_from_acp_messages(input_msgs)
                
                # 2. Setup agent
                agent.session.prompt = prompt
                
                # 3. Run agent
                input_val = request.get("input") 
                # If input is provided, it might be the trigger. 
                # If only messages provided, maybe last user message is the input? 
                # Koog agent.run() usually takes an input string.
                
                if input_val is None:
                    # try to extract last user text
                    if prompt.messages and isinstance(prompt.messages[-1], UserMessage):
                       input_val = prompt.messages[-1].text
                
                output = agent.run(input_val)

                # 4. Response
                resp: ACPResponse = {
                    "ok": True,
                    "request_id": rid,
                    "session_id": sid,
                    "output": output,
                    "messages": _acp_messages_from_prompt(agent.session.prompt)
                }
                self._send_json(200, dict(resp))

            except Exception as e:
                err_resp: ACPResponse = {
                    "ok": False,
                    "request_id": rid, 
                    "error": str(e)
                }
                self._send_json(500, dict(err_resp))

        def log_message(self, fmt: str, *args: Any) -> None:
             return

    return Handler


def serve(*, agent: AIAgent, config: Optional[ACPServerConfig] = None) -> HTTPServer:
    cfg = config or ACPServerConfig()
    handler = make_handler(agent=agent, config=cfg)
    return HTTPServer((cfg.host, int(cfg.port)), handler)
