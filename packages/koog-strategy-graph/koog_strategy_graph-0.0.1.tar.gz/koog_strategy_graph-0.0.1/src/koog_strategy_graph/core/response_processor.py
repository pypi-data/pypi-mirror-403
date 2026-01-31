from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Protocol, Sequence

from .messages import Prompt, ResponseMessage


class ResponseProcessor(Protocol):
    """
    Koog-parity response processor surface.

    Kotlin reference: `ai.koog.prompt.processor.ResponseProcessor.process(...)`.
    In Python parity we keep the same conceptual inputs but stay synchronous.
    """

    def process(
        self,
        *,
        executor: Any,
        prompt: Prompt,
        model: Any,
        tools: Sequence[Any],
        responses: List[ResponseMessage],
    ) -> List[ResponseMessage]: ...


@dataclass(frozen=True)
class Chain(ResponseProcessor):
    """
    Chain multiple processors together, in order (Koog `ResponseProcessor.Chain` parity).
    """

    processors: Sequence[ResponseProcessor]

    def process(
        self,
        *,
        executor: Any,
        prompt: Prompt,
        model: Any,
        tools: Sequence[Any],
        responses: List[ResponseMessage],
    ) -> List[ResponseMessage]:
        out = list(responses)
        for p in self.processors:
            out = list(p.process(executor=executor, prompt=prompt, model=model, tools=tools, responses=out))
        return out

