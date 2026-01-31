from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from .llm_executor import LLMExecutor, ToolChoice
from .messages import AssistantMessage, MessageBase, Prompt, SystemMessage, ToolCallMessage, UserMessage


class HistoryCompressionStrategy(ABC):
    """
    Koog-like history compression strategies.

    These are intentionally minimal: they generate a TL;DR using the same LLM executor
    (with tools disabled) and rewrite the session prompt.
    """

    @abstractmethod
    def compress(self, prompt: Prompt, llm: LLMExecutor, *, preserve_memory: bool = True) -> Prompt:
        raise AssertionError("abstract")

    @staticmethod
    def _drop_trailing_tool_calls(messages: List[MessageBase]) -> List[MessageBase]:
        out = list(messages)
        while out and isinstance(out[-1], ToolCallMessage):
            out.pop()
        return out

    @staticmethod
    def _memory_messages(messages: List[MessageBase]) -> List[MessageBase]:
        # Mirrors Koog's heuristic memory preservation.
        keep = []
        for m in messages:
            c = m.content or ""
            if "Here are the relevant facts from memory" in c or "Memory feature is not enabled" in c:
                keep.append(m)
        return keep

    @staticmethod
    def _compose_message_history(
        *,
        original: List[MessageBase],
        tldr: List[MessageBase],
        memory: List[MessageBase],
    ) -> List[MessageBase]:
        out: List[MessageBase] = []

        # Keep all system messages.
        out.extend([m for m in original if isinstance(m, SystemMessage)])

        # Keep the first user message if present.
        first_user = next((m for m in original if isinstance(m, UserMessage)), None)
        if first_user is not None:
            out.append(first_user)

        out.extend(memory)
        out.extend(tldr)

        # Preserve trailing tool calls (Koog keeps them).
        trailing_tool_calls = []
        i = len(original) - 1
        while i >= 0 and isinstance(original[i], ToolCallMessage):
            trailing_tool_calls.append(original[i])
            i -= 1
        out.extend(reversed(trailing_tool_calls))

        return out

    def _compress_prompt_into_tldr(self, prompt: Prompt, llm: LLMExecutor) -> List[MessageBase]:
        base = HistoryCompressionStrategy._drop_trailing_tool_calls(prompt.messages)
        tmp = Prompt(messages=list(base))
        tmp.append(UserMessage(text="Summarize the conversation above in TL;DR form. Keep key facts and decisions."))
        resp = llm.invoke(tmp, tool_choice=ToolChoice.NONE)
        # Use the first assistant message as TL;DR.
        first = next((m for m in resp.responses if isinstance(m, AssistantMessage)), None)
        if first is None:
            raise RuntimeError("History compression failed: LLM did not return an assistant TL;DR message.")
        return [first]


@dataclass(frozen=True)
class WholeHistory(HistoryCompressionStrategy):
    def compress(self, prompt: Prompt, llm: LLMExecutor, *, preserve_memory: bool = True) -> Prompt:
        original = list(prompt.messages)
        memory = self._memory_messages(original) if preserve_memory else []
        tldr = self._compress_prompt_into_tldr(prompt, llm)
        return Prompt(messages=self._compose_message_history(original=original, tldr=tldr, memory=memory))


@dataclass(frozen=True)
class FromLastNMessages(HistoryCompressionStrategy):
    n: int

    def compress(self, prompt: Prompt, llm: LLMExecutor, *, preserve_memory: bool = True) -> Prompt:
        original = list(prompt.messages)
        tail = original[-self.n :] if self.n > 0 else []
        tmp = Prompt(messages=list(tail))
        memory = self._memory_messages(original) if preserve_memory else []
        tldr = self._compress_prompt_into_tldr(tmp, llm)
        return Prompt(messages=self._compose_message_history(original=original, tldr=tldr, memory=memory))



