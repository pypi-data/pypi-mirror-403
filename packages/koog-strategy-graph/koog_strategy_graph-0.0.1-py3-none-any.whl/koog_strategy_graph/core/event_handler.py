from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Sequence
from uuid import uuid4

from .core import GraphContext
from .events import (
    AgentClosingContext,
    AgentCompletedContext,
    AgentExecutionFailedContext,
    AgentStartingContext,
    LLMCallCompletedContext,
    LLMCallStartingContext,
    LLMStreamingCompletedContext,
    LLMStreamingFailedContext,
    LLMStreamingFrameReceivedContext,
    LLMStreamingStartingContext,
    NodeExecutionCompletedContext,
    NodeExecutionFailedContext,
    NodeExecutionStartingContext,
    StrategyCompletedContext,
    StrategyStartingContext,
    SubgraphExecutionCompletedContext,
    SubgraphExecutionFailedContext,
    SubgraphExecutionStartingContext,
    ToolCallCompletedContext,
    ToolCallFailedContext,
    ToolCallStartingContext,
    ToolValidationFailedContext,
    execution_info_from_path,
)

_KOOG_RUN_ID_KEY = "__koog_run_id__"


def _run_id(ctx: GraphContext) -> str:
    rid = str(ctx.get(_KOOG_RUN_ID_KEY, "") or "")
    if rid:
        return rid
    rid = str(uuid4())
    ctx.store(_KOOG_RUN_ID_KEY, rid)
    return rid


def _event_id() -> str:
    return str(uuid4())


def _tools_names(tools: Any) -> List[str]:
    # tools may be ToolDescriptor, or arbitrary user values; best-effort stringify.
    if tools is None:
        return []
    if isinstance(tools, (list, tuple)):
        out: List[str] = []
        for t in tools:
            name = getattr(t, "name", None)
            out.append(str(name) if name else str(t))
        return out
    name = getattr(tools, "name", None)
    return [str(name) if name else str(tools)]


@dataclass
class EventHandlerConfig:
    """
    Koog-like appendable handler configuration.
    Each `on_*` method appends another callback for that event type.
    """

    on_agent_starting: List[Callable[[AgentStartingContext], None]] = field(default_factory=list)
    on_agent_completed: List[Callable[[AgentCompletedContext], None]] = field(default_factory=list)
    on_agent_execution_failed: List[Callable[[AgentExecutionFailedContext], None]] = field(default_factory=list)
    on_agent_closing: List[Callable[[AgentClosingContext], None]] = field(default_factory=list)

    on_strategy_starting: List[Callable[[StrategyStartingContext], None]] = field(default_factory=list)
    on_strategy_completed: List[Callable[[StrategyCompletedContext], None]] = field(default_factory=list)

    on_node_execution_starting: List[Callable[[NodeExecutionStartingContext], None]] = field(default_factory=list)
    on_node_execution_completed: List[Callable[[NodeExecutionCompletedContext], None]] = field(default_factory=list)
    on_node_execution_failed: List[Callable[[NodeExecutionFailedContext], None]] = field(default_factory=list)

    on_subgraph_execution_starting: List[Callable[[SubgraphExecutionStartingContext], None]] = field(default_factory=list)
    on_subgraph_execution_completed: List[Callable[[SubgraphExecutionCompletedContext], None]] = field(default_factory=list)
    on_subgraph_execution_failed: List[Callable[[SubgraphExecutionFailedContext], None]] = field(default_factory=list)

    on_llm_call_starting: List[Callable[[LLMCallStartingContext], None]] = field(default_factory=list)
    on_llm_call_completed: List[Callable[[LLMCallCompletedContext], None]] = field(default_factory=list)

    on_llm_streaming_starting: List[Callable[[LLMStreamingStartingContext], None]] = field(default_factory=list)
    on_llm_streaming_frame_received: List[Callable[[LLMStreamingFrameReceivedContext], None]] = field(default_factory=list)
    on_llm_streaming_failed: List[Callable[[LLMStreamingFailedContext], None]] = field(default_factory=list)
    on_llm_streaming_completed: List[Callable[[LLMStreamingCompletedContext], None]] = field(default_factory=list)

    on_tool_call_starting: List[Callable[[ToolCallStartingContext], None]] = field(default_factory=list)
    on_tool_validation_failed: List[Callable[[ToolValidationFailedContext], None]] = field(default_factory=list)
    on_tool_call_failed: List[Callable[[ToolCallFailedContext], None]] = field(default_factory=list)
    on_tool_call_completed: List[Callable[[ToolCallCompletedContext], None]] = field(default_factory=list)

    # ----------------
    # Koog-like API
    # ----------------

    def onAgentStarting(self, fn: Callable[[AgentStartingContext], None]) -> None:
        self.on_agent_starting.append(fn)

    def onAgentCompleted(self, fn: Callable[[AgentCompletedContext], None]) -> None:
        self.on_agent_completed.append(fn)

    def onAgentExecutionFailed(self, fn: Callable[[AgentExecutionFailedContext], None]) -> None:
        self.on_agent_execution_failed.append(fn)

    def onAgentClosing(self, fn: Callable[[AgentClosingContext], None]) -> None:
        self.on_agent_closing.append(fn)

    def onStrategyStarting(self, fn: Callable[[StrategyStartingContext], None]) -> None:
        self.on_strategy_starting.append(fn)

    def onStrategyCompleted(self, fn: Callable[[StrategyCompletedContext], None]) -> None:
        self.on_strategy_completed.append(fn)

    def onNodeExecutionStarting(self, fn: Callable[[NodeExecutionStartingContext], None]) -> None:
        self.on_node_execution_starting.append(fn)

    def onNodeExecutionCompleted(self, fn: Callable[[NodeExecutionCompletedContext], None]) -> None:
        self.on_node_execution_completed.append(fn)

    def onNodeExecutionFailed(self, fn: Callable[[NodeExecutionFailedContext], None]) -> None:
        self.on_node_execution_failed.append(fn)

    def onSubgraphExecutionStarting(self, fn: Callable[[SubgraphExecutionStartingContext], None]) -> None:
        self.on_subgraph_execution_starting.append(fn)

    def onSubgraphExecutionCompleted(self, fn: Callable[[SubgraphExecutionCompletedContext], None]) -> None:
        self.on_subgraph_execution_completed.append(fn)

    def onSubgraphExecutionFailed(self, fn: Callable[[SubgraphExecutionFailedContext], None]) -> None:
        self.on_subgraph_execution_failed.append(fn)

    def onLLMCallStarting(self, fn: Callable[[LLMCallStartingContext], None]) -> None:
        self.on_llm_call_starting.append(fn)

    def onLLMCallCompleted(self, fn: Callable[[LLMCallCompletedContext], None]) -> None:
        self.on_llm_call_completed.append(fn)

    def onLLMStreamingStarting(self, fn: Callable[[LLMStreamingStartingContext], None]) -> None:
        self.on_llm_streaming_starting.append(fn)

    def onLLMStreamingFrameReceived(self, fn: Callable[[LLMStreamingFrameReceivedContext], None]) -> None:
        self.on_llm_streaming_frame_received.append(fn)

    def onLLMStreamingFailed(self, fn: Callable[[LLMStreamingFailedContext], None]) -> None:
        self.on_llm_streaming_failed.append(fn)

    def onLLMStreamingCompleted(self, fn: Callable[[LLMStreamingCompletedContext], None]) -> None:
        self.on_llm_streaming_completed.append(fn)

    def onToolCallStarting(self, fn: Callable[[ToolCallStartingContext], None]) -> None:
        self.on_tool_call_starting.append(fn)

    def onToolValidationFailed(self, fn: Callable[[ToolValidationFailedContext], None]) -> None:
        self.on_tool_validation_failed.append(fn)

    def onToolCallFailed(self, fn: Callable[[ToolCallFailedContext], None]) -> None:
        self.on_tool_call_failed.append(fn)

    def onToolCallCompleted(self, fn: Callable[[ToolCallCompletedContext], None]) -> None:
        self.on_tool_call_completed.append(fn)


@dataclass
class EventHandlerFeature:
    """
    Koog-like EventHandler feature implemented as a FeaturePipeline-consumable feature.

    We keep it synchronous for now (Python parity surface). Handlers should be fast and non-blocking.
    """

    config: EventHandlerConfig = field(default_factory=EventHandlerConfig)

    # ---------------------------------------------------------------------
    # Feature protocol compatibility (legacy minimal hook surface)
    #
    # `FeaturePipeline.features` is typed as `List[Feature]` where `Feature`
    # requires these four methods. EventHandlerFeature mainly consumes the
    # richer, optional `on_*` hooks on FeaturePipeline, but we still implement
    # these as no-ops so static type checkers accept `features.append(...)`.
    # ---------------------------------------------------------------------

    def on_node_start(self, *, node: str, ctx: GraphContext, input_value: Any) -> None:
        return None

    def on_node_end(self, *, node: str, ctx: GraphContext, input_value: Any, output_value: Any) -> None:
        return None

    def on_tool_executed(self, *, tool: str, ok: bool, ctx: GraphContext) -> None:
        return None

    def on_llm_called(self, *, ctx: GraphContext) -> None:
        return None

    def _exec_info(self, ctx: GraphContext) -> Any:
        return execution_info_from_path(ctx.execution_path())

    def _agent_id(self, ctx: GraphContext) -> str:
        return str(ctx.get("agent_id") or ctx.get("__koog_agent_id__") or "")

    def _emit(self, handlers: Sequence[Callable[[Any], None]], payload: Any) -> None:
        for h in list(handlers):
            try:
                h(payload)
            except Exception:
                continue

    # ------------------------
    # Agent lifecycle (manual)
    # ------------------------

    def on_agent_starting(self, *, ctx: GraphContext, agent_id: str, run_id: str) -> None:
        self._emit(
            self.config.on_agent_starting,
            AgentStartingContext(event_id=_event_id(), execution_info=self._exec_info(ctx), agent_id=agent_id, run_id=run_id),
        )

    def on_agent_completed(self, *, ctx: GraphContext, agent_id: str, run_id: str, result: Any) -> None:
        self._emit(
            self.config.on_agent_completed,
            AgentCompletedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                agent_id=agent_id,
                run_id=run_id,
                result=result,
            ),
        )

    def on_agent_execution_failed(self, *, ctx: GraphContext, agent_id: str, run_id: str, error: Exception) -> None:
        self._emit(
            self.config.on_agent_execution_failed,
            AgentExecutionFailedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                agent_id=agent_id,
                run_id=run_id,
                error=error,
            ),
        )

    def on_agent_closing(self, *, ctx: GraphContext, agent_id: str) -> None:
        self._emit(
            self.config.on_agent_closing,
            AgentClosingContext(event_id=_event_id(), execution_info=self._exec_info(ctx), agent_id=agent_id),
        )

    # ----------------
    # Strategy events
    # ----------------

    def on_strategy_starting(self, *, ctx: GraphContext, strategy: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_strategy_starting,
            StrategyStartingContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                strategy_name=str(getattr(strategy, "name", "") or ""),
                graph=None,
            ),
        )

    def on_strategy_completed(self, *, ctx: GraphContext, strategy: Any, result: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_strategy_completed,
            StrategyCompletedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                strategy_name=str(getattr(strategy, "name", "") or ""),
                result=result,
            ),
        )

    # -------------
    # Node events
    # -------------

    def on_node_execution_starting(self, *, ctx: GraphContext, node: Any, node_path: str, node_input: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_node_execution_starting,
            NodeExecutionStartingContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                node_name=str(getattr(node, "name", "") or ""),
                node_path=str(node_path or ""),
                input_value=node_input,
            ),
        )

    def on_node_execution_completed(
        self,
        *,
        ctx: GraphContext,
        node: Any,
        node_path: str,
        node_input: Any,
        node_output: Any,
        is_technical: bool,
    ) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_node_execution_completed,
            NodeExecutionCompletedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                node_name=str(getattr(node, "name", "") or ""),
                node_path=str(node_path or ""),
                input_value=node_input,
                output_value=node_output,
                is_technical=bool(is_technical),
            ),
        )

    def on_node_execution_failed(
        self,
        *,
        ctx: GraphContext,
        node: Any,
        node_path: str,
        node_input: Any,
        error: Exception,
        is_technical: bool,
    ) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_node_execution_failed,
            NodeExecutionFailedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                node_name=str(getattr(node, "name", "") or ""),
                node_path=str(node_path or ""),
                input_value=node_input,
                error=error,
                is_technical=bool(is_technical),
            ),
        )

    # ----------------
    # Subgraph events
    # ----------------

    def on_subgraph_execution_starting(self, *, ctx: GraphContext, subgraph: Any, subgraph_input: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_subgraph_execution_starting,
            SubgraphExecutionStartingContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                subgraph_name=str(getattr(subgraph, "name", "") or ""),
                input_value=subgraph_input,
            ),
        )

    def on_subgraph_execution_completed(self, *, ctx: GraphContext, subgraph: Any, subgraph_input: Any, subgraph_output: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_subgraph_execution_completed,
            SubgraphExecutionCompletedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                subgraph_name=str(getattr(subgraph, "name", "") or ""),
                input_value=subgraph_input,
                output_value=subgraph_output,
            ),
        )

    def on_subgraph_execution_failed(self, *, ctx: GraphContext, subgraph: Any, subgraph_input: Any, error: Exception) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_subgraph_execution_failed,
            SubgraphExecutionFailedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                subgraph_name=str(getattr(subgraph, "name", "") or ""),
                input_value=subgraph_input,
                error=error,
            ),
        )

    # --------
    # LLM call
    # --------

    def on_llm_call_starting(
        self,
        *,
        ctx: GraphContext,
        prompt: Any,
        model: Any,
        tools: Any,
        tool_choice: Any,
        params: Any,
    ) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_llm_call_starting,
            LLMCallStartingContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                prompt=prompt,
                model=model,
                tools=_tools_names(tools),
                tool_choice=tool_choice,
                params=params,
            ),
        )

    def on_llm_call_completed(self, *, ctx: GraphContext, prompt: Any, model: Any, response: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_llm_call_completed,
            LLMCallCompletedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                prompt=prompt,
                model=model,
                response=response,
            ),
        )

    # --------------
    # LLM streaming
    # --------------

    def on_llm_streaming_starting(self, *, ctx: GraphContext, prompt: Any, model: Any, tools: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_llm_streaming_starting,
            LLMStreamingStartingContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                model=model,
                prompt=prompt,
                tools=_tools_names(tools),
            ),
        )

    def on_llm_streaming_frame_received(self, *, ctx: GraphContext, frame: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_llm_streaming_frame_received,
            LLMStreamingFrameReceivedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                frame=frame,
            ),
        )

    def on_llm_streaming_failed(self, *, ctx: GraphContext, error: Exception) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_llm_streaming_failed,
            LLMStreamingFailedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                error=error,
            ),
        )

    def on_llm_streaming_completed(self, *, ctx: GraphContext) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_llm_streaming_completed,
            LLMStreamingCompletedContext(event_id=_event_id(), execution_info=self._exec_info(ctx), run_id=rid),
        )

    # --------------
    # Tool execution
    # --------------

    def on_tool_call_starting(self, *, ctx: GraphContext, tool_call_id: Optional[str], tool: str, args: Any) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_tool_call_starting,
            ToolCallStartingContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                tool_call_id=tool_call_id,
                tool_name=str(tool or ""),
                tool_args=args,
            ),
        )

    def on_tool_validation_failed(self, *, ctx: GraphContext, tool_call_id: Optional[str], tool: str, args: Any, error: Exception) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_tool_validation_failed,
            ToolValidationFailedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                tool_call_id=tool_call_id,
                tool_name=str(tool or ""),
                tool_args=args,
                error=error,
            ),
        )

    def on_tool_call_failed(self, *, ctx: GraphContext, tool_call_id: Optional[str], tool: str, args: Any, error: Exception) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_tool_call_failed,
            ToolCallFailedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                tool_call_id=tool_call_id,
                tool_name=str(tool or ""),
                tool_args=args,
                error=error,
            ),
        )

    def on_tool_call_completed(
        self,
        *,
        ctx: GraphContext,
        tool_call_id: Optional[str],
        tool: str,
        args: Any,
        ok: bool,
        result: Any,
    ) -> None:
        rid = _run_id(ctx)
        self._emit(
            self.config.on_tool_call_completed,
            ToolCallCompletedContext(
                event_id=_event_id(),
                execution_info=self._exec_info(ctx),
                run_id=rid,
                tool_call_id=tool_call_id,
                tool_name=str(tool or ""),
                tool_args=args,
                ok=bool(ok),
                result=result,
            ),
        )

