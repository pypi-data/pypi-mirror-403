from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Protocol, Sequence

from ..core.messages import Prompt, ResponseMessage
from ..core.streaming import StreamFrame
from ..core.tools import ToolDescriptor


@dataclass(frozen=True)
class PromptExecutorResult:
    """
    Koog-parity execution result: raw provider payload + parsed response messages.
    """

    raw: Any
    responses: List[ResponseMessage]


class PromptExecutor(Protocol):
    """
    Koog-parity prompt executor protocol.

    Kotlin reference: `ai.koog.prompt.executor.model.PromptExecutor`.
    This interface is intentionally provider-neutral and does not depend on LangChain.

    Implementations must return `ResponseMessage` objects (AssistantMessage/ToolCallMessage/etc).
    """

    def execute(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
    ) -> PromptExecutorResult: ...

    def stream(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
    ) -> Iterator[StreamFrame]: ...

