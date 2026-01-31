# koog_strategy_graph Maintainer Guide

This doc is a **map of “where things live” and “who calls what”** in `koog_strategy_graph/`.  
It’s intended to make refactors (especially provider-agnostic extraction) safe and to help identify **redundant/repeating logic**.

## Runtime architecture (high-level)

- **Graph runtime**
  - **Core execution loop**: `Strategy.execute()` → `Subgraph.execute()` iterates nodes, resolves edges, and fires pipeline events.
  - **Execution path**: `GraphContext` tracks a Koog-like `execution_path()` (used for checkpointing/resume).
  - **Interruption semantics**: storing “forced context data” in `GraphContext` signals a restore/jump.

- **Agent layer**
  - `AIAgent` runs a top-level `Strategy` with a `GraphContext` containing:
    - `environment` (`AgentEnvironment`): tool registry + safe tool execution
    - `session` (`AgentSession`): prompt history + selected tool descriptors
    - `llm` (`LLMExecutor`): provider-neutral wrapper around a `PromptExecutor`
    - `pipeline` (`FeaturePipeline`): optional hooks/features (event handler, persistence, etc.)

- **LLM layer**
  - `LLMExecutor.invoke()` / `invoke_streaming()` call a provider-neutral `PromptExecutor`.
  - For HTTP/SSE-based chat providers, we now use a **two-layer design**:
    - `HttpChatPromptExecutor` (shared stdlib HTTP + SSE loop)
    - `<Provider>Chat...Adapter` (provider-specific request/response schema + stream parsing)
  - **Implemented**:
    - `OpenAIPromptExecutor` (thin wrapper) → `HttpChatPromptExecutor(adapter=OpenAIChatCompletionsAdapter(...))`
    - `AnthropicPromptExecutor` (thin wrapper) → `HttpChatPromptExecutor(adapter=AnthropicChatAdapter(...))` (in `provider/anthropic_provider`)
    - `GeminiPromptExecutor` (thin wrapper) → `HttpChatPromptExecutor(adapter=GeminiChatAdapter(...))` (in `provider/google_provider`)

## Call-chain map (with file references)

### Graph execution + events

- **Execution loop**
  - **Defined in**: `core.py` (`Subgraph.execute`, `Strategy.execute`, `GraphContext`)
  - **Used by**: everything built using `dsl.strategy(...)` + `agent_dsl.agent_strategy(...)`
  - **Important invariant**: edges are only resolved when a node returns a **non-`None`** output. If a node returns `None`, the graph will stop and (unless it is the finish node) raise `GraphStuckInNodeError`.
  - **Events fired**
    - `on_strategy_starting` / `on_strategy_completed` in `Strategy.execute`
    - `on_node_execution_starting` / `on_node_execution_completed` / `on_node_execution_failed` in `Subgraph.execute`
    - `on_subgraph_execution_*` in `Subgraph.execute` (nested subgraphs)

### Agent DSL nodes → LLM/tooling

- **Non-streaming LLM request nodes**
  - **Defined in**: `agent_dsl.py`
  - **Call chain**:
    - node fn → `LLMExecutor.invoke(...)`
    - `LLMExecutor` → `PromptExecutor.execute(...)` (provider)

- **Streaming node (end-to-end tool calling)**
  - **Defined in**: `agent_dsl.AgentStrategyBuilder.node_llm_request_streaming_and_send_results`
  - **Call chain**:
    - node fn → `LLMExecutor.invoke_streaming(...)`
    - consumes `StreamFrame`s:
      - `type="append"` / `"text_delta"`: collects assistant text
      - `type="tool_call"`: parses args JSON → `ToolCallMessage`
    - appends `ToolCallMessage` to prompt
    - executes tools concurrently via `AgentEnvironment.execute_tools_parallel(...)`
    - appends `ToolResultMessage` to prompt
    - repeats streaming until final assistant text arrives
  - **Events fired**: streaming events + tool events via `FeaturePipeline`

### Tool selection + allowed tools

- **Tool selection entrypoint**
  - **Defined in**: `tool_selection.select_tools_for_strategy`
  - **Call chain**:
    - `AIAgentSubgraph.execute` / `AIAgentGraphStrategy.execute` select tools from `ToolRegistry.descriptors()`
    - selection strategies may use `HistoryCompressionStrategy` to simplify selection context
  - **Allowed tools constraint**
    - `tool_selection.set_allowed_tool_names` and `tool_selection.is_tool_allowed`
    - enforced in `agent_dsl` tool execution nodes + streaming tool loop

### Tool ergonomics (Koog-style annotation/class-based tools)

- **Goal**
  - Keep the existing runtime contract (`ToolDescriptor` + `ToolRegistry` + tool calling) unchanged, but add
    Koog-like ergonomics so users don’t have to hand-write boilerplate.

- **Annotation-based tools (decorator)**
  - **Defined in**: `core/tooling/decorators.py` (`tool(...)`)
  - **What it returns**: a `DictTool` (so it plugs into `ToolRegistry` directly)
  - **Schema generation**: `core/tooling/schema.py` (`schema_from_signature(...)`)

- **Class-based tools**
  - **Defined in**: `core/tooling/class_tools.py` (`SimpleClassTool`)

- **Registry helper**
  - **Defined in**: `core/tooling/registry.py` (`register_all(...)`)

- **Built-in tools**
  - **Defined in**: `core/built_in_tools/`
    - `echo_tool` (`echo.py`)
    - `utc_now_tool` (`time.py`)

### Persistence/checkpointing

- **Persistence feature**
  - **Defined in**: `persistence.PersistenceFeature`
  - **Mechanism**
    - stores `AgentContextData` into `GraphContext` (forced data)
    - `Strategy.execute` sees it and calls `AgentContextData.apply(...)` to restore prompt + execution point
  - **Rollback tool side-effects**
    - `RollbackToolRegistry` maps tool → rollback tool and replays in reverse order during rollback

## Provider boundary: what must be provider-specific vs provider-neutral

### Provider-neutral (should live outside provider adapters)

- **PromptExecutor protocol**: `prompt_executor.py`
- **Reusable stdlib HTTP/SSE executor**: `http_chat_executor.HttpChatPromptExecutor`
- **Provider adapter protocol**: `provider_adapter.ChatProviderAdapter` (+ `ProviderRequest`)
- **LLM wrapper + session**: `llm_executor.py` (`LLMExecutor`, `AgentSession`, `ToolChoice`)
- **Streaming frame model**: `streaming.py` (`StreamFrame`)
- **Streaming consumption loop**: `agent_dsl.node_llm_request_streaming_and_send_results`
- **Tool execution**: `environment.AgentEnvironment`
- **Events/pipeline**: `features.FeaturePipeline`, `event_handler.EventHandlerFeature`
- **Observability**: `observability.opentelemetry.OpenTelemetryFeature` (standard OTel spans for agents/nodes/tools)

## A2A / ACP (Agent-to-Agent + Agent Client Protocol)

This repo now includes a **minimal, stdlib-only** starting point for Koog’s A2A/ACP concepts.

### A2A
- **Types / wire format**: `core/a2a/types.py`
  - Now supports full tool transfer via `tool_calls` list in `A2AMessage`.
- **Client (stdlib HTTP)**: `core/a2a/client.py` (`A2AClient`)
- **Server (stdlib http.server)**: `core/a2a/server.py`
  - `serve(agent=..., config=...)` returns an `HTTPServer` (caller controls `serve_forever()` / shutdown)
  - Endpoint: `POST /a2a/execute`
  - Supports text content and tool calls/results (allowing multi-agent delegation).
- **Online integration test (OpenAI)**: `tests/test_a2a_online_openai.py`
  - Spins up a local A2A server backed by an OpenAI-powered `AIAgent`.
  - Exercises real tool calling over the network (2 forced tool calls) + strict structured JSON output.
  - Requires `OPENAI_API_KEY` in `tests/.env`.

### ACP
- **Types / wire format**: `core/acp/types.py`
- **Client (stdlib HTTP)**: `core/acp/client.py` (`ACPClient`)
  - Full support for sessions (`ACPSession`) and tool execution loop.
- **Server (stdlib http.server)**: `core/acp/server.py` (`ACPServer`)
  - Exposes any `AIAgent` or `Strategy` over ACP.
  - Handles session management and protocol mapping (Koog Prompt <-> ACP messages).

### Provider-specific (should remain inside each adapter)

- `Prompt` → provider request shape (messages formatting, tool schema shape)
- model/param compatibility rules and provider-specific params
- response parsing (non-streaming)
- streaming payload parsing (chunk/event formats)

## `OpenAIPromptExecutor` feature inventory + current usage

### Public API

- **`OpenAIPromptExecutor.execute(...)`**
  - **Used by**: `LLMExecutor.invoke(...)` (indirect)
  - **Used in tests**: online functional tests wrap `OpenAIPromptExecutor.from_env()`
  - **Implementation**: delegates to `HttpChatPromptExecutor(adapter=OpenAIChatCompletionsAdapter(...))`

- **`OpenAIPromptExecutor.stream(...)`**
  - **Used by**: `LLMExecutor.invoke_streaming(...)` (indirect)
  - **Used by**:
    - `agent_dsl.node_llm_request_streaming(...)`
    - `agent_dsl.node_llm_request_streaming_and_send_results(...)`
    - `tests/test_openai_streaming_online.py`
  - **Implementation**: delegates to `HttpChatPromptExecutor` streaming loop and `OpenAIChatCompletionsAdapter` stream parsing.
  - **Important streaming edge case**:
    - Some gateways can return an SSE stream where the first/only `data:` line is `"[DONE]"` (no JSON chunks).
    - `HttpChatPromptExecutor.stream(...)` treats `"[DONE]"` as an SSE event and, if no text/tool frames were emitted, triggers a **best-effort fallback** to `execute(...)` to try to obtain at least one assistant text append before ending the stream.

### OpenAI provider-specific logic (where it lives now)

- **Shared HTTP/SSE**: `http_chat_executor.HttpChatPromptExecutor` + `http_utils.*`
- **Request/response schema + stream parsing**: `openai_adapter.OpenAIChatCompletionsAdapter`
  - Request mapping: prompt/messages/tool schema/tool choice/param normalization/model allow/deny
  - Response parsing: non-streaming chat.completions → `ResponseMessage`s
  - Streaming parsing: SSE data_line → `StreamFrame` sequence (uses `StreamFrameFlowBuilder`)
  - Execute retry shim: strips unsupported params on “Unknown parameter …” errors (one retry)

## Redundancy / repetition candidates (what we should consolidate)

### 1) HTTP + SSE primitives (already consolidated)

- **Today**
  - Shared helpers live in `http_utils.py` (`json_dumps_compact`, `iter_sse_data`, `http_post_json`).
  - Streaming control flow (including fallback behavior) lives in `http_chat_executor.HttpChatPromptExecutor`.
- **Rule**
  - New provider executors/adapters should **not** re-implement JSON dumping, POST, or SSE parsing; import from these modules.

### 2) Text-delta extraction helper (safe to extract)

- **Today**
  - Shared helper lives in `stream_text.py` (`extract_text_parts`).
  - Provider adapters should call `extract_text_parts(...)` when their streaming chunk format can contain list-of-parts text.

### 3) Tool-call delta coalescing vs `StreamFrameFlowBuilder` (duplication to eliminate)

- **Today**
  - Separately, `streaming.StreamFrameFlowBuilder` exists to provide Koog-like invariants:
    - flush pending tool call before emitting text/end
    - buffer partial tool args
- **Redundancy**
  - Two places encode “tool-call buffering” rules.
- **Status**
  - ✅ `StreamFrameFlowBuilder` supports **multiple concurrent tool calls** (indexed buffering)
  - ✅ OpenAI streaming uses the builder via `openai_adapter.OpenAIChatCompletionsAdapter` (no local `tool_acc`)

### 4) Tool execution + pipeline events (future cleanup)

- **Today**
  - `agent_dsl.node_execute_tool` and streaming loop both emit tool events + validate `is_tool_allowed`.
- **Potential refactor later**
  - Create a small shared helper (e.g. `tool_runtime.py`) that:
    - validates tool allowed
    - emits pipeline tool events consistently
    - delegates to `AgentEnvironment.execute_tool(s)`
  - Not required for provider-agnostic extraction, but reduces repetition.

## How to use this doc during refactors

- **Online tests are contract tests**:
  - Do not assert that OpenAI (or any provider) always emits **streaming text deltas**. Contract: the stream yields at least one `StreamFrame` and ends with `type="end"`.
  - Do not assert that a provider always emits a **tool call**, even when you request/force one. If a test needs tool execution deterministically, construct `ToolCallMessage(...)` directly and test the framework’s tool runtime + events.
  - Keep online assertions focused on **framework invariants** (event hooks fire, tool execution works, streaming loop terminates), not provider compliance.

- **Rule**: move only utilities that are clearly provider-neutral (HTTP/SSE/text extraction), keep request/response schemas inside provider adapters.
- **Safety**: prefer “extract function → import it → keep wrapper name for backward compatibility” until the codebase is stable.
- **Testing**: existing online tests reference `OpenAIPromptExecutor` directly; keep its behavior and public surface stable while refactoring.

## Org stress benchmark: Koog vs LangGraph (A2A hierarchy, multi-turn)

This repo includes a **graph-of-graphs-of-graphs** benchmark that exercises a 2-level org hierarchy:

- **U → O → TL → TM → O → U**
- **3 TLs** (Health / Finance / Information)
- **9 TMs** (3 specialists per TL)
- **All cross-agent calls use A2A over HTTP** (local stdlib servers)
- **Multi-turn conversation** (3 turns with changing constraints + incident response)

### Files

- **Shared scenario (schema + 3 turns)**: `benchmarks/org_stress_common.py`
- **Koog implementation** (O/TL/TM are `AIAgent` graphs; TL/TM invoked as tools via A2A): `benchmarks/org_hierarchy_koog.py`
- **LangGraph implementation** (optional dependency; same A2A wiring): `benchmarks/org_hierarchy_langgraph.py`
- **Runner** (executes both, measures timing/telemetry, scores deterministically): `benchmarks/run_org_benchmark.py`

### How to run

- Put `OPENAI_API_KEY=...` (and optionally `OPENAI_MODEL=...`) in `tests/.env`
- Run:

```powershell
python .\benchmarks\run_org_benchmark.py
```

### Verbose tracing (debug)

To print **per-agent LLM prompts/responses** and **A2A request/response summaries** while the benchmark runs:

```powershell
$env:ORG_BENCH_VERBOSE="1"
python .\benchmarks\run_org_benchmark.py
```

### What it measures (high-signal)

- **Accuracy (deterministic)**: budget/retention/no-cloud constraints + required risk presence
- **Relevance (proxy)**: required sections are non-empty
- **Efficiency**: wall-time per turn + total event counts (LLM calls, tool calls, A2A calls)
- **Interaction**: verifies the org-shaped call pattern (O calls TLs; TL calls TMs) via telemetry events
