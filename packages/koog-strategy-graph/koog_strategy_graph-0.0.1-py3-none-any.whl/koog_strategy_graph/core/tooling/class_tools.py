from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

from ..tools import ToolDescriptor

TResult = TypeVar("TResult")


@dataclass(frozen=True)
class SimpleClassTool(Generic[TResult]):
    """
    Minimal class-based tool base (Koog-style ergonomics).

    Subclasses should:
    - set `descriptor`
    - implement `run(self, args: dict[str, Any]) -> TResult`

    This type conforms to the `Tool` protocol used by `ToolRegistry`.
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

