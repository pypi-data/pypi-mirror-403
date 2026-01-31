from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .messages import ToolCallMessage
from .tools import ReceivedToolResult, SafeTool, ToolRegistry


@dataclass
class AgentEnvironment:
    """
    Koog-like environment:
    - owns the executable tool registry
    - provides safe tool execution helpers

    Note: LLM session/executor is implemented separately in `llm_executor.py`.
    """

    tools: ToolRegistry = field(default_factory=ToolRegistry)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def execute_tool(self, tool_call: ToolCallMessage) -> ReceivedToolResult:
        tool_name = (tool_call.tool or "").strip()
        if not tool_name:
            return ReceivedToolResult(
                tool=tool_name,
                tool_call_id=tool_call.tool_call_id,
                safe_result=SafeTool.Failure(content="Tool name missing", message="Tool name missing"),
            )

        try:
            tool = self.tools.require(tool_name)
        except Exception as e:
            return ReceivedToolResult(
                tool=tool_name,
                tool_call_id=tool_call.tool_call_id,
                safe_result=SafeTool.Failure(content=str(e), message=str(e), exception=e),
            )

        try:
            decoded = tool.decode_args(tool_call.args)
            result = tool(decoded)
            return ReceivedToolResult(
                tool=tool_name,
                tool_call_id=tool_call.tool_call_id,
                safe_result=SafeTool.Success(content=str(result), result=result),
            )
        except Exception as e:
            return ReceivedToolResult(
                tool=tool_name,
                tool_call_id=tool_call.tool_call_id,
                safe_result=SafeTool.Failure(content=str(e), message=str(e), exception=e),
            )

    def execute_tools(self, tool_calls: Iterable[ToolCallMessage]) -> List[ReceivedToolResult]:
        return [self.execute_tool(c) for c in tool_calls]

    def execute_tools_parallel(
        self,
        tool_calls: Iterable[ToolCallMessage],
        *,
        max_concurrency: int = 16,
    ) -> List[ReceivedToolResult]:
        """
        Execute tools concurrently (Koog parity: `toParallelToolCalls*` default concurrency is 16).

        Notes:
        - Uses threads because tools are synchronous in this implementation.
        - Returns results in the same order as inputs (stable), matching `execute_tools` semantics.
        """
        calls = list(tool_calls)
        if not calls:
            return []
        workers = max(1, min(int(max_concurrency), len(calls)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(self.execute_tool, c) for c in calls]
            return [f.result() for f in futures]


