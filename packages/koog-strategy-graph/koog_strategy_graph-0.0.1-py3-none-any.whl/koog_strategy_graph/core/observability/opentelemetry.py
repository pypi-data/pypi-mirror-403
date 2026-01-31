from __future__ import annotations

import contextlib
from typing import Any, Dict, Optional

# Check for opentelemetry presence; if not installed, these will fail or we can make them optional.
# For now, we assume they are installed as per requirements.
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode, Span
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False
    trace = None # type: ignore

from ..events import (
    AgentStartingContext,
    AgentCompletedContext,
    AgentExecutionFailedContext,
    StrategyStartingContext,
    StrategyCompletedContext,
    NodeExecutionStartingContext,
    NodeExecutionCompletedContext,
    NodeExecutionFailedContext,
    LLMCallStartingContext,
    LLMCallCompletedContext,
    ToolCallStartingContext,
    ToolCallCompletedContext,
    ToolCallFailedContext,
)
from ..event_handler import EventHandlerConfig, EventHandlerFeature


class OpenTelemetryFeature(EventHandlerFeature):
    """
    Tracing feature using OpenTelemetry.
    Maps Koog lifecycle events to OTel spans.
    """

    def __init__(self, tracer_provider: Any = None):
        super().__init__()
        if not _HAS_OTEL:
            # warn or log? For now, just no-op
            return

        self.tracer = trace.get_tracer("koog.agent", tracer_provider=tracer_provider)
        
        # We need to track active spans. 
        # Since events are synchronous and nested in the current runtime impl, 
        # we can use a simple stack or mapping if we assume context propagation works.
        # However, Koog's event handler is callback based. 
        
        # We will use a context dictionary mapping run_id/event_id to Spans.
        # Ideally, we would use OTel's Context API, but we are hooking into specific start/end events.
        # We'll map (run_id + correlation_key) -> Span.
        
        self._spans: Dict[str, Span] = {}

        # Register handlers
        c = self.config
        c.onAgentStarting(self._on_agent_starting)
        c.onAgentCompleted(self._on_agent_completed)
        c.onAgentExecutionFailed(self._on_agent_failed)
        
        c.onNodeExecutionStarting(self._on_node_starting)
        c.onNodeExecutionCompleted(self._on_node_completed)
        c.onNodeExecutionFailed(self._on_node_failed)
        
        c.onLLMCallStarting(self._on_llm_starting)
        c.onLLMCallCompleted(self._on_llm_completed)
        
        c.onToolCallStarting(self._on_tool_starting)
        c.onToolCallCompleted(self._on_tool_completed)
        c.onToolCallFailed(self._on_tool_failed)

    def _key(self, run_id: str, suffix: str) -> str:
        return f"{run_id}:{suffix}"

    # --- Agent Lifecycle ---

    def _on_agent_starting(self, ctx: AgentStartingContext) -> None:
        if not _HAS_OTEL: return
        span = self.tracer.start_span(
            name=f"agent {ctx.agent_id}",
            attributes={
                "koog.agent_id": ctx.agent_id,
                "koog.run_id": ctx.run_id
            }
        )
        self._spans[self._key(ctx.run_id, "agent")] = span

    def _on_agent_completed(self, ctx: AgentCompletedContext) -> None:
        key = self._key(ctx.run_id, "agent")
        span = self._spans.pop(key, None)
        if span:
            span.set_status(Status(StatusCode.OK))
            span.end()

    def _on_agent_failed(self, ctx: AgentExecutionFailedContext) -> None:
        key = self._key(ctx.run_id, "agent")
        span = self._spans.pop(key, None)
        if span:
            span.record_exception(ctx.error)
            span.set_status(Status(StatusCode.ERROR, str(ctx.error)))
            span.end()

    # --- Node Lifecycle ---

    def _on_node_starting(self, ctx: NodeExecutionStartingContext) -> None:
        if not _HAS_OTEL: return
        # Create a child span. In a real async/context impl we'd use use_span.
        # Here we manually parent if possible, or just let OTel implicit context work if the runtime supports it.
        # Since we are in a callback, implicit context might be lost or tricky.
        # We will try to get the parent from our map if we can enforce single-threaded behavior per run_id, 
        # but for concurrent executions this map is dangerous without thread-locals.
        # Given Koog Python runtime is often single-threaded per agent run (asyncio), 
        # we'll assume we can relying on OTel's built-in context management if we were using `with tracer.start_as_current_span`.
        # But we are in callbacks. 
        
        # Use explicit context from parent agent span?
        parent_span = self._spans.get(self._key(ctx.run_id, "agent"))
        ctx_token = trace.set_span_in_context(parent_span) if parent_span else None
        
        span = self.tracer.start_span(
            name=f"node {ctx.node_name}",
            context=ctx_token,
            attributes={
                "koog.node_name": ctx.node_name,
                "koog.node_path": ctx.node_path,
                "koog.run_id": ctx.run_id
            }
        )
        self._spans[self._key(ctx.run_id, f"node:{ctx.node_path}")] = span

    def _on_node_completed(self, ctx: NodeExecutionCompletedContext) -> None:
        key = self._key(ctx.run_id, f"node:{ctx.node_path}")
        span = self._spans.pop(key, None)
        if span:
            span.set_status(Status(StatusCode.OK))
            span.end()

    def _on_node_failed(self, ctx: NodeExecutionFailedContext) -> None:
        key = self._key(ctx.run_id, f"node:{ctx.node_path}")
        span = self._spans.pop(key, None)
        if span:
            span.record_exception(ctx.error)
            span.set_status(Status(StatusCode.ERROR, str(ctx.error)))
            span.end()

    # --- LLM Call ---

    def _on_llm_starting(self, ctx: LLMCallStartingContext) -> None:
        if not _HAS_OTEL: return
        # Parent could be node or agent
        # Finding parent is tricky without passing context through the stack. 
        # We'll just start a span.
        
        span = self.tracer.start_span(
            name="llm_call",
            attributes={
                "koog.run_id": ctx.run_id,
                "gen_ai.system": "koog",
                "gen_ai.request.model": str(ctx.model),
            }
        )
        # We can't easily key by path because LLM call doesn't have a unique path ID in the event 
        # other than being inside a node. 
        # We'll use a hacky stack key or just the event_id if we had start/end correlation.
        # But wait, LLMCallStartingContext has event_id. But Completed has a DIFFERENT event_id.
        # We define a key based on run_id. If multiple LLM calls happen in parallel, this is buggy.
        # Assumption: Serial LLM calls per run_id.
        self._spans[self._key(ctx.run_id, "llm_call")] = span

    def _on_llm_completed(self, ctx: LLMCallCompletedContext) -> None:
        key = self._key(ctx.run_id, "llm_call")
        span = self._spans.pop(key, None)
        if span:
            span.set_status(Status(StatusCode.OK))
            span.end()

    # --- Tool Call ---

    def _on_tool_starting(self, ctx: ToolCallStartingContext) -> None:
        if not _HAS_OTEL: return
        span = self.tracer.start_span(
            name=f"tool {ctx.tool_name}",
            attributes={
                "koog.run_id": ctx.run_id,
                "koog.tool_name": ctx.tool_name,
                "koog.tool_call_id": str(ctx.tool_call_id)
            }
        )
        self._spans[self._key(ctx.run_id, f"tool:{ctx.tool_call_id}")] = span

    def _on_tool_completed(self, ctx: ToolCallCompletedContext) -> None:
        key = self._key(ctx.run_id, f"tool:{ctx.tool_call_id}")
        span = self._spans.pop(key, None)
        if span:
            span.set_status(Status(StatusCode.OK))
            span.end()
            
    def _on_tool_failed(self, ctx: ToolCallFailedContext) -> None:
        key = self._key(ctx.run_id, f"tool:{ctx.tool_call_id}")
        span = self._spans.pop(key, None)
        if span:
            span.record_exception(ctx.error)
            span.set_status(Status(StatusCode.ERROR, str(ctx.error)))
            span.end()
