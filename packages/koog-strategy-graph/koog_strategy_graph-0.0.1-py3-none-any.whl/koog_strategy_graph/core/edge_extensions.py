from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence, Type, TypeVar, cast

from .core import EdgeBuilderIntermediate, GraphContext
from .messages import AssistantMessage, ReasoningMessage, ToolCallMessage
from .tools import ReceivedToolResult, SafeTool

Incoming = TypeVar("Incoming")
T = TypeVar("T")


def on_is_instance(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    typ: Type[T],
) -> EdgeBuilderIntermediate[Incoming, T, T]:
    narrowed = intermediate.on_condition(lambda _ctx, v: isinstance(v, typ)).transformed(lambda _ctx, v: cast(T, v))
    # `transformed(...)` returns EdgeBuilderIntermediate[..., Any, Any] because the original "outgoing" type is Any.
    # We know this edge now forwards `T`.
    return cast(EdgeBuilderIntermediate[Incoming, T, T], narrowed)


def on_tool_call(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    tool_name: Optional[str] = None,
    predicate: Optional[Callable[[ToolCallMessage], bool]] = None,
) -> EdgeBuilderIntermediate[Incoming, ToolCallMessage, ToolCallMessage]:
    out = on_is_instance(intermediate, ToolCallMessage)
    if tool_name is not None:
        out = out.on_condition(lambda _ctx, tc: tc.tool == tool_name)
    if predicate is not None:
        out = out.on_condition(lambda _ctx, tc: predicate(tc))
    return out


def on_tool_not_called(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    tool_name: str,
) -> EdgeBuilderIntermediate[Incoming, ToolCallMessage, ToolCallMessage]:
    return on_tool_call(intermediate).on_condition(lambda _ctx, tc: tc.tool != tool_name)


def on_multiple_tool_calls(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    predicate: Optional[Callable[[List[ToolCallMessage]], bool]] = None,
) -> EdgeBuilderIntermediate[Incoming, List[ToolCallMessage], List[ToolCallMessage]]:
    out_any = on_is_instance(intermediate, list).transformed(
        lambda _ctx, items: [x for x in cast(Sequence[Any], items) if isinstance(x, ToolCallMessage)]
    )
    out = cast(EdgeBuilderIntermediate[Incoming, List[ToolCallMessage], List[ToolCallMessage]], out_any)
    out = out.on_condition(lambda _ctx, tcs: len(tcs) > 0)
    if predicate is not None:
        out = out.on_condition(lambda _ctx, tcs: predicate(tcs))
    return out


def on_assistant_message(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    predicate: Optional[Callable[[AssistantMessage], bool]] = None,
) -> EdgeBuilderIntermediate[Incoming, str, str]:
    # Important typing detail:
    # `EdgeBuilderIntermediate.transformed(...)` does NOT change the outgoing type; it maps the "intermediate" value
    # into the already-declared outgoing type. Therefore, we must NOT call `on_is_instance(...)` here because it
    # would lock the outgoing type to `AssistantMessage`, while this helper wants to forward `str`.
    out_any = intermediate.on_condition(lambda _ctx, v: isinstance(v, AssistantMessage)).transformed(
        lambda _ctx, v: cast(AssistantMessage, v).content
    )
    out = cast(EdgeBuilderIntermediate[Incoming, str, str], out_any)
    if predicate is not None:
        out = out.on_condition(lambda _ctx, s: predicate(AssistantMessage(text=s)))
    return out


def on_reasoning_message(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    predicate: Optional[Callable[[ReasoningMessage], bool]] = None,
) -> EdgeBuilderIntermediate[Incoming, ReasoningMessage, ReasoningMessage]:
    out = on_is_instance(intermediate, ReasoningMessage)
    if predicate is not None:
        out = out.on_condition(lambda _ctx, m: predicate(m))
    return out


def on_tool_result(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    tool_name: Optional[str] = None,
    predicate: Optional[Callable[[ReceivedToolResult], bool]] = None,
) -> EdgeBuilderIntermediate[Incoming, ReceivedToolResult, ReceivedToolResult]:
    out = on_is_instance(intermediate, ReceivedToolResult)
    if tool_name is not None:
        out = out.on_condition(lambda _ctx, tr: tr.tool == tool_name)
    if predicate is not None:
        out = out.on_condition(lambda _ctx, tr: predicate(tr))
    return out


def on_successful_tool_result(
    intermediate: EdgeBuilderIntermediate[Incoming, Any, Any],
    *,
    predicate: Optional[Callable[[Any], bool]] = None,
) -> EdgeBuilderIntermediate[Incoming, ReceivedToolResult, ReceivedToolResult]:
    out = on_tool_result(intermediate)

    def _is_success(_ctx: GraphContext, tr: ReceivedToolResult) -> bool:
        return isinstance(tr.safe_result, SafeTool.Success)

    out = out.on_condition(_is_success)
    if predicate is not None:
        out = out.on_condition(lambda _ctx, tr: predicate(cast(SafeTool.Success[Any], tr.safe_result).result))
    return out


