from __future__ import annotations

from typing import Any

from ..tools import Tool, ToolRegistry


def register_all(registry: ToolRegistry, *tools: Tool[Any, Any]) -> ToolRegistry:
    """
    Convenience: register multiple tools and return the registry (for chaining).
    """
    for t in tools:
        registry.register(t)
    return registry

