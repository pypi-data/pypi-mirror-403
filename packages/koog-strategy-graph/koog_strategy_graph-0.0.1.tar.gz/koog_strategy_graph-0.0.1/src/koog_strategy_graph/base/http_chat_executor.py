from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Sequence

from .http_utils import http_post_json, iter_sse_data, json_dumps_compact
from ..core.messages import Prompt
from .prompt_executor import PromptExecutor, PromptExecutorResult
from .provider_adapter import ChatProviderAdapter
from ..core.streaming import StreamFrame
from ..core.tools import ToolDescriptor


@dataclass
class HttpChatPromptExecutor(PromptExecutor):
    """
    Reusable stdlib HTTP/SSE PromptExecutor.

    This class delegates *provider-specific* schema and parsing to `adapter`,
    while centralizing:
    - JSON request posting
    - SSE reading (`iter_sse_data`)
    - "server ignored stream=true" fallback handling
    """

    adapter: ChatProviderAdapter
    timeout_s: float = 60.0

    def execute(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
    ) -> PromptExecutorResult:
        req = self.adapter.build_request(
            prompt=prompt,
            model=model,
            params=params,
            tools=tools,
            tool_choice=tool_choice,
            stream=False,
        )
        try:
            raw = http_post_json(
                url=req.url,
                headers=req.headers,
                payload=req.payload,
                timeout_s=self.timeout_s,
                error_prefix=self.adapter.error_prefix,
            )
        except RuntimeError as e:
            payload2 = self.adapter.maybe_retry_execute_payload(error=e, payload=req.payload)
            if not payload2:
                raise
            raw = http_post_json(
                url=req.url,
                headers=req.headers,
                payload=payload2,
                timeout_s=self.timeout_s,
                error_prefix=self.adapter.error_prefix,
            )
        responses = list(self.adapter.parse_execute_response(raw))
        return PromptExecutorResult(raw=raw, responses=responses)

    def stream(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
    ) -> Iterator[StreamFrame]:
        req = self.adapter.build_request(
            prompt=prompt,
            model=model,
            params=params,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
        )

        data = json_dumps_compact(req.payload).encode("utf-8")
        http_req = urllib.request.Request(url=req.url, data=data, method="POST")
        for k, v in (req.headers or {}).items():
            http_req.add_header(k, v)
        http_req.add_header("Content-Type", "application/json")
        http_req.add_header("Accept", "text/event-stream")

        saw_any_event = False
        saw_append = False
        saw_tool_call = False
        try:
            with urllib.request.urlopen(http_req, timeout=self.timeout_s) as resp:
                content_type = str(getattr(resp, "headers", {}).get("Content-Type", "") or "").lower()  # type: ignore[union-attr]

                # Some servers ignore stream=true and return a non-streaming JSON payload.
                if "text/event-stream" not in content_type:
                    body = resp.read().decode("utf-8", errors="replace")
                    try:
                        raw = json.loads(body) if body else {}
                    except Exception:
                        raw = {}
                    # Reuse execute parser to keep provider behavior consistent.
                    for r in self.adapter.parse_execute_response(raw):
                        # Only append assistant text frames here; tool calls come as ResponseMessages.
                        txt = getattr(r, "text", None)
                        if isinstance(txt, str) and txt:
                            saw_append = True
                            yield StreamFrame(type="append", content=txt, raw=raw)
                            break
                    # Always end.
                    for fr in self.adapter.end_stream():
                        yield fr
                    return

                for data_line in iter_sse_data(resp):  # type: ignore[arg-type]
                    saw_any_event = True
                    if data_line == "[DONE]":
                        break
                    for fr in self.adapter.iter_stream_frames(data_line=data_line):
                        if fr.type == "append" and (fr.content or ""):
                            saw_append = True
                        if fr.type == "tool_call":
                            saw_tool_call = True
                        yield fr

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp is not None else ""
            raise RuntimeError(f"{self.adapter.error_prefix} HTTP {e.code}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"{self.adapter.error_prefix} request failed: {e}") from e

        # If we got SSE events but no useful frames, fall back to a single non-streaming call (best-effort).
        # NOTE: tool-call-only streams are valid; do not fall back in that case.
        if saw_any_event and not saw_append and not saw_tool_call:
            res = self.execute(prompt=prompt, model=model, params=params, tools=tools, tool_choice=tool_choice)
            for r in res.responses:
                txt = getattr(r, "text", None)
                if isinstance(txt, str) and txt:
                    yield StreamFrame(type="append", content=txt, raw=res.raw)
                    break

        # Always flush at end.
        for fr in self.adapter.end_stream():
            yield fr

