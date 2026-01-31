from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Protocol, runtime_checkable

from .core import GraphContext


@runtime_checkable
class Feature(Protocol):
    """
    Minimal Koog-like feature hook surface.
    """

    def on_node_start(self, *, node: str, ctx: GraphContext, input_value: Any) -> None: ...

    def on_node_end(self, *, node: str, ctx: GraphContext, input_value: Any, output_value: Any) -> None: ...

    def on_tool_executed(self, *, tool: str, ok: bool, ctx: GraphContext) -> None: ...

    def on_llm_called(self, *, ctx: GraphContext) -> None: ...


@dataclass
class FeaturePipeline:
    features: List[Feature] = field(default_factory=list)

    # -------------------
    # Strategy-level hooks
    # -------------------

    def on_strategy_starting(self, *, ctx: GraphContext, strategy: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_strategy_starting", None)
                if callable(fn):
                    fn(ctx=ctx, strategy=strategy)
            except Exception:
                continue

    def on_strategy_completed(self, *, ctx: GraphContext, strategy: Any, result: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_strategy_completed", None)
                if callable(fn):
                    fn(ctx=ctx, strategy=strategy, result=result)
            except Exception:
                continue

    # -------------
    # Node execution
    # -------------

    def on_node_execution_starting(self, *, ctx: GraphContext, node: Any, node_path: str, node_input: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_node_execution_starting", None)
                if callable(fn):
                    fn(ctx=ctx, node=node, node_path=node_path, node_input=node_input)
            except Exception:
                continue

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
        for f in self.features:
            try:
                fn = getattr(f, "on_node_execution_completed", None)
                if callable(fn):
                    fn(
                        ctx=ctx,
                        node=node,
                        node_path=node_path,
                        node_input=node_input,
                        node_output=node_output,
                        is_technical=is_technical,
                    )
            except Exception:
                continue

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
        for f in self.features:
            try:
                fn = getattr(f, "on_node_execution_failed", None)
                if callable(fn):
                    fn(
                        ctx=ctx,
                        node=node,
                        node_path=node_path,
                        node_input=node_input,
                        error=error,
                        is_technical=is_technical,
                    )
            except Exception:
                continue

    def on_node_start(self, *, node: str, ctx: GraphContext, input_value: Any) -> None:
        for f in self.features:
            try:
                f.on_node_start(node=node, ctx=ctx, input_value=input_value)
            except Exception:
                continue

    def on_node_end(self, *, node: str, ctx: GraphContext, input_value: Any, output_value: Any) -> None:
        for f in self.features:
            try:
                f.on_node_end(node=node, ctx=ctx, input_value=input_value, output_value=output_value)
            except Exception:
                continue

    def on_tool_executed(self, *, tool: str, ok: bool, ctx: GraphContext) -> None:
        for f in self.features:
            try:
                f.on_tool_executed(tool=tool, ok=ok, ctx=ctx)
            except Exception:
                continue

    def on_llm_called(self, *, ctx: GraphContext) -> None:
        for f in self.features:
            try:
                f.on_llm_called(ctx=ctx)
            except Exception:
                continue

    # ----------------
    # Agent lifecycle
    # ----------------

    def on_agent_starting(self, *, ctx: GraphContext, agent_id: str, run_id: str) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_agent_starting", None)
                if callable(fn):
                    fn(ctx=ctx, agent_id=agent_id, run_id=run_id)
            except Exception:
                continue

    def on_agent_completed(self, *, ctx: GraphContext, agent_id: str, run_id: str, result: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_agent_completed", None)
                if callable(fn):
                    fn(ctx=ctx, agent_id=agent_id, run_id=run_id, result=result)
            except Exception:
                continue

    def on_agent_execution_failed(self, *, ctx: GraphContext, agent_id: str, run_id: str, error: Exception) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_agent_execution_failed", None)
                if callable(fn):
                    fn(ctx=ctx, agent_id=agent_id, run_id=run_id, error=error)
            except Exception:
                continue

    def on_agent_closing(self, *, ctx: GraphContext, agent_id: str) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_agent_closing", None)
                if callable(fn):
                    fn(ctx=ctx, agent_id=agent_id)
            except Exception:
                continue

    # ----------------
    # Subgraph events
    # ----------------

    def on_subgraph_execution_starting(self, *, ctx: GraphContext, subgraph: Any, subgraph_input: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_subgraph_execution_starting", None)
                if callable(fn):
                    fn(ctx=ctx, subgraph=subgraph, subgraph_input=subgraph_input)
            except Exception:
                continue

    def on_subgraph_execution_completed(
        self, *, ctx: GraphContext, subgraph: Any, subgraph_input: Any, subgraph_output: Any
    ) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_subgraph_execution_completed", None)
                if callable(fn):
                    fn(ctx=ctx, subgraph=subgraph, subgraph_input=subgraph_input, subgraph_output=subgraph_output)
            except Exception:
                continue

    def on_subgraph_execution_failed(self, *, ctx: GraphContext, subgraph: Any, subgraph_input: Any, error: Exception) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_subgraph_execution_failed", None)
                if callable(fn):
                    fn(ctx=ctx, subgraph=subgraph, subgraph_input=subgraph_input, error=error)
            except Exception:
                continue

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
        for f in self.features:
            try:
                fn = getattr(f, "on_llm_call_starting", None)
                if callable(fn):
                    fn(ctx=ctx, prompt=prompt, model=model, tools=tools, tool_choice=tool_choice, params=params)
            except Exception:
                continue

    def on_llm_call_completed(self, *, ctx: GraphContext, prompt: Any, model: Any, response: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_llm_call_completed", None)
                if callable(fn):
                    fn(ctx=ctx, prompt=prompt, model=model, response=response)
            except Exception:
                continue

    # --------------
    # Tool execution
    # --------------

    def on_tool_call_starting(self, *, ctx: GraphContext, tool_call_id: Any, tool: str, args: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_tool_call_starting", None)
                if callable(fn):
                    fn(ctx=ctx, tool_call_id=tool_call_id, tool=tool, args=args)
            except Exception:
                continue

    def on_tool_validation_failed(self, *, ctx: GraphContext, tool_call_id: Any, tool: str, args: Any, error: Exception) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_tool_validation_failed", None)
                if callable(fn):
                    fn(ctx=ctx, tool_call_id=tool_call_id, tool=tool, args=args, error=error)
            except Exception:
                continue

    def on_tool_call_failed(self, *, ctx: GraphContext, tool_call_id: Any, tool: str, args: Any, error: Exception) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_tool_call_failed", None)
                if callable(fn):
                    fn(ctx=ctx, tool_call_id=tool_call_id, tool=tool, args=args, error=error)
            except Exception:
                continue

    def on_tool_call_completed(
        self,
        *,
        ctx: GraphContext,
        tool_call_id: Any,
        tool: str,
        args: Any,
        ok: bool,
        result: Any,
    ) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_tool_call_completed", None)
                if callable(fn):
                    fn(ctx=ctx, tool_call_id=tool_call_id, tool=tool, args=args, ok=ok, result=result)
            except Exception:
                continue

    # --------------------
    # LLM streaming events
    # --------------------

    def on_llm_streaming_starting(self, *, ctx: GraphContext, prompt: Any, model: Any, tools: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_llm_streaming_starting", None)
                if callable(fn):
                    fn(ctx=ctx, prompt=prompt, model=model, tools=tools)
            except Exception:
                continue

    def on_llm_streaming_frame_received(self, *, ctx: GraphContext, frame: Any) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_llm_streaming_frame_received", None)
                if callable(fn):
                    fn(ctx=ctx, frame=frame)
            except Exception:
                continue

    def on_llm_streaming_failed(self, *, ctx: GraphContext, error: Exception) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_llm_streaming_failed", None)
                if callable(fn):
                    fn(ctx=ctx, error=error)
            except Exception:
                continue

    def on_llm_streaming_completed(self, *, ctx: GraphContext) -> None:
        for f in self.features:
            try:
                fn = getattr(f, "on_llm_streaming_completed", None)
                if callable(fn):
                    fn(ctx=ctx)
            except Exception:
                continue


