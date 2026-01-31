from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

from .core import (
    Edge,
    EdgeBuilderIntermediate,
    FinishNode,
    GraphContext,
    Node,
    NodeBase,
    ParallelNodeExecutionResult,
    ParallelResult,
    StartNode,
    Strategy,
    Subgraph,
    SubgraphMetadata,
)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


def _is_finish_reachable(start: NodeBase[Any, Any], finish: NodeBase[Any, Any]) -> bool:
    visited: Set[NodeBase[Any, Any]] = set()

    def visit(node: NodeBase[Any, Any]) -> bool:
        if node is finish:
            return True
        if node in visited:
            return False
        visited.add(node)
        return any(visit(e.to_node) for e in node.edges)

    return visit(start)


def _build_nodes_map(start: StartNode[Any], parent_path: str) -> Dict[str, NodeBase[Any, Any]]:
    """
    Build a fully-qualified node-path map, mirroring Koog's metadata traversal.
    - Start/Finish are technical nodes and are not included as named paths.
    - Subgraphs recursively contribute their nested paths.
    """
    out: Dict[str, NodeBase[Any, Any]] = {}

    def node_path(node: NodeBase[Any, Any], parent: str) -> str:
        return f"{parent}/{node.name}"

    def visit(node: NodeBase[Any, Any], parent: str) -> None:
        # Stop at finish; it doesn't contribute further nodes.
        if isinstance(node, FinishNode):
            return

        if not isinstance(node, StartNode):
            p = node_path(node, parent)
            existing = out.get(p)
            if existing is not None:
                # If we reached the same node again via a cycle, just stop recursion.
                if existing is node:
                    return
                # Otherwise, this is a true duplicate name under the same parent path.
                raise RuntimeError(f"Node with name {node.name!r} already exists in the subgraph.")
            out[p] = node

            # If the node is a subgraph, recurse into its start with this node's path as parent.
            if isinstance(node, Subgraph):
                visit(node.start, p)

        for e in node.edges:
            visit(e.to_node, parent)

    visit(start, parent_path)
    return out


@dataclass
class StrategyBuilder(Generic[TInput, TOutput]):
    name: str
    node_start: StartNode[TInput]
    node_finish: FinishNode[TOutput]
    _built: bool = False

    def node(self, name: str, fn: Callable[[Any, Any], Any]) -> Node[Any, Any]:
        # fn signature is (ctx, input) -> output
        return Node(name=name, fn=fn)

    def subgraph(self, name: str) -> "SubgraphBuilder[Any, Any]":
        return SubgraphBuilder(name=name, node_start=StartNode(), node_finish=FinishNode())

    def edge(self, intermediate: EdgeBuilderIntermediate[Any, Any, Any]) -> None:
        edge = intermediate.build()
        intermediate.from_node.add_edge(edge)

    def parallel(
        self,
        name: str,
        *nodes: NodeBase[Any, Any],
        merge: Callable[[GraphContext, List[ParallelResult[Any, Any]]], ParallelNodeExecutionResult[Any]],
        max_workers: Optional[int] = None,
    ) -> Node[Any, Any]:
        """
        Koog-like parallel node execution:
        - runs provided nodes in parallel using isolated forked contexts
        - `merge(ctx, results)` decides which output/context becomes the resulting node output/context
        """
        import concurrent.futures

        def _run(ctx: GraphContext, input_value: Any) -> Any:
            results: List[ParallelResult[Any, Any]] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = []
                for n in nodes:
                    node_ctx = ctx.fork_isolated()
                    futs.append((n, node_ctx, ex.submit(n.execute, node_ctx, input_value)))

                for n, node_ctx, fut in futs:
                    out = fut.result()
                    # Koog parity: checkpoints / execution-point jumps are NOT supported from parallel execution.
                    if node_ctx.get_agent_context_data() is not None:
                        raise RuntimeError(
                            f"Checkpoints are not supported in parallel execution. Node: {n.name}"
                        )
                    results.append(
                        ParallelResult(
                            node_name=n.name,
                            node_input=input_value,
                            node_result=ParallelNodeExecutionResult(output=out, context=node_ctx),
                        )
                    )

            merged = merge(ctx, results)
            # Replace outer context with merged context (Koog: context.replace(result.context))
            ctx.replace_from(merged.context)
            return merged.output

        return Node(name=name, fn=_run)

    def build(self) -> Strategy[TInput, TOutput]:
        if self._built:
            raise RuntimeError("StrategyBuilder.build() can only be called once.")

        if not _is_finish_reachable(self.node_start, self.node_finish):
            raise RuntimeError(f"Finish node is not reachable from start in strategy {self.name!r}.")

        strategy = Strategy(name=self.name, start=self.node_start, finish=self.node_finish)

        nodes_map = _build_nodes_map(self.node_start, self.name)
        # Koog includes the strategy itself at key == strategyName
        nodes_map[self.name] = strategy

        # Uniqueness rule: all node names should be unique within a strategy
        # (Koog uses a stricter rule to support checkpointing).
        all_names: List[str] = [n.name for n in nodes_map.values()]
        unique_names = len(set(all_names)) == len(all_names)

        strategy.metadata = SubgraphMetadata(nodes_map=nodes_map, unique_names=unique_names)
        self._built = True
        return strategy


@dataclass
class SubgraphBuilder(Generic[TInput, TOutput]):
    name: str
    node_start: StartNode[TInput]
    node_finish: FinishNode[TOutput]

    def __post_init__(self) -> None:
        self.node_start = StartNode(subgraph_name=self.name)
        self.node_finish = FinishNode(subgraph_name=self.name)

    def node(self, name: str, fn: Callable[[Any, Any], Any]) -> Node[Any, Any]:
        return Node(name=name, fn=fn)

    def edge(self, intermediate: EdgeBuilderIntermediate[Any, Any, Any]) -> None:
        edge = intermediate.build()
        intermediate.from_node.add_edge(edge)

    def parallel(
        self,
        name: str,
        *nodes: NodeBase[Any, Any],
        merge: Callable[[GraphContext, List[ParallelResult[Any, Any]]], ParallelNodeExecutionResult[Any]],
        max_workers: Optional[int] = None,
    ) -> Node[Any, Any]:
        import concurrent.futures

        def _run(ctx: GraphContext, input_value: Any) -> Any:
            results: List[ParallelResult[Any, Any]] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = []
                for n in nodes:
                    node_ctx = ctx.fork_isolated()
                    futs.append((n, node_ctx, ex.submit(n.execute, node_ctx, input_value)))

                for n, node_ctx, fut in futs:
                    out = fut.result()
                    results.append(
                        ParallelResult(
                            node_name=n.name,
                            node_input=input_value,
                            node_result=ParallelNodeExecutionResult(output=out, context=node_ctx),
                        )
                    )

            merged = merge(ctx, results)
            ctx.replace_from(merged.context)
            return merged.output

        return Node(name=name, fn=_run)

    def build(self) -> Subgraph[TInput, TOutput]:
        if not _is_finish_reachable(self.node_start, self.node_finish):
            raise RuntimeError(f"Finish node is not reachable from start in subgraph {self.name!r}.")
        return Subgraph(name=self.name, start=self.node_start, finish=self.node_finish)


def strategy(name: str) -> StrategyBuilder[Any, Any]:
    """
    Koog-like entrypoint:
      s = strategy("my-strategy")
      ... define nodes/edges ...
      strat = s.build()
    """
    return StrategyBuilder(name=name, node_start=StartNode(), node_finish=FinishNode())


