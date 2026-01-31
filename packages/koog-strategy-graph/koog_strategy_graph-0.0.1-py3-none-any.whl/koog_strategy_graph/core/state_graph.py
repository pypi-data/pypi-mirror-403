from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Iterable, Iterator, Mapping, Optional, Type, TypeVar, cast

from .checkpoint_sqlite import SqliteCheckpointer

StateT = TypeVar("StateT", bound=Dict[str, Any])

# LangGraph compatibility: END sentinel
END = "__end__"


def _merge_state(state: Dict[str, Any], updates: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not updates:
        return state
    # LangGraph-style shallow merge; callers can store nested objects directly.
    state.update(dict(updates))
    return state


@dataclass
class CompiledStateGraph(Generic[StateT]):
    """
    Executable graph instance (LangGraph-like surface).
    """

    builder: "StateGraph[StateT]"
    checkpointer: Optional[SqliteCheckpointer] = None

    def stream(
        self,
        payload: Mapping[str, Any],
        *,
        config: Optional[Mapping[str, Any]] = None,
        stream_mode: str = "updates",
    ) -> Iterator[Dict[str, Dict[str, Any]]]:
        # stream_mode kept for API compatibility; only "updates" is implemented.
        _ = stream_mode

        thread_id = ""
        if config:
            configurable = config.get("configurable") or {}
            thread_id = str(configurable.get("thread_id") or "")

        # Load prior state (if any)
        state: Dict[str, Any] = {}
        if self.checkpointer and thread_id:
            loaded = self.checkpointer.load(thread_id)
            if loaded:
                state = loaded

        # Merge incoming payload (first run initializes, subsequent runs patch)
        _merge_state(state, payload)
        typed_state = cast(StateT, state)

        current = self.builder.entry_point
        if not current:
            raise ValueError("Graph has no entry point (call set_entry_point).")

        steps = 0
        while True:
            if current == END:
                break
            fn = self.builder.nodes.get(current)
            if fn is None:
                raise KeyError(f"Unknown node: {current}")

            updates = fn(typed_state)
            if updates is None:
                updates = {}
            if not isinstance(updates, dict):
                raise TypeError(f"Node '{current}' must return a dict of updates, got: {type(updates)}")

            _merge_state(state, updates)

            # Persist after every node so runs are resumable
            if self.checkpointer and thread_id:
                self.checkpointer.save(thread_id, state)

            yield {current: updates}

            # Route to next node
            next_node = self.builder._next_node(current, typed_state)
            if next_node is None:
                # If no edges match, end (mirrors LangGraph behavior where missing edge effectively halts)
                break
            current = next_node

            steps += 1
            if steps > self.builder.max_steps:
                raise RuntimeError(f"Max steps ({self.builder.max_steps}) reached; possible infinite loop.")


class StateGraph(Generic[StateT]):
    """
    Koog-inspired state-machine graph with a LangGraph-like builder API.

    This is intentionally minimal and meant to replace `langgraph.graph.StateGraph` for this repo.
    """

    def __init__(self, _state_type: Type[StateT], *, max_steps: int = 10_000):
        self._state_type = _state_type
        self.max_steps = max_steps
        self.nodes: Dict[str, Callable[[StateT], Dict[str, Any]]] = {}
        self.entry_point: str = ""
        self._edges: Dict[str, list[str]] = {}
        self._conditional_edges: Dict[str, list[tuple[Callable[[StateT], str], Dict[str, str]]]] = {}

    def add_node(self, name: str, fn: Callable[[StateT], Dict[str, Any]]) -> None:
        self.nodes[name] = fn

    def set_entry_point(self, name: str) -> None:
        self.entry_point = name

    def add_edge(self, from_node: str, to_node: str) -> None:
        self._edges.setdefault(from_node, []).append(to_node)

    def add_conditional_edges(
        self,
        from_node: str,
        router: Callable[[StateT], str],
        mapping: Dict[str, str],
    ) -> None:
        self._conditional_edges.setdefault(from_node, []).append((router, mapping))

    def _next_node(self, from_node: str, state: StateT) -> Optional[str]:
        # 1) conditional edges (evaluated in definition order)
        for router, mapping in self._conditional_edges.get(from_node, []):
            key = router(state)
            if key in mapping:
                return mapping[key]

        # 2) unconditional edges (first wins)
        outs = self._edges.get(from_node, [])
        if outs:
            return outs[0]
        return None

    def compile(self, *, checkpointer: Optional[SqliteCheckpointer] = None) -> CompiledStateGraph[StateT]:
        return CompiledStateGraph(builder=self, checkpointer=checkpointer)


