from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Protocol, Sequence

from ..core.messages import Prompt, ResponseMessage
from ..core.streaming import StreamFrame
from ..core.tools import ToolDescriptor


@dataclass(frozen=True)
class ProviderRequest:
    """
    A provider request descriptor for a single prompt execution.

    This is intentionally small: it lets a reusable HTTP executor post the payload
    and lets each provider adapter control only what must be provider-specific.
    """

    url: str
    headers: Dict[str, str]
    payload: Dict[str, Any]
    # Whether the caller should request SSE (`Accept: text/event-stream`) and treat
    # the response as a stream (if the server honors it).
    stream: bool = False


class ChatProviderAdapter(Protocol):
    """
    Provider adapter for chat-style LLM APIs.

    Goal: new providers should implement this adapter and reuse the shared HTTP/SSE
    and StreamFrame-building utilities in the core.
    """

    error_prefix: str

    def build_request(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
        stream: bool,
    ) -> ProviderRequest: ...

    def parse_execute_response(self, raw: Dict[str, Any]) -> list[ResponseMessage]: ...

    def maybe_retry_execute_payload(self, *, error: RuntimeError, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Optional provider hook: if the first execute call fails, return an adjusted payload to retry once.

        Use cases:
        - Some endpoints reject newer/optional params (e.g., OpenAI gateways that don't accept GPT-5 params)
        """

        ...

    def iter_stream_frames(self, *, data_line: str) -> Iterator[StreamFrame]:
        """
        Convert a single SSE `data:` line into zero or more `StreamFrame`s.

        The shared HTTP layer yields `data_line` as a decoded UTF-8 string.
        Implementations should:
        - ignore non-JSON lines (except for "[DONE]" which should yield nothing)
        - coalesce tool-call deltas using `StreamFrameFlowBuilder` (recommended)
        - emit `StreamFrame(type="append", ...)` and `StreamFrame(type="tool_call", ...)`
        """

        ...

    def end_stream(self) -> list[StreamFrame]:
        """
        Called once at the end of streaming to flush any buffered frames.
        Implementations should typically emit an `end` frame (and flush pending tool calls).
        """

        ...

