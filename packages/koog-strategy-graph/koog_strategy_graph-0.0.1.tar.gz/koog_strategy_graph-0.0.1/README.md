# koog_strategy_graph

Koog-inspired **strategy graph** + **agent runtime** in Python (stdlib-first).

This folder contains a lightweight, Koog-like execution model:

- **Graph runtime**: nodes + ordered edges, with Koog-style `Option` forwarding.
- **Agent layer**: `AIAgent` wrapper, `AgentSession` prompt history, `AgentEnvironment` tool registry.
- **LLM layer (provider-neutral)**: `PromptExecutor` protocol + `LLMExecutor` wrapper.
- **Tools**: `ToolDescriptor` + `ToolRegistry` + `DictTool` + ergonomic decorator/class helpers.
- **Extras**: Mermaid diagram export, persistence/checkpointing feature, A2A/ACP clients/servers, and a small LangGraph-like `StateGraph`.

---

## Install (pip)

Install the published distribution:

```bash
pip install koog-strategy-graph
```

Optional extras:

```bash
# Enables OpenTelemetryFeature (tracing)
pip install "koog-strategy-graph[otel]"
```

## Development (from source)

Editable install from this monorepo:

```bash
# From the repo root
pip install -e packages/koog_strategy_graph
```

If you don’t want to install and just want to run a script locally, add the `src/` directory to `sys.path`:

```python
import os, sys
PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PKG_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

import koog_strategy_graph
```

---

## Mental model (graph execution)

- A **node** is a function: `(ctx: GraphContext, input) -> output`.
- Nodes have **ordered outgoing edges**.
- Each edge decides whether it is taken by returning an `Option`:
  - `Some(next_input)` means “take this edge, and pass `next_input` into the next node”.
  - `Empty()` means “this edge does not match; try the next edge”.
- If a node produces an output and **no edge matches**, execution raises `GraphStuckInNodeError` (unless the node is the finish node).
- `GraphContext` is a lightweight, root-shared key/value store used for:
  - agent/session/environment wiring
  - features/pipeline hooks
  - checkpoint/restore “forced context data”

---

## Quickstart 1 — a minimal strategy (no LLM)

```python
from koog_strategy_graph import GraphContext, AIAgent, strategy

# Build a strategy graph.
b = strategy("echo_strategy")
n = b.node("echo", lambda _ctx, x: x)

# Wire edges. `forward_to(...)` is the simplest "pass-through" edge.
b.edge(b.node_start.forward_to(n))
b.edge(n.forward_to(b.node_finish))

echo_strategy = b.build()

# Execute either via Strategy directly...
out = echo_strategy.execute(GraphContext(), "hello")
assert out == "hello"

# ...or via AIAgent (agent wrapper is optional for non-LLM graphs).
agent = AIAgent(strategy=echo_strategy, llm=None)
assert agent.run("hi") == "hi"
```

---

## Quickstart 2 — conditional routing (Option-based edges)

```python
from koog_strategy_graph import GraphContext, Some, strategy

b = strategy("router")

def classify(_ctx: GraphContext, x: str) -> str:
    return "short" if len(x) < 5 else "long"

n_classify = b.node("classify", classify)
n_short = b.node("short", lambda _ctx, _x: "S")
n_long = b.node("long", lambda _ctx, _x: "L")

b.edge(b.node_start.forward_to(n_classify))

# EdgeBuilderIntermediate supports on_condition(...) and transformed(...).
b.edge(
    n_classify.forward_to(n_short)
    .on_condition(lambda _ctx, label: label == "short", label="is_short")
    .transformed(lambda _ctx, _label: "ignored", label="drop_label")
)
b.edge(
    n_classify.forward_to(n_long)
    .on_condition(lambda _ctx, label: label == "long", label="is_long")
    .transformed(lambda _ctx, _label: "ignored", label="drop_label")
)

# Both nodes end the graph.
b.edge(n_short.forward_to(b.node_finish).transformed(lambda _ctx, _x: "S", label="to_finish"))
b.edge(n_long.forward_to(b.node_finish).transformed(lambda _ctx, _x: "L", label="to_finish"))

s = b.build()
assert s.execute(GraphContext(), "yo") == "S"
assert s.execute(GraphContext(), "welcome") == "L"
```

---

## Quickstart 3 — an LLM agent with tools (OpenAI)

This repo includes an online `OpenAIPromptExecutor` using stdlib HTTP (see `provider/openai_provider/`).

```python
import os

from koog_strategy_graph import (
    AIAgent,
    AgentEnvironment,
    AgentSession,
    LLMExecutor,
    ToolChoice,
    DictTool,
    ToolDescriptor,
    agent_strategy,
    on_assistant_message,
    on_tool_call,
)
from koog_strategy_graph.provider.openai_provider.openai_prompt_executor import OpenAIPromptExecutor

# 1) Tools (deterministic functions exposed to the LLM)
env = AgentEnvironment()
env.tools.register(
    DictTool(
        descriptor=ToolDescriptor(
            name="echo",
            description="Echo a string back.",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        ),
        fn=lambda args: f"echo:{(args or {}).get('text', '')}",
    )
)

# 2) LLM executor (provider-neutral wrapper around a PromptExecutor)
prompt_exec = OpenAIPromptExecutor.from_env()  # expects OPENAI_API_KEY
llm = LLMExecutor(
    executor=prompt_exec,
    default_model=os.getenv("OPENAI_MODEL") or "gpt-5-mini",
    default_params={
        # GPT-5-safe knobs used across this repo:
        "max_completion_tokens": 512,
        "reasoning_effort": "low",
        "verbosity": "low",
    },
)

# 3) Agent graph (Koog-like DSL)
session = AgentSession()
b = agent_strategy("agent", llm=llm, environment=env, session=session)

ask = b.node_llm_request("ask", allow_tool_calls=True)     # returns a ResponseMessage
run_tool = b.node_execute_tool("run_tool")                 # ToolCallMessage -> ReceivedToolResult
send_result = b.node_llm_send_tool_result("send_result")   # -> ResponseMessage

b.edge(b.base.node_start.forward_to(ask))

# If LLM returns a tool call, execute it.
b.edge(on_tool_call(ask.forward_to(run_tool)))

# After tool execution, send tool result back to LLM.
b.edge(run_tool.forward_to(send_result))

# If the LLM returns final assistant text, end.
b.edge(on_assistant_message(ask.forward_to(b.base.node_finish)))
b.edge(on_assistant_message(send_result.forward_to(b.base.node_finish)))

agent_strategy_graph = b.build()

# 4) Run via AIAgent (wires session/environment/llm into GraphContext)
agent = AIAgent(strategy=agent_strategy_graph, llm=llm, environment=env, session=session)
result_text = agent.run("Say hello. You MAY call tools if helpful.")
print(result_text)
```

Notes:

- Tool availability inside agent graphs is controlled by a **tool selection strategy** (see `ALL`, `NONE`, `Tools`, `AutoSelectForTask`).
- For streaming + autonomous tool loops, see `AgentStrategyBuilder.node_llm_request_streaming_and_send_results(...)` in `core/agent_dsl.py`.

---

## Exposing an agent over HTTP (A2A)

The A2A server is stdlib `http.server` and returns an `HTTPServer`; you control `serve_forever()` and shutdown.

```python
import threading

from koog_strategy_graph import AIAgent, A2AServerConfig, A2AClient, A2AEndpoint, serve

# `agent` can be any AIAgent (LLM-backed or offline).
server = serve(agent=agent, config=A2AServerConfig(host="127.0.0.1", port=0))  # port=0 => ephemeral
host, port = server.server_address[0], server.server_address[1]

t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
try:
    client = A2AClient(endpoint=A2AEndpoint(base_url=f"http://{host}:{port}"))
    resp = client.execute(
        {
            "request_id": "r1",
            "messages": [{"role": "user", "content": "hi"}],
            "input": "hello",
        }
    )
    assert resp["ok"] is True
finally:
    server.shutdown()
```

---

## LangGraph-like state machine (`StateGraph`)

If you want a smaller “state update” surface (LangGraph-ish), use `StateGraph`:

```python
from typing import TypedDict

from koog_strategy_graph import END, StateGraph

class S(TypedDict, total=False):
    n: int

g = StateGraph(dict)
g.add_node("inc", lambda st: {"n": int(st.get("n", 0)) + 1})
g.set_entry_point("inc")
g.add_conditional_edges("inc", lambda st: "done" if st["n"] >= 3 else "more", {"more": "inc", "done": END})

compiled = g.compile()
updates = list(compiled.stream({"n": 0}))
```

---

## Visualizing a strategy (Mermaid)

```python
from koog_strategy_graph import as_mermaid_diagram

print(as_mermaid_diagram(echo_strategy))
```

---

## Public API reference (recommended imports)

Everything below is exported by `koog_strategy_graph/__init__.py` and intended to be imported as:

```python
from koog_strategy_graph import <name>
```

### Core graph runtime

- `GraphConfig`
- `GraphContext`
- `NodeBase`, `Node`, `StartNode`, `FinishNode`
- `Edge`, `EdgeBuilderIntermediate`
- `Subgraph`, `Strategy`
- `ExecutionPoint`, `ExecutionPointNode`
- `ParallelNodeExecutionResult`, `ParallelResult`
- `strategy` (builder entrypoint), `StrategyBuilder`, `SubgraphBuilder`
- `as_mermaid_diagram`

### Option/Maybe (used by edges)

- `Option`, `Some`, `Empty`

### Agent runtime + LLM wrapper

- `AIAgent`
- `AgentEnvironment`
- `LLMExecutor`, `LLMResponse`
- `AgentSession`
- `ToolChoice`

### Tools

- `ToolDescriptor`
- `ToolRegistry`
- `DictTool`
- `SafeTool`
- `ReceivedToolResult`

### Agent DSL (Koog-like builder)

- `agent_strategy`
- `AgentStrategyBuilder`

### Tool selection

- `ToolSelectionStrategy`
- `ALL`, `NONE`, `Tools`, `AutoSelectForTask`

### Edge helpers (routing by message/result type)

- `on_is_instance`
- `on_tool_call`, `on_tool_not_called`, `on_multiple_tool_calls`
- `on_assistant_message`, `on_reasoning_message`
- `on_tool_result`, `on_successful_tool_result`

### Features / pipeline hooks

- `Feature`, `FeaturePipeline`
- `EventHandlerConfig`, `EventHandlerFeature`
- `HistoryCompressionStrategy`, `WholeHistory`, `FromLastNMessages`

### Persistence / checkpointing

- `SqliteCheckpointer`
- `make_strategy_checkpoint`, `apply_strategy_checkpoint`
- `RollbackStrategy`
- `AgentCheckpointData`
- `PersistenceStorageProvider`
- `NoPersistenceStorageProvider`
- `InMemoryPersistenceStorageProvider`
- `FilePersistenceStorageProvider`
- `SqlitePersistenceStorageProvider`
- `RollbackToolRegistry`
- `PersistenceFeatureConfig`, `PersistenceFeature`

### Structured outputs

- `StructuredResult`

### Streaming

- `StreamFrame`

### A2A / ACP (agent-to-agent protocols)

- A2A: `A2AEndpoint`, `A2ARequest`, `A2AResponse`, `A2AMessage`, `A2AClient`, `A2AServerConfig`
- ACP: `ACPEndpoint`, `ACPRequest`, `ACPResponse`, `ACPMessage`, `ACPClient`

---

## Provider implementations (extra imports)

These are **not** re-exported at the top-level, but are used by tests/benchmarks:

- OpenAI prompt executor (online):

```python
from koog_strategy_graph.provider.openai_provider.openai_prompt_executor import OpenAIPromptExecutor
```

There are also provider adapters under `koog_strategy_graph/provider/` (e.g. `anthropic_provider/`, `google_provider/`) intended to plug into the shared `HttpChatPromptExecutor` in `koog_strategy_graph/base/`.

