from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, get_type_hints

from ..tools import DictTool, Tool, ToolDescriptor
from .schema import schema_from_signature

TResult = TypeVar("TResult")


def tool(
    *,
    name: Optional[str] = None,
    description: str = "",
    input_schema: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., TResult]], Tool[Any, TResult]]:
    """
    Koog-like annotation-based tools (Python decorator).

    Usage:

    - Single-arg "args object" style:
        @tool(name="echo")
        def echo(args: dict[str, Any]) -> str:
            return str(args.get("text", ""))

    - Multi-arg style:
        @tool()
        def add(a: int, b: int) -> int:
            return a + b

    Notes:
    - Under the hood we create a `DictTool` so it plugs into existing ToolRegistry/tool-calling.
    - JSON schema is generated from python type hints unless explicitly provided.
    """

    def _decorate(fn: Callable[..., TResult]) -> Tool[Any, TResult]:
        tool_name = (name or fn.__name__ or "").strip()
        if not tool_name:
            raise ValueError("Tool name cannot be empty")

        schema = input_schema if isinstance(input_schema, dict) else schema_from_signature(fn)

        desc = ToolDescriptor(
            name=tool_name,
            description=(description or (inspect.getdoc(fn) or "")).strip(),
            input_schema=schema,
        )

        sig = inspect.signature(fn)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        hints = get_type_hints(fn)

        def _call(raw: Dict[str, Any]) -> TResult:
            raw2 = dict(raw or {})
            if len(params) == 0:
                return fn()  # type: ignore[misc]
            if len(params) == 1:
                p = params[0]
                tp = hints.get(p.name, Any)
                # If param is dict-like, pass the whole raw dict.
                origin = getattr(tp, "__origin__", None)
                if tp in (dict, Dict) or origin in (dict, Dict) or tp is Any or tp is object:
                    return fn(raw2)  # type: ignore[misc]
                # Otherwise pass a single value from raw under param name.
                return fn(raw2.get(p.name))  # type: ignore[misc]

            kwargs = {p.name: raw2.get(p.name) for p in params}
            return fn(**kwargs)  # type: ignore[misc]

        return DictTool(descriptor=desc, fn=_call)

    return _decorate


@dataclass(frozen=True)
class ClassTool(Generic[TResult]):
    """
    Convenience base for class-based tools.

    Subclasses implement `run(self, args: dict[str, Any]) -> TResult`.
    """

    descriptor: ToolDescriptor

    def run(self, args: Dict[str, Any]) -> TResult:
        raise NotImplementedError

    def __call__(self, args: Dict[str, Any]) -> TResult:
        return self.run(dict(args or {}))

    def decode_args(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return dict(raw or {})

    def encode_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return dict(args or {})

