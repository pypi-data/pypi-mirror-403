from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class AgentExecutionInfo:
    """
    Koog-like execution context chain.

    In Kotlin Koog, this is used to track nested execution contexts within a run.
    Here we derive it from the current execution path (strategy/subgraph/node stack).
    """

    part_name: str
    parent: Optional["AgentExecutionInfo"] = None


def execution_info_from_path(path: str) -> AgentExecutionInfo:
    parts = [p for p in (path or "").split("/") if p]
    if not parts:
        return AgentExecutionInfo(part_name="root", parent=None)
    cur: Optional[AgentExecutionInfo] = None
    for p in parts:
        cur = AgentExecutionInfo(part_name=str(p), parent=cur)
    # cur is not None here
    return cur  # type: ignore[return-value]


# -----------------
# Agent lifecycle
# -----------------


@dataclass(frozen=True)
class AgentStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    agent_id: str
    run_id: str


@dataclass(frozen=True)
class AgentCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    agent_id: str
    run_id: str
    result: Any


@dataclass(frozen=True)
class AgentExecutionFailedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    agent_id: str
    run_id: str
    error: Exception


@dataclass(frozen=True)
class AgentClosingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    agent_id: str


# ---------
# Strategy
# ---------


@dataclass(frozen=True)
class StrategyStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    strategy_name: str
    graph: Any = None


@dataclass(frozen=True)
class StrategyCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    strategy_name: str
    result: Any


# -----
# Node
# -----


@dataclass(frozen=True)
class NodeExecutionStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    node_name: str
    node_path: str
    input_value: Any


@dataclass(frozen=True)
class NodeExecutionCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    node_name: str
    node_path: str
    input_value: Any
    output_value: Any
    is_technical: bool


@dataclass(frozen=True)
class NodeExecutionFailedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    node_name: str
    node_path: str
    input_value: Any
    error: Exception
    is_technical: bool


# --------
# Subgraph
# --------


@dataclass(frozen=True)
class SubgraphExecutionStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    subgraph_name: str
    input_value: Any


@dataclass(frozen=True)
class SubgraphExecutionCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    subgraph_name: str
    input_value: Any
    output_value: Any


@dataclass(frozen=True)
class SubgraphExecutionFailedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    subgraph_name: str
    input_value: Any
    error: Exception


# --------
# LLM call
# --------


@dataclass(frozen=True)
class LLMCallStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    prompt: Any
    model: Any
    tools: Sequence[str]
    tool_choice: Any
    params: Any


@dataclass(frozen=True)
class LLMCallCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    prompt: Any
    model: Any
    response: Any


# --------------
# LLM streaming
# --------------


@dataclass(frozen=True)
class LLMStreamingStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    model: Any
    prompt: Any
    tools: Sequence[str]


@dataclass(frozen=True)
class LLMStreamingFrameReceivedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    frame: Any


@dataclass(frozen=True)
class LLMStreamingFailedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    error: Exception


@dataclass(frozen=True)
class LLMStreamingCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str


# --------------
# Tool execution
# --------------


@dataclass(frozen=True)
class ToolCallStartingContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    tool_call_id: Optional[str]
    tool_name: str
    tool_args: Any


@dataclass(frozen=True)
class ToolValidationFailedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    tool_call_id: Optional[str]
    tool_name: str
    tool_args: Any
    error: Exception


@dataclass(frozen=True)
class ToolCallFailedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    tool_call_id: Optional[str]
    tool_name: str
    tool_args: Any
    error: Exception


@dataclass(frozen=True)
class ToolCallCompletedContext:
    event_id: str
    execution_info: AgentExecutionInfo
    run_id: str
    tool_call_id: Optional[str]
    tool_name: str
    tool_args: Any
    ok: bool
    result: Any

