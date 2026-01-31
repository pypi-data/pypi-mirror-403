from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, Sequence

from .history import HistoryCompressionStrategy, WholeHistory
from .llm_executor import AgentSession, LLMExecutor, ToolChoice
from .messages import AssistantMessage, ToolCallMessage, UserMessage
from .tools import Tool, ToolDescriptor


class StructureFixingParser(Protocol):
    """
    Koog-like "fixing parser" surface.

    Kotlin Koog can optionally attempt to fix malformed structured responses.
    In Python parity, this is intentionally minimal: implementors can attempt to
    recover a list of tool names from the LLM raw response or assistant text.
    """

    def parse_selected_tools(
        self,
        *,
        allowed_tool_names: Sequence[str],
        tool_call: Optional[ToolCallMessage],
        assistant_text: Optional[str],
        raw: Any,
    ) -> Optional[List[str]]: ...


class ToolSelectionStrategy:
    """
    Sealed-like base for Koog tool selection strategies.
    """


@dataclass(frozen=True)
class ALL(ToolSelectionStrategy):
    pass


@dataclass(frozen=True)
class NONE(ToolSelectionStrategy):
    pass


@dataclass(frozen=True)
class Tools(ToolSelectionStrategy):
    tools: List[ToolDescriptor]


@dataclass(frozen=True)
class AutoSelectForTask(ToolSelectionStrategy):
    subtask_description: str
    fixing_parser: Optional[StructureFixingParser] = None
    history_compression: HistoryCompressionStrategy = WholeHistory()


def tools_to_descriptors(tools: Sequence[Tool[Any, Any]]) -> List[ToolDescriptor]:
    return [t.descriptor for t in tools]


def _select_relevant_tools_prompt(*, tools: Sequence[ToolDescriptor], subtask_description: str) -> str:
    """
    Mirrors Koog's `Prompts.selectRelevantTools` prompt content.
    """
    lines: List[str] = []
    lines.append("You will be now concentrating on solving the following task:")
    lines.append("")
    lines.append("## TASK DESCRIPTION")
    lines.append("")
    lines.append(str(subtask_description or "").strip())
    lines.append("")
    lines.append("## AVAILABLE TOOLS")
    lines.append("")
    lines.append("You have the following tools available:")
    for t in tools:
        lines.append(f"- Name: {t.name}\n  Description: {t.description}")
    lines.append("")
    lines.append("Please, provide a list of the tools ONLY RELEVANT FOR THE GIVEN TASK, separated by commas.")
    lines.append("Think carefully about the tools you select, and make sure they are relevant to the task.")
    return "\n".join(lines).strip()


def select_tools_for_strategy(
    *,
    strategy: ToolSelectionStrategy,
    all_tools: Sequence[ToolDescriptor],
    session: AgentSession,
    llm: LLMExecutor,
) -> List[ToolDescriptor]:
    """
    Koog-parity tool selection:
    - ALL: all tools
    - NONE: none
    - Tools: explicit subset
    - AutoSelectForTask: LLM-driven selection using a temporary TL;DR history
    """
    if isinstance(strategy, ALL):
        return list(all_tools)
    if isinstance(strategy, NONE):
        return []
    if isinstance(strategy, Tools):
        return list(strategy.tools)
    if not isinstance(strategy, AutoSelectForTask):
        raise TypeError(f"Unknown ToolSelectionStrategy: {type(strategy)!r}")

    allowed = [t.name for t in all_tools if t.name]
    if not allowed:
        return []

    # Temporarily compress history to TL;DR, then ask for relevant tools in structured form.
    initial_prompt = session.prompt
    try:
        # Koog uses `replaceHistoryWithTLDR()`; Python parity uses the same executor (tools disabled).
        session.prompt = strategy.history_compression.compress(initial_prompt, llm, preserve_memory=True)

        session.prompt.append(UserMessage(text=_select_relevant_tools_prompt(tools=all_tools, subtask_description=strategy.subtask_description)))

        selector_tool_name = "__koog_selected_tools__"
        selector_tool = ToolDescriptor(
            name=selector_tool_name,
            description="Return the selected tool names relevant for the task.",
            input_schema={
                "type": "object",
                "properties": {"tools": {"type": "array", "items": {"type": "string"}}},
                "required": ["tools"],
                "additionalProperties": False,
            },
        )

        resp = llm.invoke(session.prompt, tools=[selector_tool], tool_choice=ToolChoice.named(selector_tool_name))

        tool_call = next((m for m in resp.responses if isinstance(m, ToolCallMessage) and m.tool == selector_tool_name), None)
        assistant = next((m for m in resp.responses if isinstance(m, AssistantMessage)), None)
        assistant_text = assistant.text if assistant is not None else None

        selected_names: List[str] = []
        if tool_call is not None and isinstance(tool_call.args, dict):
            raw_list = tool_call.args.get("tools")
            if isinstance(raw_list, list):
                selected_names = [str(x) for x in raw_list if isinstance(x, (str, int, float)) and str(x).strip()]

        if not selected_names and assistant_text:
            # Fallback: parse comma-separated list (Koog prompt asks for comma-separated list).
            selected_names = [p.strip() for p in assistant_text.split(",") if p.strip()]

        if not selected_names and strategy.fixing_parser is not None:
            fixed = strategy.fixing_parser.parse_selected_tools(
                allowed_tool_names=allowed,
                tool_call=tool_call,
                assistant_text=assistant_text,
                raw=resp.raw,
            )
            if fixed:
                selected_names = list(fixed)

        selected_set = {n for n in selected_names if n in set(allowed)}
        return [t for t in all_tools if t.name in selected_set]
    finally:
        # Restore original prompt history (Koog restores `initialPrompt` after selection).
        session.prompt = initial_prompt


_KOOG_ALLOWED_TOOLS_KEY = "__koog_allowed_tool_names__"


def set_allowed_tool_names(ctx: Any, names: Optional[Sequence[str]]) -> Optional[Sequence[str]]:
    """
    Store/restore the allowed tool set in GraphContext storage.
    Returns the previous value for restoration.
    """
    prev = None
    try:
        prev = ctx.get(_KOOG_ALLOWED_TOOLS_KEY, None)
    except Exception:
        prev = None
    if names is None:
        try:
            ctx.remove(_KOOG_ALLOWED_TOOLS_KEY)
        except Exception:
            pass
        return prev

    try:
        ctx.store(_KOOG_ALLOWED_TOOLS_KEY, list(names))
    except Exception:
        pass
    return prev


def is_tool_allowed(ctx: Any, tool_name: str) -> bool:
    try:
        allowed = ctx.get(_KOOG_ALLOWED_TOOLS_KEY, None)
    except Exception:
        allowed = None
    if allowed is None:
        return True
    if isinstance(allowed, list):
        return tool_name in set(str(x) for x in allowed)
    return True

