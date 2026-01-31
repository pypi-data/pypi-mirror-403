from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Protocol, TypeVar, cast, runtime_checkable

from .option import Empty, Option, Some

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TIncomingOutput = TypeVar("TIncomingOutput")
TIntermediateOutput = TypeVar("TIntermediateOutput")
TOutgoingInput = TypeVar("TOutgoingInput")


class GraphStuckInNodeError(RuntimeError):
    """Raised when a node produces an output but no outgoing edge matches (and it's not the finish node)."""


class GraphMaxIterationsReachedError(RuntimeError):
    """Raised when graph execution exceeds the max-iterations guard."""


_KOOG_AGENT_CONTEXT_DATA_KEY = "__koog_agent_context_data__"
_KOOG_EXECUTION_STACK_KEY = "__koog_execution_stack__"
_KOOG_PIPELINE_KEY = "__koog_pipeline__"


@dataclass
class GraphConfig:
    """
    Minimal config mirroring the Koog max-iterations guard.
    """

    max_iterations: int = 1000


@dataclass
class StateManager:
    iterations: int = 0


@dataclass
class GraphContext:
    """
    Minimal execution context.

    This is intentionally lightweight but keeps the same extension points Koog uses:
    - config + state manager for max-iteration enforcement
    - storage for features/checkpoint metadata
    - root/child relation for subgraphs and parallel forks
    """

    config: GraphConfig = field(default_factory=GraphConfig)
    state_manager: StateManager = field(default_factory=StateManager)
    storage: Dict[str, Any] = field(default_factory=dict)
    parent: Optional["GraphContext"] = None

    def root(self) -> "GraphContext":
        ctx: GraphContext = self
        while ctx.parent is not None:
            ctx = ctx.parent
        return ctx

    def fork(self) -> "GraphContext":
        # Subgraphs in Koog share the same *root* context; `fork()` keeps parent linkage.
        return GraphContext(
            config=self.config,
            state_manager=StateManager(iterations=self.state_manager.iterations),
            storage=dict(self.storage),
            parent=self,
        )

    def fork_isolated(self) -> "GraphContext":
        """
        Fork an isolated context (used for parallel execution).
        Unlike `fork()`, this fork does NOT share a root with the parent.
        """
        return GraphContext(
            config=self.config,
            state_manager=StateManager(iterations=self.state_manager.iterations),
            storage=dict(self.storage),
            parent=None,
        )

    def replace_from(self, other: "GraphContext") -> None:
        """
        Replace the mutable parts of this context (storage + state_manager) with another context.
        """
        self.storage = dict(other.storage)
        self.state_manager = StateManager(iterations=other.state_manager.iterations)

    def store(self, key: str, value: Any) -> None:
        self.root().storage[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.root().storage.get(key, default)

    def remove(self, key: str) -> bool:
        root = self.root()
        if key in root.storage:
            del root.storage[key]
            return True
        return False

    # -----------------------------
    # Koog-style execution helpers
    # -----------------------------

    def set_pipeline(self, pipeline: Any) -> None:
        """
        Attach a pipeline-like object (features/interceptors) to the root context.
        """
        self.store(_KOOG_PIPELINE_KEY, pipeline)

    def get_pipeline(self) -> Any:
        return self.get(_KOOG_PIPELINE_KEY, None)

    def store_agent_context_data(self, data: Any) -> None:
        """
        Store Koog-like "forced context data" (used for checkpoints / execution-point jumps).
        """
        self.store(_KOOG_AGENT_CONTEXT_DATA_KEY, data)

    def get_agent_context_data(self) -> Any:
        return self.get(_KOOG_AGENT_CONTEXT_DATA_KEY, None)

    def remove_agent_context_data(self) -> bool:
        return self.remove(_KOOG_AGENT_CONTEXT_DATA_KEY)

    def _execution_stack(self) -> List[str]:
        root = self.root()
        stack = root.storage.get(_KOOG_EXECUTION_STACK_KEY)
        if not isinstance(stack, list):
            stack = []
            root.storage[_KOOG_EXECUTION_STACK_KEY] = stack
        return cast(List[str], stack)

    def set_execution_stack(self, parts: List[str]) -> None:
        self.root().storage[_KOOG_EXECUTION_STACK_KEY] = list(parts)

    def execution_path(self) -> str:
        """
        Fully-qualified node path, compatible with `Strategy.set_execution_point(...)`:
          "<strategy>/<subgraph>/.../<node>"

        Note: technical Start/Finish nodes should NOT be pushed into the execution stack.
        """
        stack = self._execution_stack()
        return "/".join([p for p in stack if p])

    @contextmanager
    def push_execution_part(self, part: str) -> Iterator[None]:
        """
        Push a node/subgraph name onto the execution stack for the duration of a block.
        """
        stack = self._execution_stack()
        stack.append(part)
        try:
            yield
        finally:
            if stack and stack[-1] == part:
                stack.pop()
            else:
                # Defensive: if the stack was mutated unexpectedly, don't crash execution.
                try:
                    stack.remove(part)
                except ValueError:
                    pass


@dataclass(frozen=True)
class SubgraphMetadata:
    """
    Mirrors Koog's SubgraphMetadata at a high level:
    - nodes_map: fully qualified node path -> node instance
    - unique_names: whether all node names are unique within a strategy (required for checkpointing)
    """

    nodes_map: Dict[str, "NodeBase[Any, Any]"]
    unique_names: bool


@runtime_checkable
class ExecutionPointNode(Protocol):
    def get_execution_point(self) -> Optional["ExecutionPoint"]: ...

    def reset_execution_point(self) -> None: ...

    def enforce_execution_point(self, node: "NodeBase[Any, Any]", input_value: Any = None) -> None: ...


@dataclass(frozen=True)
class ExecutionPoint:
    node: "NodeBase[Any, Any]"
    input_value: Any = None


class NodeBase(ABC, Generic[TInput, TOutput]):
    """
    Koog-like node base:
    - `execute(...)` produces an output
    - `edges` are resolved in order; the first edge producing Some(...) is taken
    """

    def __init__(self, name: str):
        self.name = name
        self._edges: List["Edge[TOutput, Any]"] = []

    @property
    def edges(self) -> List["Edge[TOutput, Any]"]:
        return list(self._edges)

    def add_edge(self, edge: "Edge[TOutput, Any]") -> None:
        self._edges.append(edge)

    def forward_to(self, other: "NodeBase[Any, Any]") -> "EdgeBuilderIntermediate[TOutput, TOutput, Any]":
        return EdgeBuilderIntermediate(
            from_node=self,
            to_node=other,
            forward_output_composition=lambda _ctx, out: Some(out),
        )

    def resolve_edge(self, ctx: GraphContext, node_output: TOutput) -> Optional[tuple["Edge[Any, Any]", Any]]:
        for e in self._edges:
            opt = e.forward_output(ctx, node_output)
            if not opt.is_empty:
                return e, opt.value
        return None

    @abstractmethod
    def execute(self, ctx: GraphContext, input_value: TInput) -> Optional[TOutput]:
        raise AssertionError("abstract")


class Node(NodeBase[TInput, TOutput]):
    def __init__(self, name: str, fn: Callable[[GraphContext, TInput], TOutput]):
        super().__init__(name=name)
        self._fn = fn

    def execute(self, ctx: GraphContext, input_value: TInput) -> TOutput:
        return self._fn(ctx, input_value)


class StartNode(NodeBase[TInput, TInput]):
    def __init__(self, subgraph_name: Optional[str] = None):
        super().__init__(name=f"__start__{subgraph_name}" if subgraph_name else "__start__")

    def execute(self, ctx: GraphContext, input_value: TInput) -> TInput:
        return input_value


class FinishNode(NodeBase[TOutput, TOutput]):
    def __init__(self, subgraph_name: Optional[str] = None):
        super().__init__(name=f"__finish__{subgraph_name}" if subgraph_name else "__finish__")

    def add_edge(self, edge: "Edge[TOutput, Any]") -> None:
        raise RuntimeError("FinishNode cannot have outgoing edges")

    def execute(self, ctx: GraphContext, input_value: TOutput) -> TOutput:
        return input_value


class Edge(Generic[TIncomingOutput, TOutgoingInput]):
    def __init__(
        self,
        to_node: NodeBase[TOutgoingInput, Any],
        forward_output: Callable[[GraphContext, TIncomingOutput], Option[TOutgoingInput]],
        *,
        label: str = "onCondition",
    ):
        self.to_node = to_node
        self._forward_output = forward_output
        self.label = label

    def forward_output(self, ctx: GraphContext, output: TIncomingOutput) -> Option[TOutgoingInput]:
        return self._forward_output(ctx, output)


class EdgeBuilderIntermediate(Generic[TIncomingOutput, TIntermediateOutput, TOutgoingInput]):
    """
    Mirrors Koog's AIAgentEdgeBuilderIntermediate:
    - `on_condition` filters whether the edge is taken
    - `transformed` maps the forwarded value
    """

    def __init__(
        self,
        *,
        from_node: NodeBase[Any, TIncomingOutput],
        to_node: NodeBase[TOutgoingInput, Any],
        forward_output_composition: Callable[[GraphContext, TIncomingOutput], Option[TIntermediateOutput]],
        label: str = "onCondition",
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.forward_output_composition = forward_output_composition
        self.label = label

    def on_condition(
        self,
        predicate: Callable[[GraphContext, TIntermediateOutput], bool],
        *,
        label: str = "onCondition",
    ) -> "EdgeBuilderIntermediate[TIncomingOutput, TIntermediateOutput, TOutgoingInput]":
        def _f(ctx: GraphContext, out: TIncomingOutput) -> Option[TIntermediateOutput]:
            return self.forward_output_composition(ctx, out).filter(lambda v: predicate(ctx, v))

        return EdgeBuilderIntermediate(
            from_node=self.from_node,
            to_node=self.to_node,
            forward_output_composition=_f,
            label=label,
        )

    def transformed(
        self,
        mapper: Callable[[GraphContext, TIntermediateOutput], TOutgoingInput],
        *,
        label: str = "transformed",
    ) -> "EdgeBuilderIntermediate[TIncomingOutput, TOutgoingInput, TOutgoingInput]":
        def _f(ctx: GraphContext, out: TIncomingOutput) -> Option[TOutgoingInput]:
            return self.forward_output_composition(ctx, out).map(lambda v: mapper(ctx, v))

        return EdgeBuilderIntermediate(
            from_node=self.from_node,
            to_node=self.to_node,
            forward_output_composition=_f,
            label=label,
        )

    def build(self) -> Edge[TIncomingOutput, TOutgoingInput]:
        forward_output = cast(Callable[[GraphContext, TIncomingOutput], Option[TOutgoingInput]], self.forward_output_composition)
        return Edge(
            to_node=self.to_node,
            forward_output=forward_output,
            label=self.label,
        )


class Subgraph(NodeBase[TInput, TOutput], ExecutionPointNode):
    """
    Koog-like subgraph:
    - has a start + finish
    - runs a node/edge loop until it reaches finish
    - supports an "execution point" override (force a starting node + input)
    """

    def __init__(self, name: str, start: StartNode[TInput], finish: FinishNode[TOutput]):
        super().__init__(name=name)
        self.start = start
        self.finish = finish
        self._forced_node: Optional[NodeBase[Any, Any]] = None
        self._forced_input: Any = None

    def get_execution_point(self) -> Optional[ExecutionPoint]:
        if self._forced_node is None:
            return None
        return ExecutionPoint(self._forced_node, self._forced_input)

    def reset_execution_point(self) -> None:
        self._forced_node = None
        self._forced_input = None

    def enforce_execution_point(self, node: NodeBase[Any, Any], input_value: Any = None) -> None:
        if self._forced_node is not None:
            raise RuntimeError(f"Forced execution point already set to {self._forced_node.name}")
        self._forced_node = node
        self._forced_input = input_value

    def execute(self, ctx: GraphContext, input_value: TInput) -> Optional[TOutput]:
        current_node: NodeBase[Any, Any] = self.start
        current_input: Any = input_value

        ep = self.get_execution_point()
        if ep is not None:
            current_node = ep.node
            current_input = ep.input_value
            self.reset_execution_point()

        pipeline = ctx.get_pipeline()

        # Subgraph events (Koog parity): do not double-fire for top-level Strategy (it has its own events).
        is_top_strategy = isinstance(self, Strategy)
        if pipeline is not None and not is_top_strategy:
            on_sg_start = getattr(pipeline, "on_subgraph_execution_starting", None)
            if callable(on_sg_start):
                on_sg_start(ctx=ctx, subgraph=self, subgraph_input=input_value)

        try:
            while True:
                ctx.state_manager.iterations += 1
                if ctx.state_manager.iterations > ctx.config.max_iterations:
                    raise GraphMaxIterationsReachedError(f"Max iterations ({ctx.config.max_iterations}) reached")

                is_technical = isinstance(current_node, (StartNode, FinishNode))

                # Track execution path for checkpointing/debugging (Koog-like).
                exec_block = ctx.push_execution_part(current_node.name) if not is_technical else nullcontext()
                with exec_block:
                    node_path = ctx.execution_path()
                    if pipeline is not None:
                        on_start = getattr(pipeline, "on_node_execution_starting", None)
                        if callable(on_start):
                            on_start(ctx=ctx, node=current_node, node_path=node_path, node_input=current_input)

                    try:
                        node_output = current_node.execute(ctx, current_input)
                    except Exception as e:
                        if pipeline is not None:
                            on_fail = getattr(pipeline, "on_node_execution_failed", None)
                            if callable(on_fail):
                                on_fail(
                                    ctx=ctx,
                                    node=current_node,
                                    node_path=node_path,
                                    node_input=current_input,
                                    error=e,
                                    is_technical=is_technical,
                                )
                        raise

                    # Koog semantics: forced context data indicates an interruption (jump/rollback).
                    if ctx.get_agent_context_data() is not None:
                        return None

                    if pipeline is not None:
                        on_done = getattr(pipeline, "on_node_execution_completed", None)
                        if callable(on_done):
                            on_done(
                                ctx=ctx,
                                node=current_node,
                                node_path=node_path,
                                node_input=current_input,
                                node_output=node_output,
                                is_technical=is_technical,
                            )

                resolved = current_node.resolve_edge(ctx, node_output) if node_output is not None else None
                if resolved is None:
                    if current_node is self.finish:
                        if pipeline is not None and not is_top_strategy:
                            on_sg_done = getattr(pipeline, "on_subgraph_execution_completed", None)
                            if callable(on_sg_done):
                                on_sg_done(ctx=ctx, subgraph=self, subgraph_input=input_value, subgraph_output=node_output)
                        return node_output  # type: ignore[return-value]
                    raise GraphStuckInNodeError(f"Graph stuck in node {current_node.name} (no edge matched)")

                edge, next_input = resolved
                current_node = edge.to_node
                current_input = next_input
        except Exception as e:
            if pipeline is not None and not is_top_strategy:
                on_sg_fail = getattr(pipeline, "on_subgraph_execution_failed", None)
                if callable(on_sg_fail):
                    on_sg_fail(ctx=ctx, subgraph=self, subgraph_input=input_value, error=e)
            raise


class Strategy(Subgraph[TInput, TOutput]):
    """
    Top-level strategy == a named subgraph.
    """

    metadata: Optional[SubgraphMetadata] = None

    def execute(self, ctx: GraphContext, input_value: TInput) -> Optional[TOutput]:
        """
        Koog-like strategy execution wrapper:
        - initialize execution path root
        - allow features/pipeline to restore state at strategy start
        - if an interruption occurs (agent context data stored), restore and re-run
        """
        if not ctx.execution_path():
            ctx.set_execution_stack([self.name])

        pipeline = ctx.get_pipeline()
        if pipeline is not None:
            on_start = getattr(pipeline, "on_strategy_starting", None)
            if callable(on_start):
                on_start(ctx=ctx, strategy=self)

        # Restore state if a feature placed AgentContextData into the context.
        data = ctx.get_agent_context_data()
        if data is not None:
            apply_fn = getattr(data, "apply", None)
            if callable(apply_fn):
                apply_fn(ctx=ctx, strategy=self)
            ctx.remove_agent_context_data()

        result: Optional[TOutput] = super().execute(ctx, input_value)
        while result is None and ctx.get_agent_context_data() is not None:
            data = ctx.get_agent_context_data()
            apply_fn = getattr(data, "apply", None) if data is not None else None
            if callable(apply_fn):
                apply_fn(ctx=ctx, strategy=self)
            ctx.remove_agent_context_data()
            result = super().execute(ctx, input_value)

        if pipeline is not None:
            on_done = getattr(pipeline, "on_strategy_completed", None)
            if callable(on_done):
                on_done(ctx=ctx, strategy=self, result=result)

        return result

    def set_execution_point(self, node_path: str, input_value: Any) -> None:
        """
        Force the next execution to start from a specific nested node path, like Koog's `setExecutionPoint`.

        Path format:
          "<strategy>/<subgraph>/<subgraph>/.../<node>"
        """
        if not self.metadata:
            raise RuntimeError("Strategy metadata is not initialized (did you build via koog_strategy_graph.dsl.strategy?).")
        if not node_path or "/" not in node_path:
            raise ValueError(f"Invalid node_path: {node_path!r}")

        segments = [s for s in node_path.split("/") if s]
        strategy_name = segments[0]
        if strategy_name != self.name:
            raise ValueError(f"node_path must start with strategy name {self.name!r}, got: {strategy_name!r}")

        # Start at the first segment after strategy name.
        current: Optional[NodeBase[Any, Any]] = self.metadata.nodes_map.get(strategy_name)
        current_path = strategy_name

        for seg in segments[1:-1]:
            if current is None or not isinstance(current, ExecutionPointNode):
                raise RuntimeError(f"Restore failed at {current_path!r}: not a subgraph/execution-point node")
            current_path = f"{current_path}/{seg}"
            nxt = self.metadata.nodes_map.get(current_path)
            if nxt is None:
                raise KeyError(f"Node path not found: {current_path}")
            current.enforce_execution_point(nxt, input_value)
            current = nxt

        leaf_path = "/".join(segments)
        leaf = self.metadata.nodes_map.get(leaf_path)
        if leaf is None:
            raise KeyError(f"Leaf node path not found: {leaf_path}")
        if current is None or not isinstance(current, ExecutionPointNode):
            raise RuntimeError(f"Restore failed at {current_path!r}: not a subgraph/execution-point node")
        current.enforce_execution_point(leaf, input_value)


@dataclass(frozen=True)
class ParallelNodeExecutionResult(Generic[TOutput]):
    output: TOutput
    context: GraphContext


@dataclass(frozen=True)
class ParallelResult(Generic[TInput, TOutput]):
    node_name: str
    node_input: TInput
    node_result: ParallelNodeExecutionResult[TOutput]


