from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from ..tools import DictTool, ToolDescriptor


def utc_now_tool(*, name: str = "utc_now") -> DictTool[str]:
    """
    Returns current UTC timestamp in ISO8601 (safe).
    Args schema: {}
    """

    desc = ToolDescriptor(
        name=name,
        description="Return the current UTC time as an ISO8601 timestamp.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    )

    def _fn(_args: Dict[str, Any]) -> str:
        _ = _args
        return datetime.now(timezone.utc).isoformat()

    return DictTool(descriptor=desc, fn=_fn)

