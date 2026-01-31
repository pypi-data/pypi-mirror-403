from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Sequence

from ...base.http_utils import json_dumps_compact
from ...base.provider_adapter import ProviderRequest, ChatProviderAdapter
from ...core.messages import (
    AssistantMessage,
    Prompt,
    ReasoningMessage,
    ResponseMessage,
    SystemMessage,
    ToolCallMessage,
    ToolResultMessage,
    UserMessage,
)
from ...base.stream_text import extract_text_parts
from ...core.streaming import StreamFrame, StreamFrameFlowBuilder
from ...core.tools import ToolDescriptor


def _openai_tool_spec(tool: ToolDescriptor) -> Dict[str, Any]:
    params = tool.input_schema if isinstance(tool.input_schema, dict) else None
    # OpenAI expects a JSON schema-like "parameters" object. If missing, use an empty object schema.
    if not params:
        params = {"type": "object", "properties": {}, "additionalProperties": True}
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": params,
        },
    }


def _openai_tool_choice(tool_choice: Optional[str]) -> Optional[Any]:
    """
    Map Koog-style ToolChoice strings into OpenAI chat.completions tool_choice.
    - None -> omit (provider default)
    - "none"/"auto"/"required" -> pass-through
    - "<tool_name>" -> force a specific function tool
    """
    if tool_choice is None:
        return None
    if tool_choice in ("none", "auto", "required"):
        return tool_choice
    # Named tool.
    return {"type": "function", "function": {"name": str(tool_choice)}}


def _is_gpt5_model(name: str) -> bool:
    return (name or "").strip().lower().startswith("gpt-5")


def _forbid_4o_models(name: str) -> None:
    # User requirement: never use 4o models.
    n = (name or "").strip().lower()
    if "gpt-4o" in n or n.endswith("4o") or "4o-mini" in n or "4o" == n:
        raise RuntimeError(f"4o models are not allowed. Got model={name!r}")


def _normalize_openai_params(*, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Koog-like param aliases into OpenAI request params.
    """
    p: Dict[str, Any] = dict(params or {})
    aliases = {
        "maxTokens": "max_tokens",
        "topP": "top_p",
        "frequencyPenalty": "frequency_penalty",
        "presencePenalty": "presence_penalty",
        "stopSequences": "stop",
        "randomSeed": "seed",
        "safetyIdentifier": "user",
        "parallelToolCalls": "parallel_tool_calls",
    }
    for src, dst in aliases.items():
        if src in p and dst not in p:
            p[dst] = p.pop(src)

    if _is_gpt5_model(model):
        if "temperature" in p and p["temperature"] not in (None, 1, 1.0):
            raise ValueError(
                "GPT-5 does not support temperature != default. Remove 'temperature' and use reasoning/verbosity controls instead."
            )
        p.pop("temperature", None)

        if "top_p" in p and p["top_p"] not in (None, 1, 1.0):
            raise ValueError("GPT-5 does not support top_p != default. Remove 'top_p'.")
        p.pop("top_p", None)

        if "max_tokens" in p and "max_completion_tokens" not in p:
            p["max_completion_tokens"] = p.pop("max_tokens")
        p.pop("max_tokens", None)

        if "reasoningEffort" in p and "reasoning_effort" not in p:
            p["reasoning_effort"] = p.pop("reasoningEffort")

    else:
        if "max_completion_tokens" in p and "max_tokens" not in p:
            p["max_tokens"] = p.pop("max_completion_tokens")
        p.pop("max_completion_tokens", None)
        p.pop("reasoning_effort", None)
        p.pop("reasoning", None)
        p.pop("text", None)

    return p


def _prompt_to_openai_messages(prompt: Prompt) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in prompt.messages:
        if isinstance(m, SystemMessage):
            out.append({"role": "system", "content": m.text})
        elif isinstance(m, UserMessage):
            out.append({"role": "user", "content": m.text})
        elif isinstance(m, AssistantMessage):
            out.append({"role": "assistant", "content": m.text})
        elif isinstance(m, ReasoningMessage):
            out.append({"role": "assistant", "content": m.text})
        elif isinstance(m, ToolCallMessage):
            args_str = json_dumps_compact(m.args if isinstance(m.args, dict) else {})
            tc = {
                "id": m.tool_call_id or "call_1",
                "type": "function",
                "function": {"name": m.tool, "arguments": args_str},
            }
            out.append({"role": "assistant", "content": "", "tool_calls": [tc]})
        elif isinstance(m, ToolResultMessage):
            out.append({"role": "tool", "tool_call_id": m.tool_call_id or "call_1", "content": str(m.result)})
        else:
            raise TypeError(f"Unsupported message type: {type(m)!r}")
    return out


def _parse_openai_chat_completions(raw: Dict[str, Any]) -> List[ResponseMessage]:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"OpenAI response missing choices: {raw!r}")
    msg = (choices[0] or {}).get("message") or {}

    def _extract_assistant_text(m: Dict[str, Any]) -> str:
        """
        OpenAI Chat Completions typically returns `message.content` as a string, but in some
        scenarios it may be null and instead provide a `message.refusal` string.
        We normalize those cases into a best-effort assistant text.
        """
        content2 = m.get("content")
        if isinstance(content2, str):
            return content2
        if content2 is None:
            refusal = m.get("refusal")
            if isinstance(refusal, str) and refusal.strip():
                return refusal
            return ""
        # Defensive: if a proxy returns a structured content shape.
        if isinstance(content2, list):
            # Reuse provider-agnostic extractor (handles {"text":{"value":"..."}} and common part shapes).
            txt = "".join(extract_text_parts(content2))
            if txt.strip():
                return txt
            # Some variants may encode refusal as a typed part.
            for p in content2:
                if isinstance(p, dict):
                    r = p.get("refusal")
                    if isinstance(r, str) and r.strip():
                        return r
            return ""
        return str(content2)

    assistant_text = _extract_assistant_text(msg)

    tool_calls = msg.get("tool_calls") or []
    responses: List[ResponseMessage] = []

    if tool_calls and isinstance(tool_calls, list):
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function") or {}
            if not isinstance(fn, dict):
                continue
            name = fn.get("name")
            args_raw = fn.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else {}
            except Exception:
                args = {}
            responses.append(ToolCallMessage(tool=str(name or ""), args=dict(args) if isinstance(args, dict) else {}, tool_call_id=tc.get("id")))

        if assistant_text.strip():
            responses.append(AssistantMessage(text=assistant_text))
        return responses

    responses.append(AssistantMessage(text=assistant_text))
    return responses


@dataclass
class OpenAIChatCompletionsAdapter(ChatProviderAdapter):
    api_key: str
    base_url: str = "https://api.openai.com"
    error_prefix: str = "OpenAI"
    # For tests/diagnostics: records {model, params, tools, tool_choice} per call.
    traces: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise RuntimeError("OpenAIChatCompletionsAdapter requires a non-empty api_key")

        # Streaming parser state.
        self._sfb = StreamFrameFlowBuilder()
        self._saw_append = False
        self._saw_tool_call = False
        self._saw_any_event = False
        self._last_finish_reason: Optional[str] = None

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
        openai_model = str(model or os.getenv("OPENAI_MODEL") or "gpt-5-mini")
        _forbid_4o_models(openai_model)
        effective_params = _normalize_openai_params(model=openai_model, params=params)

        payload: Dict[str, Any] = {"model": openai_model, "messages": _prompt_to_openai_messages(prompt)}
        if stream:
            payload["stream"] = True
        if effective_params:
            payload.update(dict(effective_params))

        tool_specs = [_openai_tool_spec(t) for t in tools if t.name]
        if tool_specs:
            payload["tools"] = tool_specs
            tc = _openai_tool_choice(tool_choice)
            if tc is not None:
                payload["tool_choice"] = tc
            payload.setdefault("parallel_tool_calls", True)

        self.traces.append(
            {
                "model": openai_model,
                "params": dict(effective_params),
                "tools": [t.name for t in tools],
                "tool_choice": tool_choice,
                "stream": stream,
            }
        )

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return ProviderRequest(url=url, headers=headers, payload=payload, stream=stream)

    def parse_execute_response(self, raw: Dict[str, Any]) -> list[ResponseMessage]:
        return list(_parse_openai_chat_completions(raw))

    def maybe_retry_execute_payload(self, *, error: RuntimeError, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Some model/endpoints reject newer/alternate params. Retry once, stripping known offenders.
        msg = str(error)
        retry_keys: List[str] = []
        if "Unknown parameter: 'text'" in msg:
            retry_keys.append("text")
        if "Unknown parameter: 'verbosity'" in msg:
            retry_keys.append("verbosity")
        if "Unknown parameter: 'reasoning_effort'" in msg:
            retry_keys.append("reasoning_effort")
        if "Unknown parameter: 'reasoning'" in msg:
            retry_keys.append("reasoning")
        if not retry_keys:
            return None
        payload2 = dict(payload)
        for k in retry_keys:
            payload2.pop(k, None)
        return payload2

    def iter_stream_frames(self, *, data_line: str) -> Iterator[StreamFrame]:
        if data_line == "[DONE]":
            return
            yield  # pragma: no cover

        try:
            chunk = json.loads(data_line)
        except Exception:
            return
            yield  # pragma: no cover

        self._saw_any_event = True

        # Responses-API-like events (some gateways proxy these even for chat.completions).
        t = chunk.get("type")
        if isinstance(t, str):
            if t.endswith(".delta") and isinstance(chunk.get("delta"), str):
                delta_txt = chunk.get("delta") or ""
                if delta_txt:
                    for fr in self._sfb.emit_append(delta_txt, raw=chunk):
                        if fr.type == "append":
                            self._saw_append = True
                        elif fr.type == "tool_call":
                            self._saw_tool_call = True
                        yield fr
                return
            if t.endswith(".done") and isinstance(chunk.get("text"), str):
                done_txt = chunk.get("text") or ""
                if done_txt:
                    for fr in self._sfb.emit_append(done_txt, raw=chunk):
                        if fr.type == "append":
                            self._saw_append = True
                        elif fr.type == "tool_call":
                            self._saw_tool_call = True
                        yield fr
                return
            if t == "response.completed":
                self._last_finish_reason = "stop"
                return

        choices = chunk.get("choices") or []
        if not isinstance(choices, list) or not choices:
            return
        c0 = choices[0] or {}
        delta = c0.get("delta") or c0.get("message") or {}
        finish_reason = c0.get("finish_reason")
        if isinstance(finish_reason, str):
            self._last_finish_reason = finish_reason

        if isinstance(delta, dict):
            dtext = delta.get("text")
            for txt in extract_text_parts(delta.get("content")):
                if txt:
                    for fr in self._sfb.emit_append(txt, raw=chunk):
                        if fr.type == "append":
                            self._saw_append = True
                        elif fr.type == "tool_call":
                            self._saw_tool_call = True
                        yield fr
            if isinstance(dtext, str) and dtext:
                for fr in self._sfb.emit_append(dtext, raw=chunk):
                    if fr.type == "append":
                        self._saw_append = True
                    elif fr.type == "tool_call":
                        self._saw_tool_call = True
                    yield fr

            dtc = delta.get("tool_calls") or []
            if isinstance(dtc, list):
                for it in dtc:
                    if not isinstance(it, dict):
                        continue
                    idx = it.get("index")
                    if not isinstance(idx, int):
                        continue
                    fn = it.get("function") or {}
                    tool_name: Optional[str] = None
                    args_part: Optional[str] = None
                    if isinstance(fn, dict):
                        if isinstance(fn.get("name"), str):
                            tool_name = fn.get("name")
                        if isinstance(fn.get("arguments"), str):
                            args_part = fn.get("arguments")
                    self._sfb.upsert_tool_call(
                        index=idx,
                        tool_call_id=it.get("id") if isinstance(it.get("id"), str) else None,
                        tool_name=tool_name,
                        args_delta=args_part,
                    )

        if finish_reason == "tool_calls":
            for fr in self._sfb.try_emit_pending_tool_calls(raw=chunk):
                self._saw_tool_call = True
                yield fr

        if finish_reason is not None:
            for fr in self._sfb.try_emit_pending_tool_calls(raw=chunk):
                self._saw_tool_call = True
                yield fr

    def end_stream(self) -> list[StreamFrame]:
        out: list[StreamFrame] = []
        out.extend(self._sfb.try_emit_pending_tool_calls(raw=None))
        out.append(StreamFrame(type="end", finish_reason=self._last_finish_reason, raw=None))
        return out

