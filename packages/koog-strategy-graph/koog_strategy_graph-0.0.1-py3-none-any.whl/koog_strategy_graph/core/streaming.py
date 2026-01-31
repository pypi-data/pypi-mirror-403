from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class StreamFrame:
    """
    Koog-like streaming frame model.

    Kotlin reference (docs): Append / ToolCall / End.
    We keep a single dataclass with optional fields to avoid breaking existing call sites.
    """

    # "append" | "tool_call" | "end" (we also accept legacy "text_delta")
    type: str
    # For append/text delta frames: the text content
    content: str = ""
    # Tool call frames
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    # End frames
    finish_reason: Optional[str] = None
    raw: Any = None


class StreamFrameFlowBuilder:
    """
    Provider-agnostic helper to build Koog-like streaming frames safely.

    Motivation (Kotlin parity):
    - Koog buffers partial tool-call argument deltas and only emits a completed ToolCall frame.
    - Koog flushes any pending tool call *before* emitting text or end.

    Python executors can use this helper to implement the same invariants without
    duplicating buffering logic per provider.
    """

    def __init__(self):
        # OpenAI-style tool call streaming is indexed and can contain *multiple* tool calls
        # within a single assistant turn (parallel tool calls).
        #
        # We buffer deltas keyed by index and only emit ToolCall frames when it's safe:
        # - before any text append
        # - at end
        # - when the provider indicates tool calls are complete (e.g., finish_reason == "tool_calls")
        self._pending_by_index: Dict[int, Dict[str, Any]] = {}

    def try_emit_pending_tool_calls(self, *, raw: Any = None) -> list[StreamFrame]:
        if not self._pending_by_index:
            return []
        out: list[StreamFrame] = []
        for idx in sorted(self._pending_by_index.keys()):
            p = self._pending_by_index[idx] or {}
            out.append(
                StreamFrame(
                    type="tool_call",
                    tool_call_id=p.get("id"),
                    tool_name=str(p.get("name") or ""),
                    # Keep parity with earlier OpenAI behavior: allow empty string.
                    tool_args=str(p.get("args") or ""),
                    raw=raw,
                )
            )
        self._pending_by_index.clear()
        return out

    # Backwards-compat helper (single-frame); prefer try_emit_pending_tool_calls.
    def try_emit_pending_tool_call(self, *, raw: Any = None) -> Optional[StreamFrame]:
        frames = self.try_emit_pending_tool_calls(raw=raw)
        if not frames:
            return None
        return frames[0]

    def emit_append(self, text: str, *, raw: Any = None) -> list[StreamFrame]:
        out = self.try_emit_pending_tool_calls(raw=raw)
        out.append(StreamFrame(type="append", content=text, raw=raw))
        return out

    def emit_end(self, *, finish_reason: Optional[str] = None, raw: Any = None) -> list[StreamFrame]:
        out = self.try_emit_pending_tool_calls(raw=raw)
        out.append(StreamFrame(type="end", finish_reason=finish_reason, raw=raw))
        return out

    def upsert_tool_call(
        self,
        *,
        index: int,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        args_delta: Optional[str] = None,
    ) -> Optional[StreamFrame]:
        """
        Update (or start) a pending tool call by streaming delta.

        Rules (Koog parity):
        - Buffer deltas keyed by `index`.
        - Do not emit frames here; emission happens via `emit_append`, `emit_end`,
          or `try_emit_pending_tool_calls`.
        """
        idx = int(index)
        entry = self._pending_by_index.setdefault(idx, {"id": None, "name": None, "args": ""})
        if tool_call_id is not None and not entry.get("id"):
            entry["id"] = tool_call_id
        if tool_name and not entry.get("name"):
            entry["name"] = tool_name
        if args_delta:
            entry["args"] = str(entry.get("args") or "") + str(args_delta)
        self._pending_by_index[idx] = entry
        return None

