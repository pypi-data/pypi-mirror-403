from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Protocol, TypeVar, runtime_checkable

TArgs = TypeVar("TArgs")
TResult = TypeVar("TResult", covariant=True)


@dataclass(frozen=True)
class ToolDescriptor:
    """
    Minimal Koog-like descriptor.

    This is used both:
    - to describe tools to the LLM (name/description/schema), and
    - to look up an executable tool at runtime.
    """

    name: str
    description: str = ""
    input_schema: Optional[Dict[str, Any]] = None


class ToolExecutionError(RuntimeError):
    pass


class SafeTool:
    """
    Koog-like "safe tool" wrapper results.
    """

    @dataclass(frozen=True)
    class Result(Generic[TResult]):
        content: str

    @dataclass(frozen=True)
    class Success(Result[TResult]):
        result: TResult

    @dataclass(frozen=True)
    class Failure(Result[TResult]):
        message: str
        exception: Optional[BaseException] = None


@dataclass(frozen=True)
class ReceivedToolResult:
    """
    Koog-like tool execution envelope.
    """

    tool: str
    tool_call_id: Optional[str]
    safe_result: SafeTool.Result[Any]


@runtime_checkable
class Tool(Protocol[TArgs, TResult]):
    """
    Executable tool contract.

    - `descriptor` describes this tool to the LLM and to the registry.
    - `__call__` executes it with decoded args.
    """

    @property
    def descriptor(self) -> ToolDescriptor: ...

    def __call__(self, args: TArgs) -> TResult: ...

    def decode_args(self, raw: Dict[str, Any]) -> TArgs: ...

    def encode_args(self, args: TArgs) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class DictTool(Generic[TResult]):
    """
    A simple tool where args are a dict[str, Any].
    """

    descriptor: ToolDescriptor
    fn: Callable[[Dict[str, Any]], TResult]

    def __call__(self, args: Dict[str, Any]) -> TResult:
        return self.fn(args)

    def decode_args(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return dict(raw or {})

    def encode_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return dict(args or {})


class ToolRegistry:
    def __init__(self, tools: Optional[Iterable[Tool[Any, Any]]] = None):
        self._tools: Dict[str, Tool[Any, Any]] = {}
        if tools:
            for t in tools:
                self.register(t)

    def register(self, tool: Tool[Any, Any]) -> None:
        name = tool.descriptor.name
        if not name:
            raise ValueError("Tool name cannot be empty")
        self._tools[name] = tool

    def get(self, name: str) -> Optional[Tool[Any, Any]]:
        return self._tools.get(name)

    def require(self, name: str) -> Tool[Any, Any]:
        t = self.get(name)
        if t is None:
            raise KeyError(f"Tool not found: {name}")
        return t

    def descriptors(self) -> List[ToolDescriptor]:
        return [t.descriptor for t in self._tools.values()]


# -------------------------
# Ergonomic helper functions
# -------------------------
#
# These helpers are optional and purely additive. They exist to make it easy to build tools
# without manually writing a Tool class, similar to Koog's annotation/class-based tools.


def register_all(registry: ToolRegistry, *tools: Tool[Any, Any]) -> ToolRegistry:
    """
    Convenience: register multiple tools and return the registry (for chaining).
    """
    for t in tools:
        registry.register(t)
    return registry

