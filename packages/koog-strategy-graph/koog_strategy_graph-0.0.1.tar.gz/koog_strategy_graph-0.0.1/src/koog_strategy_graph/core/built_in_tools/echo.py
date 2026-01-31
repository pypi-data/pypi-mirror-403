from __future__ import annotations

from typing import Any, Dict

from ..tools import DictTool, ToolDescriptor


def echo_tool(*, name: str = "echo") -> DictTool[str]:
    """
    Deterministic echo tool (safe).
    Args schema: {"text": str}
    """

    desc = ToolDescriptor(
        name=name,
        description="Echo back the provided text.",
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": True,
        },
    )

    def _fn(args: Dict[str, Any]) -> str:
        return str((args or {}).get("text", ""))

    return DictTool(descriptor=desc, fn=_fn)

