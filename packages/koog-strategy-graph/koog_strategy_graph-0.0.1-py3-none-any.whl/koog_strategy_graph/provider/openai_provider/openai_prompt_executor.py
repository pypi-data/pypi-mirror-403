from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Sequence

from ...base.http_chat_executor import HttpChatPromptExecutor
from .openai_adapter import OpenAIChatCompletionsAdapter
from ...base.prompt_executor import PromptExecutor, PromptExecutorResult
from ...core.messages import Prompt
from ...core.streaming import StreamFrame
from ...core.tools import ToolDescriptor


@dataclass
class OpenAIPromptExecutor(PromptExecutor):
    """
    OpenAI Chat Completions-backed PromptExecutor (online).

    - Uses stdlib HTTP (no extra deps).
    - Provider-neutral core remains LangChain-free; this is an optional adapter.
    """

    api_key: str
    base_url: str = "https://api.openai.com"
    timeout_s: float = 60.0
    # For tests/diagnostics: records {model, params, tools, tool_choice} per call.
    traces: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "OpenAIPromptExecutor":
        key = os.getenv("OPENAI_API_KEY") or ""
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        base_url = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com"
        return cls(api_key=key, base_url=base_url)

    def execute(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
    ) -> PromptExecutorResult:
        adapter = OpenAIChatCompletionsAdapter(api_key=self.api_key, base_url=self.base_url, traces=self.traces)
        http_exec = HttpChatPromptExecutor(adapter=adapter, timeout_s=self.timeout_s)
        return http_exec.execute(prompt=prompt, model=model, params=params, tools=tools, tool_choice=tool_choice)

    def stream(
        self,
        *,
        prompt: Prompt,
        model: Any,
        params: Dict[str, Any],
        tools: Sequence[ToolDescriptor],
        tool_choice: Optional[str],
    ) -> Iterator[StreamFrame]:
        adapter = OpenAIChatCompletionsAdapter(api_key=self.api_key, base_url=self.base_url, traces=self.traces)
        http_exec = HttpChatPromptExecutor(adapter=adapter, timeout_s=self.timeout_s)
        yield from http_exec.stream(prompt=prompt, model=model, params=params, tools=tools, tool_choice=tool_choice)

