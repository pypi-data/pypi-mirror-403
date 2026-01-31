from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar

from .core import GraphContext, Node, NodeBase, Strategy, Subgraph
from .dsl import StrategyBuilder, SubgraphBuilder, strategy as base_strategy
from .environment import AgentEnvironment
from .features import FeaturePipeline
from .history import HistoryCompressionStrategy, WholeHistory
from .llm_executor import AgentSession, LLMExecutor, ToolChoice
from .messages import (
    AssistantMessage,
    MessageBase,
    Prompt,
    ResponseMessage,
    ToolCallMessage,
    ToolResultMessage,
    UserMessage,
)
from .structured import StructuredResult
from .tools import ReceivedToolResult
from .tools import SafeTool
from .tool_selection import (
    ALL,
    Tools,
    ToolSelectionStrategy,
    is_tool_allowed,
    select_tools_for_strategy,
    set_allowed_tool_names,
    tools_to_descriptors,
)
from .response_processor import ResponseProcessor

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class AIAgentSubgraph(Subgraph[Any, Any]):
    """
    Koog agent subgraph (must be a real `Subgraph` so metadata traversal works).

    Kotlin reference: `AIAgentSubgraph.execute(...)`:
    - select tools for the subgraph (ALL/NONE/Tools/AutoSelectForTask)
    - execute with inner toolset
    - restore previous toolset while keeping updated prompt history
    """

    def __init__(
        self,
        name: str,
        start: Any,
        finish: Any,
        *,
        tool_selection_strategy: ToolSelectionStrategy = ALL(),
        llm_model: Any = None,
        llm_params: Optional[dict] = None,
        response_processor: Optional[ResponseProcessor] = None,
    ):
        super().__init__(name=name, start=start, finish=finish)
        self.tool_selection_strategy = tool_selection_strategy
        self.llm_model = llm_model
        self.llm_params = dict(llm_params or {})
        self.response_processor = response_processor

    def execute(self, ctx: GraphContext, input_value: Any) -> Any:
        env = ctx.get("environment")
        session = ctx.get("session")
        llm = ctx.get("llm")
        if env is None or not hasattr(env, "tools"):
            raise RuntimeError("AIAgentSubgraph requires `environment` to be stored in context.")
        if not isinstance(session, AgentSession):
            raise RuntimeError("AIAgentSubgraph requires `session` (AgentSession) to be stored in context.")
        if not isinstance(llm, LLMExecutor):
            raise RuntimeError("AIAgentSubgraph requires `llm` (LLMExecutor) to be stored in context.")

        all_desc = env.tools.descriptors()
        selected_desc = select_tools_for_strategy(
            strategy=self.tool_selection_strategy,
            all_tools=all_desc,
            session=session,
            llm=llm,
        )
        selected_names = [d.name for d in selected_desc if d.name]

        prev_allowed = set_allowed_tool_names(ctx, selected_names)
        prev_llm_tools = list(session.llm_tools)
        prev_llm = llm
        try:
            session.llm_tools = list(selected_desc)
            if self.llm_model is not None or self.llm_params or self.response_processor is not None:
                if isinstance(self.llm_model, LLMExecutor):
                    ctx.store("llm", self.llm_model)
                else:
                    ctx.store(
                        "llm",
                        llm.with_overrides(
                            model=self.llm_model,
                            params=dict(self.llm_params or {}),
                            response_processor=self.response_processor,
                        ),
                    )
            return super().execute(ctx, input_value)
        finally:
            ctx.store("llm", prev_llm)
            session.llm_tools = prev_llm_tools
            set_allowed_tool_names(ctx, prev_allowed if isinstance(prev_allowed, list) else None)


class AIAgentGraphStrategy(Strategy[Any, Any]):
    """
    Koog strategy node (a Strategy is also a Subgraph in Kotlin).
    Applies tool selection strategy for the whole strategy execution, then delegates to base Strategy logic.
    """

    def __init__(
        self,
        name: str,
        start: Any,
        finish: Any,
        *,
        tool_selection_strategy: ToolSelectionStrategy = ALL(),
        llm_model: Any = None,
        llm_params: Optional[dict] = None,
        response_processor: Optional[ResponseProcessor] = None,
    ):
        super().__init__(name=name, start=start, finish=finish)
        self.tool_selection_strategy = tool_selection_strategy
        self.llm_model = llm_model
        self.llm_params = dict(llm_params or {})
        self.response_processor = response_processor

    def execute(self, ctx: GraphContext, input_value: Any) -> Any:
        env = ctx.get("environment")
        session = ctx.get("session")
        llm = ctx.get("llm")
        if env is None or not hasattr(env, "tools"):
            raise RuntimeError("AIAgentGraphStrategy requires `environment` to be stored in context.")
        if not isinstance(session, AgentSession):
            raise RuntimeError("AIAgentGraphStrategy requires `session` (AgentSession) to be stored in context.")
        if not isinstance(llm, LLMExecutor):
            raise RuntimeError("AIAgentGraphStrategy requires `llm` (LLMExecutor) to be stored in context.")

        all_desc = env.tools.descriptors()
        selected_desc = select_tools_for_strategy(
            strategy=self.tool_selection_strategy,
            all_tools=all_desc,
            session=session,
            llm=llm,
        )
        selected_names = [d.name for d in selected_desc if d.name]

        prev_allowed = set_allowed_tool_names(ctx, selected_names)
        prev_llm_tools = list(session.llm_tools)
        prev_llm = llm
        try:
            session.llm_tools = list(selected_desc)
            if self.llm_model is not None or self.llm_params or self.response_processor is not None:
                if isinstance(self.llm_model, LLMExecutor):
                    ctx.store("llm", self.llm_model)
                else:
                    ctx.store(
                        "llm",
                        llm.with_overrides(
                            model=self.llm_model,
                            params=dict(self.llm_params or {}),
                            response_processor=self.response_processor,
                        ),
                    )
            return super().execute(ctx, input_value)
        finally:
            ctx.store("llm", prev_llm)
            session.llm_tools = prev_llm_tools
            set_allowed_tool_names(ctx, prev_allowed if isinstance(prev_allowed, list) else None)


@dataclass()
class AgentSubgraphBuilder:
    """
    Koog subgraph builder for agent graphs.

    This mirrors Koog's `subgraph(...) { ... }` inside agent strategies.
    """

    name: str
    base: SubgraphBuilder[Any, Any]
    parent: "AgentStrategyBuilder"
    tool_selection_strategy: ToolSelectionStrategy = field(default_factory=ALL)
    llm_model: Any = None
    llm_params: Dict[str, Any] = field(default_factory=dict)
    response_processor: Optional[ResponseProcessor] = None

    def node(self, name: str, fn: Callable[[GraphContext, Any], Any]) -> Node[Any, Any]:
        # Mirror AgentStrategyBuilder.node(...) but build nodes inside this subgraph builder.
        def _wrapped(ctx: GraphContext, input_value: Any) -> Any:
            self.parent._pipeline(ctx).on_node_start(node=name, ctx=ctx, input_value=input_value)
            out = fn(ctx, input_value)
            self.parent._pipeline(ctx).on_node_end(node=name, ctx=ctx, input_value=input_value, output_value=out)
            return out

        return self.base.node(name, _wrapped)

    def node_llm_request(self, name: str, *, allow_tool_calls: bool = True) -> Node[str, ResponseMessage]:
        """
        Koog helper for subgraph builders: request LLM and append responses into the shared session prompt.
        """

        def _run(_ctx: GraphContext, message: str) -> ResponseMessage:
            session = self.parent._session(_ctx)
            llm = self.parent._llm(_ctx)
            session.append_user(message)
            choice = ToolChoice.AUTO if allow_tool_calls else ToolChoice.NONE
            self.parent._pipeline(_ctx).on_llm_called(ctx=_ctx)
            resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=choice)
            session.prompt.append(*resp.responses)
            return resp.responses[0]

        return self.node(name, _run)

    def edge(self, intermediate) -> None:
        self.base.edge(intermediate)

    def build(self) -> AIAgentSubgraph:
        return AIAgentSubgraph(
            name=self.name,
            start=self.base.node_start,
            finish=self.base.node_finish,
            tool_selection_strategy=self.tool_selection_strategy,
            llm_model=self.llm_model,
            llm_params=dict(self.llm_params or {}),
            response_processor=self.response_processor,
        )


@dataclass()
class AgentStrategyBuilder:
    """
    Koog strategy builder wrapper (Python).

    It wraps the generic `StrategyBuilder` but provides Koog-named node helpers that
    mutate an `AgentSession` (prompt history) and integrate tool execution.
    """

    base: StrategyBuilder[Any, Any]
    llm: LLMExecutor
    environment: AgentEnvironment
    session: AgentSession = field(default_factory=AgentSession)
    features: FeaturePipeline = field(default_factory=FeaturePipeline)
    tool_selection_strategy: ToolSelectionStrategy = field(default_factory=ALL)

    def _pipeline(self, ctx: GraphContext) -> FeaturePipeline:
        p = ctx.get_pipeline()
        return p if isinstance(p, FeaturePipeline) else self.features

    def _session(self, ctx: GraphContext) -> AgentSession:
        s = ctx.get("session")
        return s if isinstance(s, AgentSession) else self.session

    def _llm(self, ctx: GraphContext) -> LLMExecutor:
        llm = ctx.get("llm")
        return llm if isinstance(llm, LLMExecutor) else self.llm

    def _env(self, ctx: GraphContext) -> AgentEnvironment:
        env = ctx.get("environment")
        return env if isinstance(env, AgentEnvironment) else self.environment

    def node(self, name: str, fn: Callable[[GraphContext, Any], Any]) -> Node[Any, Any]:
        def _wrapped(ctx: GraphContext, input_value: Any) -> Any:
            self._pipeline(ctx).on_node_start(node=name, ctx=ctx, input_value=input_value)
            out = fn(ctx, input_value)
            self._pipeline(ctx).on_node_end(node=name, ctx=ctx, input_value=input_value, output_value=out)
            return out

        return self.base.node(name, _wrapped)

    def edge(self, intermediate) -> None:  # EdgeBuilderIntermediate
        self.base.edge(intermediate)

    def build(self):
        # Build the underlying strategy.
        strat = self.base.build()

        # Koog parity: strategy itself is also a subgraph with a tool selection strategy.
        agent_strat = AIAgentGraphStrategy(
            name=strat.name,
            start=strat.start,
            finish=strat.finish,
            tool_selection_strategy=self.tool_selection_strategy,
        )
        agent_strat.metadata = getattr(strat, "metadata", None)
        # Ensure nodes_map points to this wrapper strategy instance (Koog includes the strategy at key == name).
        if agent_strat.metadata is not None:
            try:
                agent_strat.metadata.nodes_map[agent_strat.name] = agent_strat
            except Exception:
                pass
        return agent_strat

    # -----------------
    # Koog subgraphs
    # -----------------

    def subgraph(
        self,
        name: str,
        *,
        tool_selection_strategy: ToolSelectionStrategy = ALL(),
        llm_model: Any = None,
        llm_params: Optional[Dict[str, Any]] = None,
        response_processor: Optional[ResponseProcessor] = None,
        define: Optional[Callable[[AgentSubgraphBuilder], None]] = None,
    ) -> AIAgentSubgraph:
        """
        Create a Koog-parity agent subgraph node with tool selection strategy.
        """
        base = self.base.subgraph(name)
        b = AgentSubgraphBuilder(
            name=name,
            base=base,
            parent=self,
            tool_selection_strategy=tool_selection_strategy,
            llm_model=llm_model,
            llm_params=dict(llm_params or {}),
            response_processor=response_processor,
        )
        if define is not None:
            define(b)
        return b.build()

    def subgraph_tools(
        self,
        name: str,
        *,
        tools: Sequence[Any],
        llm_model: Any = None,
        llm_params: Optional[Dict[str, Any]] = None,
        response_processor: Optional[ResponseProcessor] = None,
        define: Optional[Callable[[AgentSubgraphBuilder], None]] = None,
    ) -> AIAgentSubgraph:
        """
        Create a Koog-parity subgraph restricted to a specific list of Tool(s).
        """
        # Tools in Python parity are expected to implement the `Tool` protocol.
        typed: List[Tool[Any, Any]] = [t for t in tools if isinstance(t, Tool)]  # type: ignore[arg-type]
        return self.subgraph(
            name,
            tool_selection_strategy=Tools(tools=tools_to_descriptors(typed)),
            llm_model=llm_model,
            llm_params=llm_params,
            response_processor=response_processor,
            define=define,
        )

    # -----------------
    # Koog node helpers
    # -----------------

    def node_do_nothing(self, name: str) -> Node[Any, Any]:
        return self.node(name, lambda _ctx, x: x)

    def node_append_prompt(self, name: str, build: Callable[[Any], Sequence[MessageBase]]) -> Node[Any, Any]:
        def _run(_ctx: GraphContext, input_value: Any) -> Any:
            msgs = list(build(input_value))
            self._session(_ctx).prompt.append(*msgs)
            return input_value

        return self.node(name, _run)

    def node_llm_request(self, name: str, *, allow_tool_calls: bool = True) -> Node[str, ResponseMessage]:
        def _run(_ctx: GraphContext, message: str) -> ResponseMessage:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.append_user(message)
            choice = ToolChoice.AUTO if allow_tool_calls else ToolChoice.NONE
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_called(ctx=_ctx)
            pipeline.on_llm_call_starting(
                ctx=_ctx,
                prompt=session.prompt,
                model=llm.default_model,
                tools=session.llm_tools,
                tool_choice=choice,
                params=dict(llm.default_params),
            )
            resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=choice)
            pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=resp)
            # Koog keeps prompt continuity; append parsed responses.
            session.prompt.append(*resp.responses)
            return resp.responses[0]

        return self.node(name, _run)

    def node_llm_send_message_only_calling_tools(self, name: str) -> Node[str, ResponseMessage]:
        def _run(_ctx: GraphContext, message: str) -> ResponseMessage:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.append_user(message)
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_called(ctx=_ctx)
            pipeline.on_llm_call_starting(
                ctx=_ctx,
                prompt=session.prompt,
                model=llm.default_model,
                tools=session.llm_tools,
                tool_choice=ToolChoice.REQUIRED,
                params=dict(llm.default_params),
            )
            resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.REQUIRED)
            pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=resp)
            session.prompt.append(*resp.responses)
            return resp.responses[0]

        return self.node(name, _run)

    def node_llm_send_message_force_one_tool(self, name: str, tool_name: str) -> Node[str, ResponseMessage]:
        def _run(_ctx: GraphContext, message: str) -> ResponseMessage:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.append_user(message)
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_called(ctx=_ctx)
            pipeline.on_llm_call_starting(
                ctx=_ctx,
                prompt=session.prompt,
                model=llm.default_model,
                tools=session.llm_tools,
                tool_choice=ToolChoice.named(tool_name),
                params=dict(llm.default_params),
            )
            resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.named(tool_name))
            pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=resp)
            session.prompt.append(*resp.responses)
            return resp.responses[0]

        return self.node(name, _run)

    def node_execute_tool(self, name: str) -> Node[ToolCallMessage, ReceivedToolResult]:
        def _run(_ctx: GraphContext, tool_call: ToolCallMessage) -> ReceivedToolResult:
            pipeline = self._pipeline(_ctx)
            pipeline.on_tool_call_starting(
                ctx=_ctx,
                tool_call_id=tool_call.tool_call_id,
                tool=(tool_call.tool or "").strip(),
                args=dict(tool_call.args or {}),
            )
            if not is_tool_allowed(_ctx, (tool_call.tool or "").strip()):
                tr = ReceivedToolResult(
                    tool=(tool_call.tool or "").strip(),
                    tool_call_id=tool_call.tool_call_id,
                    safe_result=SafeTool.Failure(
                        content=f"Tool not allowed in this subgraph: {tool_call.tool}",
                        message=f"Tool not allowed in this subgraph: {tool_call.tool}",
                    ),
                )
                pipeline.on_tool_executed(tool=tr.tool, ok=False, ctx=_ctx)
                pipeline.on_tool_call_failed(
                    ctx=_ctx,
                    tool_call_id=tool_call.tool_call_id,
                    tool=tr.tool,
                    args=dict(tool_call.args or {}),
                    error=RuntimeError(f"Tool not allowed in this subgraph: {tool_call.tool}"),
                )
                return tr
            tr = self._env(_ctx).execute_tool(tool_call)
            ok = isinstance(tr.safe_result, SafeTool.Success)
            pipeline.on_tool_executed(tool=tr.tool, ok=ok, ctx=_ctx)
            pipeline.on_tool_call_completed(
                ctx=_ctx,
                tool_call_id=tool_call.tool_call_id,
                tool=tr.tool,
                args=dict(tool_call.args or {}),
                ok=ok,
                result=tr.safe_result,
            )
            return tr

        return self.node(name, _run)

    def node_execute_multiple_tools(self, name: str, *, parallel_tools: bool = False) -> Node[List[ToolCallMessage], List[ReceivedToolResult]]:
        def _run(_ctx: GraphContext, tool_calls: List[ToolCallMessage]) -> List[ReceivedToolResult]:
            # Enforce allowed tools for the subgraph context.
            for c in tool_calls:
                if not is_tool_allowed(_ctx, (c.tool or "").strip()):
                    return [
                        ReceivedToolResult(
                            tool=(c.tool or "").strip(),
                            tool_call_id=c.tool_call_id,
                            safe_result=SafeTool.Failure(
                                content=f"Tool not allowed in this subgraph: {c.tool}",
                                message=f"Tool not allowed in this subgraph: {c.tool}",
                            ),
                        )
                    ]
            if not parallel_tools:
                return self._env(_ctx).execute_tools(tool_calls)
            return self._env(_ctx).execute_tools_parallel(tool_calls, max_concurrency=16)

        return self.node(name, _run)

    def node_llm_send_tool_result(self, name: str) -> Node[ReceivedToolResult, ResponseMessage]:
        def _run(_ctx: GraphContext, result: ReceivedToolResult) -> ResponseMessage:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.prompt.append(
                ToolResultMessage(tool=result.tool, tool_call_id=result.tool_call_id, result=result.safe_result.content)
            )
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_call_starting(
                ctx=_ctx,
                prompt=session.prompt,
                model=llm.default_model,
                tools=session.llm_tools,
                tool_choice=ToolChoice.AUTO,
                params=dict(llm.default_params),
            )
            resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.AUTO)
            pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=resp)
            session.prompt.append(*resp.responses)
            return resp.responses[0]

        return self.node(name, _run)

    def node_llm_send_multiple_tool_results(self, name: str) -> Node[List[ReceivedToolResult], List[ResponseMessage]]:
        def _run(_ctx: GraphContext, results: List[ReceivedToolResult]) -> List[ResponseMessage]:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            for r in results:
                session.prompt.append(
                    ToolResultMessage(tool=r.tool, tool_call_id=r.tool_call_id, result=r.safe_result.content)
                )
            # Minimal "multiple": do a single call and return all response messages.
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_call_starting(
                ctx=_ctx,
                prompt=session.prompt,
                model=llm.default_model,
                tools=session.llm_tools,
                tool_choice=ToolChoice.AUTO,
                params=dict(llm.default_params),
            )
            resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.AUTO)
            pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=resp)
            session.prompt.append(*resp.responses)
            return list(resp.responses)

        return self.node(name, _run)

    def node_llm_request_multiple(self, name: str, *, count: int = 2) -> Node[str, List[ResponseMessage]]:
        """
        Koog requestLLMMultiple() (minimal): performs `count` independent LLM calls and returns a flattened list.
        """

        def _run(_ctx: GraphContext, message: str) -> List[ResponseMessage]:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.append_user(message)
            all_responses: List[ResponseMessage] = []
            for _ in range(max(1, int(count))):
                pipeline = self._pipeline(_ctx)
                pipeline.on_llm_called(ctx=_ctx)
                pipeline.on_llm_call_starting(
                    ctx=_ctx,
                    prompt=session.prompt,
                    model=llm.default_model,
                    tools=session.llm_tools,
                    tool_choice=ToolChoice.AUTO,
                    params=dict(llm.default_params),
                )
                resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.AUTO)
                pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=resp)
                session.prompt.append(*resp.responses)
                all_responses.extend(list(resp.responses))
            return all_responses

        return self.node(name, _run)

    def node_execute_multiple_tools_and_send_results(
        self,
        name: str,
        *,
        parallel_tools: bool = False,
        max_concurrency: int = 16,
        responses_count: int = 2,
    ) -> Node[List[ToolCallMessage], List[ResponseMessage]]:
        def _run(ctx: GraphContext, tool_calls: List[ToolCallMessage]) -> List[ResponseMessage]:
            session = self._session(ctx)
            llm = self._llm(ctx)
            env = self._env(ctx)
            pipeline = self._pipeline(ctx)
            if not parallel_tools:
                results = env.execute_tools(tool_calls)
            else:
                results = env.execute_tools_parallel(tool_calls, max_concurrency=max_concurrency)
            for r in results:
                ok = isinstance(r.safe_result, SafeTool.Success)
                pipeline.on_tool_executed(tool=r.tool, ok=ok, ctx=ctx)
                # Best-effort tool-call completion event per result (we don't have the original args here).
                pipeline.on_tool_call_completed(
                    ctx=ctx,
                    tool_call_id=r.tool_call_id,
                    tool=r.tool,
                    args={},
                    ok=ok,
                    result=r.safe_result,
                )
                session.prompt.append(
                    ToolResultMessage(tool=r.tool, tool_call_id=r.tool_call_id, result=r.safe_result.content)
                )

            # Minimal multiple: multiple independent calls
            all_responses: List[ResponseMessage] = []
            for _ in range(max(1, int(responses_count))):
                pipeline.on_llm_called(ctx=ctx)
                pipeline.on_llm_call_starting(
                    ctx=ctx,
                    prompt=session.prompt,
                    model=llm.default_model,
                    tools=session.llm_tools,
                    tool_choice=ToolChoice.AUTO,
                    params=dict(llm.default_params),
                )
                resp = llm.invoke(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.AUTO)
                pipeline.on_llm_call_completed(ctx=ctx, prompt=session.prompt, model=llm.default_model, response=resp)
                session.prompt.append(*resp.responses)
                all_responses.extend(list(resp.responses))
            return all_responses

        return self.node(name, _run)

    def node_execute_single_tool(
        self,
        name: str,
        *,
        tool_name: str,
        do_append_prompt: bool = True,
    ) -> Node[dict, SafeTool.Result[Any]]:
        """
        Koog nodeExecuteSingleTool (minimal): call a tool directly from args dict.
        """

        def _run(_ctx: GraphContext, tool_args: dict) -> SafeTool.Result[Any]:
            session = self._session(_ctx)
            env = self._env(_ctx)
            if not is_tool_allowed(_ctx, tool_name):
                res = SafeTool.Failure(
                    content=f"Tool not allowed in this subgraph: {tool_name}",
                    message=f"Tool not allowed in this subgraph: {tool_name}",
                )
                self._pipeline(_ctx).on_tool_executed(tool=tool_name, ok=False, ctx=_ctx)
                return res
            if do_append_prompt:
                session.prompt.append(
                    UserMessage(text=f"Tool call: {tool_name} was explicitly called with args: {tool_args}")
                )
            tr = env.execute_tool(ToolCallMessage(tool=tool_name, args=dict(tool_args or {})))
            ok = isinstance(tr.safe_result, SafeTool.Success)
            self._pipeline(_ctx).on_tool_executed(tool=tr.tool, ok=ok, ctx=_ctx)
            if do_append_prompt:
                session.prompt.append(
                    UserMessage(text=f"Tool call: {tool_name} returned result: {tr.safe_result.content}")
                )
            return tr.safe_result

        return self.node(name, _run)

    def node_set_llm_tools(self, name: str, tools: Sequence[Any]) -> Node[Any, Any]:
        """
        Minimal equivalent of Koog's nodeSetStructuredOutput: configure which tools the LLM can call.
        """

        def _run(_ctx: GraphContext, input_value: Any) -> Any:
            self._session(_ctx).llm_tools = list(tools)
            return input_value

        return self.node(name, _run)

    def node_llm_request_structured(
        self,
        name: str,
        *,
        schema: Optional[dict] = None,
        schema_name: str = "StructuredOutput",
        model: Any = None,
        examples: Optional[Sequence[Any]] = None,
        fixing_parser_model: Any = None,
        fixing_parser_retries: int = 3,
    ) -> Node[str, StructuredResult[Any]]:
        """
        Koog-parity structured request at the node layer.

        Kotlin reference: structured output supports executor/session/node layers.
        In Python, this node:
        - appends user message into the shared session prompt
        - calls `llm.invoke_structured(...)` (schema-based; not tool-calling)
        - appends the resulting assistant text into the prompt for continuity

        Inputs:
        - **schema**: explicit JSON schema dict (standard flavor).
        - **model**: optional pydantic model; if provided and schema not set, we'll use `model.model_json_schema()`.
        - **examples**: optional examples to help the model format output.
        - **fixing_parser_model**: optional model override used for fixing retries.
        """

        from .messages import AssistantMessage
        from .structured import JsonSchema, StructureFixingParser

        def _run(_ctx: GraphContext, message: str) -> StructuredResult[Any]:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.append_user(message)
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_called(ctx=_ctx)
            pipeline.on_llm_call_starting(
                ctx=_ctx,
                prompt=session.prompt,
                model=llm.default_model,
                tools=session.llm_tools,
                tool_choice="structured",
                params=dict(llm.default_params),
            )

            schema_dict: Optional[dict] = schema
            if schema_dict is None and model is not None:
                mjs = getattr(model, "model_json_schema", None)
                if callable(mjs):
                    try:
                        maybe = mjs()
                        schema_dict = maybe if isinstance(maybe, dict) else None
                    except Exception:
                        schema_dict = None
            if schema_dict is None:
                schema_dict = {"type": "object", "properties": {}, "additionalProperties": True}

            fixing = None
            if fixing_parser_model is not None and fixing_parser_retries > 0:
                fixing = StructureFixingParser(model=fixing_parser_model, retries=int(fixing_parser_retries))

            res = llm.invoke_structured(
                session.prompt,
                schema=JsonSchema(name=schema_name, schema=dict(schema_dict), strict=True),
                examples=examples,
                fixing_parser=fixing,
            )
            pipeline.on_llm_call_completed(ctx=_ctx, prompt=session.prompt, model=llm.default_model, response=res)

            # Keep session prompt in sync with Koog session semantics: append assistant text if available.
            if res.text:
                session.prompt.append(AssistantMessage(text=res.text))
            return res

        return self.node(name, _run)

    def node_llm_moderate_message(self, name: str) -> Node[str, dict]:
        """
        Koog nodeLLMModerateMessage: returns an OpenAI Moderations API payload.
        """

        def _run(ctx: GraphContext, message: str) -> dict:
            self._pipeline(ctx).on_llm_called(ctx=ctx)
            return self._llm(ctx).moderate_message(message)

        return self.node(name, _run)

    def node_llm_request_streaming(self, name: str) -> Node[str, Any]:
        """
        Koog nodeLLMRequestStreaming: returns an iterator of StreamFrame(s).
        """

        def _run(_ctx: GraphContext, message: str) -> Any:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.append_user(message)
            pipeline = self._pipeline(_ctx)
            pipeline.on_llm_streaming_starting(ctx=_ctx, prompt=session.prompt, model=llm.default_model, tools=session.llm_tools)
            try:
                return llm.invoke_streaming(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.AUTO)
            except Exception as e:
                pipeline.on_llm_streaming_failed(ctx=_ctx, error=e)
                raise

        return self.node(name, _run)

    def node_llm_request_streaming_and_send_results(self, name: str) -> Node[str, List[ResponseMessage]]:
        """
        Koog nodeLLMRequestStreamingAndSendResults:
        - streams frames
        - collects assistant text
        - appends the final assistant message to the prompt
        - returns the collected response messages
        """

        from .streaming import StreamFrame
        import json

        def _run(_ctx: GraphContext, message: str) -> List[ResponseMessage]:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            env = self._env(_ctx)
            pipeline = self._pipeline(_ctx)

            # Koog write-session semantics: always keep prompt history continuous.
            session.append_user(message)

            max_tool_rounds = 8
            tool_round = 0

            while True:
                pipeline.on_llm_streaming_starting(
                    ctx=_ctx,
                    prompt=session.prompt,
                    model=llm.default_model,
                    tools=session.llm_tools,
                )
                try:
                    frames = llm.invoke_streaming(session.prompt, tools=session.llm_tools, tool_choice=ToolChoice.AUTO)
                except Exception as e:
                    pipeline.on_llm_streaming_failed(ctx=_ctx, error=e)
                    raise

                parts: List[str] = []
                tool_calls: List[ToolCallMessage] = []

                for fr in frames:
                    if not isinstance(fr, StreamFrame):
                        raise TypeError(f"Expected StreamFrame, got: {type(fr)!r}")
                    pipeline.on_llm_streaming_frame_received(ctx=_ctx, frame=fr)

                    if fr.type in ("text_delta", "append"):
                        parts.append(fr.content or "")
                        continue

                    if fr.type == "tool_call":
                        tool_name = (fr.tool_name or "").strip()
                        raw_args = fr.tool_args or "{}"
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else {}
                        except Exception:
                            args = {}
                        tool_calls.append(
                            ToolCallMessage(
                                tool=tool_name,
                                args=dict(args) if isinstance(args, dict) else {},
                                tool_call_id=fr.tool_call_id,
                            )
                        )
                        continue

                    if fr.type == "end":
                        break

                pipeline.on_llm_streaming_completed(ctx=_ctx)

                # If the streamed turn requests tools, execute them and continue streaming until we get assistant text.
                if tool_calls:
                    tool_round += 1
                    if tool_round > max_tool_rounds:
                        raise RuntimeError("Exceeded max_tool_rounds while handling streaming tool calls.")

                    # Append tool-call messages to history and emit events (OpenAI compatibility; safe for other providers).
                    for tc in tool_calls:
                        pipeline.on_tool_call_starting(
                            ctx=_ctx,
                            tool_call_id=tc.tool_call_id,
                            tool=(tc.tool or "").strip(),
                            args=dict(tc.args or {}),
                        )
                        if not is_tool_allowed(_ctx, (tc.tool or "").strip()):
                            err = RuntimeError(f"Tool not allowed in this subgraph: {tc.tool}")
                            pipeline.on_tool_validation_failed(
                                ctx=_ctx,
                                tool_call_id=tc.tool_call_id,
                                tool=(tc.tool or "").strip(),
                                args=dict(tc.args or {}),
                                error=err,
                            )
                            pipeline.on_tool_call_failed(
                                ctx=_ctx,
                                tool_call_id=tc.tool_call_id,
                                tool=(tc.tool or "").strip(),
                                args=dict(tc.args or {}),
                                error=err,
                            )
                            raise err
                        session.prompt.append(tc)

                    # Execute in parallel (Koog parity default: 16).
                    results = env.execute_tools_parallel(tool_calls, max_concurrency=16)
                    for r in results:
                        ok = isinstance(r.safe_result, SafeTool.Success)
                        pipeline.on_tool_executed(tool=r.tool, ok=ok, ctx=_ctx)
                        pipeline.on_tool_call_completed(
                            ctx=_ctx,
                            tool_call_id=r.tool_call_id,
                            tool=r.tool,
                            args={},
                            ok=ok,
                            result=r.safe_result,
                        )
                        session.prompt.append(
                            ToolResultMessage(tool=r.tool, tool_call_id=r.tool_call_id, result=r.safe_result.content)
                        )

                    # Next streamed request uses updated prompt.
                    continue

                # Otherwise finalize assistant text (single assistant message for continuity).
                text = "".join(parts).strip()
                if not text:
                    raise RuntimeError("Streaming produced no assistant text and no tool calls.")
                msgs: List[ResponseMessage] = [AssistantMessage(text=text)]
                session.prompt.append(*msgs)
                return msgs

        return self.node(name, _run)

    def node_llm_compress_history(
        self,
        name: str,
        *,
        strategy: Optional[HistoryCompressionStrategy] = None,
        preserve_memory: bool = True,
    ) -> Node[Any, Any]:
        strat = strategy or WholeHistory()

        def _run(_ctx: GraphContext, input_value: Any) -> Any:
            session = self._session(_ctx)
            llm = self._llm(_ctx)
            session.prompt = strat.compress(session.prompt, llm, preserve_memory=preserve_memory)
            return input_value

        return self.node(name, _run)


def agent_strategy(
    name: str,
    *,
    llm: LLMExecutor,
    environment: AgentEnvironment,
    session: Optional[AgentSession] = None,
    tool_selection_strategy: ToolSelectionStrategy = ALL(),
) -> AgentStrategyBuilder:
    base = base_strategy(name)
    return AgentStrategyBuilder(
        base=base,
        llm=llm,
        environment=environment,
        session=session or AgentSession(),
        tool_selection_strategy=tool_selection_strategy,
    )


