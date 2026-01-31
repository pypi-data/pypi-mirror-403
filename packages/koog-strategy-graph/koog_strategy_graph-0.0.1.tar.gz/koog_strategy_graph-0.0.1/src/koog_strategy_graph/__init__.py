"""
Koog-inspired strategy graph framework (Python).

This package mirrors the core semantics of Koog's strategy graphs:
- Nodes with ordered outgoing edges
- Edge conditions + output transformations
- Subgraphs (graphs as nodes) with start/finish nodes
- Optional checkpointing/resume hooks

The `koog_strategy_graph.state_graph.StateGraph` module provides a minimal,
LangGraph-like state-machine wrapper used by this repo's org workflow.
"""

from .core.option import Option, Some, Empty
from .core.core import (
    GraphConfig,
    GraphContext,
    NodeBase,
    Node,
    StartNode,
    FinishNode,
    Edge,
    EdgeBuilderIntermediate,
    Subgraph,
    Strategy,
    ExecutionPoint,
    ExecutionPointNode,
    ParallelNodeExecutionResult,
    ParallelResult,
)
from .core.state_graph import END, StateGraph
from .core.checkpoint_sqlite import SqliteCheckpointer
from .core.dsl import strategy, StrategyBuilder, SubgraphBuilder
from .core.mermaid import as_mermaid_diagram
from .core.tools import ToolDescriptor, ToolRegistry, SafeTool, ReceivedToolResult, DictTool
from .core.environment import AgentEnvironment
from .core.llm_executor import LLMExecutor, AgentSession, ToolChoice, LLMResponse
from .base.prompt_executor import PromptExecutor, PromptExecutorResult
from .core.streaming import StreamFrame
from .core.response_processor import ResponseProcessor, Chain
from .core.agent_dsl import agent_strategy, AgentStrategyBuilder
from .core.agent import AIAgent
from .core.tool_selection import ToolSelectionStrategy, ALL, NONE, Tools, AutoSelectForTask
from .core.edge_extensions import (
    on_is_instance,
    on_tool_call,
    on_tool_not_called,
    on_multiple_tool_calls,
    on_assistant_message,
    on_reasoning_message,
    on_tool_result,
    on_successful_tool_result,
)
from .core.features import Feature, FeaturePipeline
from .core.persistence import (
    apply_strategy_checkpoint,
    make_strategy_checkpoint,
    RollbackStrategy,
    AgentCheckpointData,
    PersistenceStorageProvider,
    NoPersistenceStorageProvider,
    InMemoryPersistenceStorageProvider,
    FilePersistenceStorageProvider,
    SqlitePersistenceStorageProvider,
    RollbackToolRegistry,
    PersistenceFeatureConfig,
    PersistenceFeature,
)
from .core.structured import StructuredResult
from .core.event_handler import EventHandlerConfig, EventHandlerFeature
from .core.history import HistoryCompressionStrategy, WholeHistory, FromLastNMessages
from .core.a2a.types import A2AEndpoint, A2ARequest, A2AResponse, A2AMessage
from .core.a2a.client import A2AClient
from .core.a2a.server import A2AServerConfig
from .core.acp.types import ACPEndpoint, ACPRequest, ACPResponse, ACPMessage
from .core.acp.client import ACPClient

__all__ = [
    "Option",
    "Some",
    "Empty",
    "GraphConfig",
    "GraphContext",
    "NodeBase",
    "Node",
    "StartNode",
    "FinishNode",
    "Edge",
    "EdgeBuilderIntermediate",
    "Subgraph",
    "Strategy",
    "ExecutionPoint",
    "ExecutionPointNode",
    "ParallelNodeExecutionResult",
    "ParallelResult",
    "END",
    "StateGraph",
    "SqliteCheckpointer",
    "strategy",
    "StrategyBuilder",
    "SubgraphBuilder",
    "as_mermaid_diagram",
    "ToolDescriptor",
    "ToolRegistry",
    "SafeTool",
    "ReceivedToolResult",
    "DictTool",
    "AgentEnvironment",
    "LLMExecutor",
    "AgentSession",
    "ToolChoice",
    "LLMResponse",
    "PromptExecutor",
    "PromptExecutorResult",
    "StreamFrame",
    "ResponseProcessor",
    "Chain",
    "agent_strategy",
    "AgentStrategyBuilder",
    "AIAgent",
    "ToolSelectionStrategy",
    "ALL",
    "NONE",
    "Tools",
    "AutoSelectForTask",
    "on_is_instance",
    "on_tool_call",
    "on_tool_not_called",
    "on_multiple_tool_calls",
    "on_assistant_message",
    "on_reasoning_message",
    "on_tool_result",
    "on_successful_tool_result",
    "Feature",
    "FeaturePipeline",
    "apply_strategy_checkpoint",
    "make_strategy_checkpoint",
    "RollbackStrategy",
    "AgentCheckpointData",
    "PersistenceStorageProvider",
    "NoPersistenceStorageProvider",
    "InMemoryPersistenceStorageProvider",
    "FilePersistenceStorageProvider",
    "SqlitePersistenceStorageProvider",
    "RollbackToolRegistry",
    "PersistenceFeatureConfig",
    "PersistenceFeature",
    "StructuredResult",
    "EventHandlerConfig",
    "EventHandlerFeature",
    "HistoryCompressionStrategy",
    "WholeHistory",
    "FromLastNMessages",
    "A2AEndpoint",
    "A2ARequest",
    "A2AResponse",
    "A2AMessage",
    "A2AClient",
    "A2AServerConfig",
    "ACPEndpoint",
    "ACPRequest",
    "ACPResponse",
    "ACPMessage",
    "ACPClient",
]