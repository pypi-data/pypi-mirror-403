from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MetaInfo:
    timestamp: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class MessageBase(ABC):
    meta: MetaInfo = field(default_factory=MetaInfo)

    @property
    @abstractmethod
    def role(self) -> str:
        raise AssertionError("abstract")

    @property
    @abstractmethod
    def content(self) -> str:
        raise AssertionError("abstract")


@dataclass(frozen=True)
class SystemMessage(MessageBase):
    text: str = ""

    @property
    def role(self) -> str:
        return "system"

    @property
    def content(self) -> str:
        return self.text


@dataclass(frozen=True)
class UserMessage(MessageBase):
    text: str = ""

    @property
    def role(self) -> str:
        return "user"

    @property
    def content(self) -> str:
        return self.text


@dataclass(frozen=True)
class AssistantMessage(MessageBase):
    text: str = ""

    @property
    def role(self) -> str:
        return "assistant"

    @property
    def content(self) -> str:
        return self.text


@dataclass(frozen=True)
class ReasoningMessage(MessageBase):
    text: str = ""

    @property
    def role(self) -> str:
        return "reasoning"

    @property
    def content(self) -> str:
        return self.text


@dataclass(frozen=True)
class ToolCallMessage(MessageBase):
    tool: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    tool_call_id: Optional[str] = None

    @property
    def role(self) -> str:
        return "tool_call"

    @property
    def content(self) -> str:
        # Deterministic string representation for persistence/logging.
        return json.dumps(
            {"tool": self.tool, "args": self.args, "tool_call_id": self.tool_call_id},
            sort_keys=True,
            ensure_ascii=False,
        )


@dataclass(frozen=True)
class ToolResultMessage(MessageBase):
    tool: str = ""
    result: Any = None
    tool_call_id: Optional[str] = None

    @property
    def role(self) -> str:
        return "tool"

    @property
    def content(self) -> str:
        return str(self.result)


ResponseMessage = Union[AssistantMessage, ToolCallMessage, ReasoningMessage]


@dataclass
class Prompt:
    """
    Koog-like prompt container (message history + params kept elsewhere).
    """

    messages: List[MessageBase] = field(default_factory=list)

    def with_messages(self, messages: Sequence[MessageBase]) -> "Prompt":
        return Prompt(messages=list(messages))

    def append(self, *msgs: MessageBase) -> None:
        self.messages.extend(msgs)

    def to_serializable(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for m in self.messages:
            base: Dict[str, Any] = {
                "role": m.role,
                "content": m.content,
                "timestamp": m.meta.timestamp.isoformat(),
            }
            if isinstance(m, ToolCallMessage):
                base.update({"tool": m.tool, "args": m.args, "tool_call_id": m.tool_call_id})
            if isinstance(m, ToolResultMessage):
                base.update({"tool": m.tool, "tool_call_id": m.tool_call_id, "result": m.result})
            out.append(base)
        return out

    @staticmethod
    def from_serializable(items: List[Dict[str, Any]]) -> "Prompt":
        msgs: List[MessageBase] = []
        for it in items:
            ts = it.get("timestamp")
            meta = MetaInfo(timestamp=datetime.fromisoformat(ts)) if ts else MetaInfo()
            role = it.get("role")
            content = it.get("content", "") or ""
            if role == "system":
                msgs.append(SystemMessage(text=content, meta=meta))
            elif role == "user":
                msgs.append(UserMessage(text=content, meta=meta))
            elif role == "assistant":
                msgs.append(AssistantMessage(text=content, meta=meta))
            elif role == "tool_call":
                msgs.append(
                    ToolCallMessage(
                        tool=str(it.get("tool") or ""),
                        args=dict(it.get("args") or {}),
                        tool_call_id=it.get("tool_call_id"),
                        meta=meta,
                    )
                )
            elif role == "tool":
                msgs.append(
                    ToolResultMessage(
                        tool=str(it.get("tool") or ""),
                        result=it.get("result"),
                        tool_call_id=it.get("tool_call_id"),
                        meta=meta,
                    )
                )
            elif role == "reasoning":
                msgs.append(ReasoningMessage(text=content, meta=meta))
            else:
                raise ValueError(f"Unknown serialized message role: {role!r}")
        return Prompt(messages=msgs)


