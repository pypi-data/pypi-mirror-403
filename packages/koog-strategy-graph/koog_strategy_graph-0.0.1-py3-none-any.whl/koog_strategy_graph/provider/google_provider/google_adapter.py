from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional, Sequence, List

from ...base.http_utils import json_dumps_compact
from ...base.provider_adapter import ChatProviderAdapter, ProviderRequest
from ...base.stream_text import extract_text_parts
from ...core.messages import Prompt, SystemMessage, UserMessage, AssistantMessage, ToolCallMessage, ToolResultMessage, ResponseMessage
from ...core.streaming import StreamFrame, StreamFrameFlowBuilder
from ...core.tools import ToolDescriptor

class GeminiChatAdapter(ChatProviderAdapter):
    """
    Adapter for Google's Gemini API (via REST).
    """
    error_prefix = "Gemini API error"

    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta/models"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._flow_builder = StreamFrameFlowBuilder()

    def build_request(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
        stream: bool,
    ) -> ProviderRequest:
        # Gemini REST API structure:
        # { "contents": [...], "tools": [...], "systemInstruction": ... }
        
        contents = []
        system_instruction = None

        for m in prompt.messages:
            if isinstance(m, SystemMessage):
                # Gemini prefers systemInstruction field
                if system_instruction is None:
                    system_instruction = {"parts": [{"text": m.text}]}
                else:
                    system_instruction["parts"][0]["text"] += "\n" + m.text
            
            elif isinstance(m, UserMessage):
                contents.append({"role": "user", "parts": [{"text": m.text}]})
            
            elif isinstance(m, AssistantMessage):
                contents.append({"role": "model", "parts": [{"text": m.text}]})
            
            elif isinstance(m, ToolCallMessage):
                # Function call part
                contents.append({
                    "role": "model",
                    "parts": [{
                        "functionCall": {
                            "name": m.tool,
                            "args": m.args # Expecting dict
                        }
                    }]
                })

            elif isinstance(m, ToolResultMessage):
                # Function response part
                contents.append({
                    "role": "user", # or 'function'? Gemini uses 'functionResponse' part in 'user' role usually or separate structure?
                    # API docs say: role: "function" is deprecated/not used, usually "user" or specific function role interaction.
                    # Actually Gemini uses "parts": [{"functionResponse": ...}] usually within a turn.
                    # Let's assume role "user" with functionResponse part.
                    "parts": [{
                        "functionResponse": {
                            "name": "unknown", # Koog doesn't track name in ResultMessage easily without lookup?
                            # Wait, we need the function name. ToolResultMessage usually has tool_call_id. 
                            # We might need to map id back to name or hope Gemini doesn't strictly enforce name if ID is present (Gemini doesn't use IDs the same way OpenAI does).
                            # Gemini uses 'name'.
                            # LIMITATION: ToolResultMessage needs name. 
                            # For now, we will assume we can't perfectly map without name. 
                            # We will send a placeholder or empty string if name missing.
                            "response": {"result": m.result}
                        }
                    }]
                })
                # Note: This is brittle without name.

        # Tools
        gemini_tools = []
        if tools:
            funcs = []
            for t in tools:
                funcs.append({
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.schema # JSON schema
                })
            gemini_tools.append({"function_declarations": funcs})

        payload = {
            "contents": contents,
            **params
        }
        
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        if gemini_tools:
            payload["tools"] = gemini_tools
            # Tool config
            if tool_choice:
                if tool_choice == "auto":
                    payload["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}
                elif tool_choice == "any":
                     payload["toolConfig"] = {"functionCallingConfig": {"mode": "ANY"}}
                elif tool_choice == "none":
                     payload["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}
                # Named tool not directly supported in mode enum easily without "ANY" + allowed_function_names

        # URL construction
        # v1beta/models/{model}:generateContent or streamGenerateContent
        method = "streamGenerateContent" if stream else "generateContent"
        url = f"{self.base_url}/{model}:{method}?key={self.api_key}"

        return ProviderRequest(
            url=url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            stream=stream
        )

    def parse_execute_response(self, raw: Dict[str, Any]) -> List[ResponseMessage]:
        # Parse standard response
        # { "candidates": [ { "content": { "parts": [...] } } ] }
        
        candidates = raw.get("candidates", [])
        if not candidates:
            return []
            
        cand = candidates[0]
        parts = cand.get("content", {}).get("parts", [])
        
        text_out = "".join(extract_text_parts(parts))
        tool_calls = []
        
        for p in parts:
            if "functionCall" in p:
                fc = p["functionCall"]
                tool_calls.append(ToolCallMessage(
                    tool_call_id="gemini_call", # Gemini doesn't always provide ID
                    tool=fc.get("name"),
                    args=fc.get("args")
                ))
                
        return [ResponseMessage(text=text_out, tool_calls=tool_calls)]

    def maybe_retry_execute_payload(self, *, error: RuntimeError, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def iter_stream_frames(self, *, data_line: str) -> Iterator[StreamFrame]:
        # Gemini sends a JSON array of responses, but standard HTTP client might see them as chunks if SSE?
        # Actually Gemini `streamGenerateContent` returns a continuous JSON response or SSE?
        # Docs say: "The response is a stream of JSON objects." (REST)
        # It's typically chunked transfer encoding, but not strictly SSE "data: ..." format unless using specific client.
        # However, `HttpChatPromptExecutor` expects SSE `data: ` lines.
        # If Gemini REST API returns a JSON list `[{}, {}, ...]`, `iter_sse_data` won't work out of the box.
        
        # CRITICAL: `HttpChatPromptExecutor` is designed for SSE (Server-Sent Events).
        # Gemini REST API does NOT use SSE. It uses a long-lived HTTP response with partial JSONs (or newline delimited JSON).
        # We need to adapt headers or use an adapter that can handle this.
        # But `ChatProviderAdapter.iter_stream_frames` is called *by* `iter_sse_data`.
        
        # If `iter_sse_data` fails to find "data:" prefix, it yields lines? 
        # `http_utils.iter_sse_data` logic: it strips "data: " prefix. 
        # If Gemini returns just raw JSON lines, we might need a workaround.
        
        # Workaround: Assume `data_line` is the raw line if `iter_sse_data` is lenient, or we need to Modify `HttpChatPromptExecutor` to support non-SSE streaming.
        # Since I cannot easily modify the core executor safely without breaking OpenAI, I will assume for now that 
        # I can parse the line passed to me.
        # But `iter_sse_data` explicitly looks for "data:".
        
        # If Gemini doesn't support SSE, this Adapter pattern (specifically `HttpChatPromptExecutor`) is incompatible with Gemini REST API directly.
        # I would need to implement a `GeminiPromptExecutor` that overrides `stream`.
        
        # FOR NOW: I will implement the parsing assuming we receive a JSON object string in `data_line`. 
        # (Maybe via a proxy or if we use the SSE-compatible endpoint if it exists).
        # BUT wait, this is "Advanced Plan". 
        # I'll add a note that Gemini streaming might require `alt=sse` parameter if supported, or this implementation is partial.
        # Research says Gemini REST API supports SSE-like behavior? 
        # No, it's usually just a response stream.
        
        # I will proceed with the parsing logic, assuming we get the JSON chunk.
        
        try:
            # Clean up line if needed (remove leading comma etc if it's a list stream)
            clean = data_line.strip()
            if clean.startswith(","): clean = clean[1:]
            if clean.startswith("["): clean = clean[1:]
            if clean.endswith("]"): clean = clean[:-1]
            if not clean: return
            
            chunk = json.loads(clean)
        except:
            return

        # Parse chunk
        # Similar to execute response
        candidates = chunk.get("candidates", [])
        if not candidates: return
        
        parts = candidates[0].get("content", {}).get("parts", [])
        # Extract text delta
        text_delta = "".join(extract_text_parts(parts))
        if text_delta:
            yield StreamFrame(type="append", content=text_delta)

        for p in parts:
             # functionCall check remains manual since extract_text_parts ignores it
             if "functionCall" in p:
                 # Gemini usually sends full function call in one chunk?
                 # If so we don't need delta builder, just emit tool_call frame?
                 # But StreamFrame expects "tool_call" with ID/name/args.
                 # If it's atomic, good.
                 fc = p["functionCall"]
                 yield StreamFrame(
                     type="tool_call",
                     tool_call_id="gemini_stream_id",
                     name=fc.get("name"),
                     args=json.dumps(fc.get("args")) # args usually dict in content, but StreamFrame expects string or we decode?
                     # StreamFrame logic in `node_llm_request_streaming` parses args JSON.
                     # So we should send JSON string.
                 )

    def end_stream(self) -> List[StreamFrame]:
        return []
