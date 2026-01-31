from __future__ import annotations

import json
import pickle
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol

from .core import GraphContext, Strategy
from .messages import Prompt
from .tools import Tool


class RollbackStrategy(str, Enum):
    """
    Koog-like rollback strategies.
    """

    Default = "default"
    MessageHistoryOnly = "message_history_only"


_KOOG_AGENT_ID_KEY = "__koog_agent_id__"
_KOOG_SESSION_KEY = "__koog_agent_session__"


@dataclass(frozen=True)
class AgentCheckpointData:
    """
    Koog-like checkpoint payload.

    Mirrors Koog's checkpoint concept:
    - message history
    - node path (execution point)
    - input for the node
    - timestamp + version

    Note: `message_history` is stored in Prompt's portable serialized format.
    """

    checkpoint_id: str
    message_history: List[Dict[str, Any]]
    node_path: str
    last_input_pickle: bytes
    created_at: float
    version: int
    tombstone: bool = False

    def is_tombstone(self) -> bool:
        return bool(self.tombstone)

    def prompt(self) -> Prompt:
        return Prompt.from_serializable(list(self.message_history or []))

    def last_input(self) -> Any:
        return pickle.loads(self.last_input_pickle) if self.last_input_pickle else None


class PersistenceStorageProvider(Protocol):
    def get_checkpoints(self, agent_id: str) -> List[AgentCheckpointData]: ...

    def save_checkpoint(self, agent_id: str, checkpoint: AgentCheckpointData) -> None: ...

    def get_latest_checkpoint(self, agent_id: str) -> Optional[AgentCheckpointData]: ...


@dataclass
class NoPersistenceStorageProvider:
    def get_checkpoints(self, agent_id: str) -> List[AgentCheckpointData]:
        _ = agent_id
        return []

    def save_checkpoint(self, agent_id: str, checkpoint: AgentCheckpointData) -> None:
        _ = agent_id
        _ = checkpoint
        return

    def get_latest_checkpoint(self, agent_id: str) -> Optional[AgentCheckpointData]:
        _ = agent_id
        return None


@dataclass
class InMemoryPersistenceStorageProvider:
    _by_agent: Dict[str, List[AgentCheckpointData]] = field(default_factory=dict)

    def get_checkpoints(self, agent_id: str) -> List[AgentCheckpointData]:
        return list(self._by_agent.get(agent_id, []))

    def save_checkpoint(self, agent_id: str, checkpoint: AgentCheckpointData) -> None:
        self._by_agent.setdefault(agent_id, []).append(checkpoint)
        self._by_agent[agent_id].sort(key=lambda c: (c.version, c.created_at))

    def get_latest_checkpoint(self, agent_id: str) -> Optional[AgentCheckpointData]:
        cps = self._by_agent.get(agent_id) or []
        return cps[-1] if cps else None


@dataclass
class FilePersistenceStorageProvider:
    """
    Simple file-based provider (JSONL).

    One file per agent_id: <dir>/<agent_id>.jsonl
    """

    directory: Path

    def _path(self, agent_id: str) -> Path:
        safe = "".join(ch for ch in agent_id if ch.isalnum() or ch in {"-", "_"}).strip() or "agent"
        return self.directory / f"{safe}.jsonl"

    def get_checkpoints(self, agent_id: str) -> List[AgentCheckpointData]:
        p = self._path(agent_id)
        if not p.exists():
            return []
        out: List[AgentCheckpointData] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            out.append(
                AgentCheckpointData(
                    checkpoint_id=str(obj.get("checkpoint_id") or ""),
                    message_history=list(obj.get("message_history") or []),
                    node_path=str(obj.get("node_path") or ""),
                    last_input_pickle=bytes.fromhex(obj.get("last_input_pickle_hex") or "")
                    if obj.get("last_input_pickle_hex")
                    else b"",
                    created_at=float(obj.get("created_at") or 0.0),
                    version=int(obj.get("version") or 0),
                    tombstone=bool(obj.get("tombstone") or False),
                )
            )
        out.sort(key=lambda c: (c.version, c.created_at))
        return out

    def save_checkpoint(self, agent_id: str, checkpoint: AgentCheckpointData) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        p = self._path(agent_id)
        payload = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "message_history": checkpoint.message_history,
            "node_path": checkpoint.node_path,
            "last_input_pickle_hex": checkpoint.last_input_pickle.hex() if checkpoint.last_input_pickle else "",
            "created_at": checkpoint.created_at,
            "version": checkpoint.version,
            "tombstone": checkpoint.tombstone,
        }
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def get_latest_checkpoint(self, agent_id: str) -> Optional[AgentCheckpointData]:
        cps = self.get_checkpoints(agent_id)
        return cps[-1] if cps else None


@dataclass
class SqlitePersistenceStorageProvider:
    """
    SQLite provider for Koog-like checkpoints.

    Stores ALL checkpoints and supports retrieving latest + by id.
    """

    db_path: Path
    _conn: Optional[sqlite3.Connection] = None

    @classmethod
    def from_conn_string(cls, conn_string: str) -> "SqlitePersistenceStorageProvider":
        return cls(db_path=Path(conn_string))

    def __enter__(self) -> "SqlitePersistenceStorageProvider":
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS koog_agent_checkpoints (
              agent_id TEXT NOT NULL,
              checkpoint_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              tombstone INTEGER NOT NULL,
              created_at REAL NOT NULL,
              payload_blob BLOB NOT NULL,
              PRIMARY KEY (agent_id, checkpoint_id)
            )
            """
        )
        self._conn.commit()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SqlitePersistenceStorageProvider is not open (use it as a context manager).")
        return self._conn

    def save_checkpoint(self, agent_id: str, checkpoint: AgentCheckpointData) -> None:
        if not agent_id:
            return
        conn = self._require_conn()
        payload = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "message_history": checkpoint.message_history,
            "node_path": checkpoint.node_path,
            "last_input_pickle": checkpoint.last_input_pickle,
            "created_at": checkpoint.created_at,
            "version": checkpoint.version,
            "tombstone": checkpoint.tombstone,
        }
        blob = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
        conn.execute(
            """
            INSERT INTO koog_agent_checkpoints(agent_id, checkpoint_id, version, tombstone, created_at, payload_blob)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_id, checkpoint_id) DO UPDATE SET
              version = excluded.version,
              tombstone = excluded.tombstone,
              created_at = excluded.created_at,
              payload_blob = excluded.payload_blob
            """,
            (agent_id, checkpoint.checkpoint_id, int(checkpoint.version), 1 if checkpoint.tombstone else 0, float(checkpoint.created_at), blob),
        )
        conn.commit()

    def get_checkpoints(self, agent_id: str) -> List[AgentCheckpointData]:
        if not agent_id:
            return []
        conn = self._require_conn()
        cur = conn.execute(
            """
            SELECT payload_blob FROM koog_agent_checkpoints
            WHERE agent_id = ?
            ORDER BY version ASC, created_at ASC
            """,
            (agent_id,),
        )
        out: List[AgentCheckpointData] = []
        for (blob,) in cur.fetchall():
            payload = pickle.loads(blob)
            if not isinstance(payload, dict):
                continue
            out.append(
                AgentCheckpointData(
                    checkpoint_id=str(payload.get("checkpoint_id") or ""),
                    message_history=list(payload.get("message_history") or []),
                    node_path=str(payload.get("node_path") or ""),
                    last_input_pickle=bytes(payload.get("last_input_pickle") or b""),
                    created_at=float(payload.get("created_at") or 0.0),
                    version=int(payload.get("version") or 0),
                    tombstone=bool(payload.get("tombstone") or False),
                )
            )
        return out

    def get_latest_checkpoint(self, agent_id: str) -> Optional[AgentCheckpointData]:
        cps = self.get_checkpoints(agent_id)
        return cps[-1] if cps else None

    # ---------------
    # Back-compat API
    # ---------------

    def save(self, thread_id: str, checkpoint: AgentCheckpointData) -> None:
        # Legacy name used by earlier code.
        self.save_checkpoint(thread_id, checkpoint)

    def load(self, thread_id: str) -> Optional[AgentCheckpointData]:
        return self.get_latest_checkpoint(thread_id)


@dataclass
class RollbackToolRegistry:
    """
    Koog-like rollback tool registry.

    Maps a tool name -> rollback tool (must accept the same args).
    """

    _by_name: Dict[str, Tool[Any, Any]] = field(default_factory=dict)

    def register_rollback(self, tool: Tool[Any, Any], rollback_tool: Tool[Any, Any]) -> None:
        name = tool.descriptor.name
        if not name:
            raise ValueError("Tool name cannot be empty")
        if name in self._by_name:
            raise ValueError(f'Tool "{name}" is already defined')
        self._by_name[name] = rollback_tool

    def get_rollback_tool(self, tool_name: str) -> Optional[Tool[Any, Any]]:
        return self._by_name.get(tool_name)


@dataclass
class PersistenceFeatureConfig:
    storage: PersistenceStorageProvider = field(default_factory=NoPersistenceStorageProvider)
    enable_automatic_persistence: bool = False
    rollback_strategy: RollbackStrategy = RollbackStrategy.Default
    rollback_tool_registry: RollbackToolRegistry = field(default_factory=RollbackToolRegistry)


@dataclass
class AgentContextData:
    """
    Koog-like "forced data" applied to the agent execution context on restore.
    """

    message_history: List[Dict[str, Any]]
    node_path: str
    last_input: Any
    rollback_strategy: RollbackStrategy
    additional_rollback_actions: List[Callable[[GraphContext], None]] = field(default_factory=list)

    def apply(self, *, ctx: GraphContext, strategy: Strategy[Any, Any]) -> None:
        for action in self.additional_rollback_actions:
            try:
                action(ctx)
            except Exception:
                continue

        session = ctx.get(_KOOG_SESSION_KEY) or ctx.get("session")
        if session is None or not hasattr(session, "prompt"):
            raise RuntimeError("Persistence requires an AgentSession to be stored in context.")

        # Restore prompt history
        session.prompt = Prompt.from_serializable(list(self.message_history or []))

        if self.rollback_strategy == RollbackStrategy.MessageHistoryOnly:
            return

        if self.node_path:
            strategy.set_execution_point(self.node_path, self.last_input)


@dataclass
class PersistenceFeature:
    """
    Koog-like Persistence feature as a pipeline-installed component.
    """

    config: PersistenceFeatureConfig

    # ---------------------------------------------------------------------
    # Feature protocol compatibility
    # ---------------------------------------------------------------------
    # `FeaturePipeline` maintains a minimal `Feature` Protocol used by some codepaths.
    # Persistence is primarily wired through the Koog-like execution hooks
    # (`on_strategy_starting`, `on_node_execution_completed`, `on_strategy_completed`),
    # but we still provide these no-op methods so static typing remains consistent.

    def on_node_start(self, *, node: str, ctx: GraphContext, input_value: Any) -> None:
        _ = node
        _ = ctx
        _ = input_value
        return

    def on_node_end(self, *, node: str, ctx: GraphContext, input_value: Any, output_value: Any) -> None:
        _ = node
        _ = ctx
        _ = input_value
        _ = output_value
        return

    def on_tool_executed(self, *, tool: str, ok: bool, ctx: GraphContext) -> None:
        _ = tool
        _ = ok
        _ = ctx
        return

    def on_llm_called(self, *, ctx: GraphContext) -> None:
        _ = ctx
        return

    def _agent_id(self, ctx: GraphContext) -> str:
        agent_id = str(ctx.get(_KOOG_AGENT_ID_KEY, "") or ctx.get("agent_id") or "")
        if not agent_id:
            raise RuntimeError("Persistence requires an agent_id to be set in the GraphContext.")
        return agent_id

    def _session_prompt_serializable(self, ctx: GraphContext) -> List[Dict[str, Any]]:
        session = ctx.get(_KOOG_SESSION_KEY) or ctx.get("session")
        if session is None or not hasattr(session, "prompt"):
            raise RuntimeError("Persistence requires an AgentSession to be stored in context.")
        prompt = session.prompt
        if not isinstance(prompt, Prompt):
            raise TypeError(f"AgentSession.prompt must be a Prompt, got: {type(prompt)!r}")
        return prompt.to_serializable()

    def _message_history_diff(
        self, *, current: List[Dict[str, Any]], checkpoint: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Only works when current is AHEAD of checkpoint and shares an exact prefix.
        if len(checkpoint) > len(current):
            return []
        for i, msg in enumerate(checkpoint):
            if current[i] != msg:
                return []
        return current[len(checkpoint) :]

    def on_strategy_starting(self, *, ctx: GraphContext, strategy: Strategy[Any, Any]) -> None:
        # Enforce Koog prerequisite: unique node names required for checkpointing.
        if getattr(strategy, "metadata", None) is None or not getattr(strategy.metadata, "unique_names", False):  # type: ignore[union-attr]
            raise RuntimeError("Checkpoint feature requires unique node names in the strategy metadata")

        # If the user already requested an explicit restore/jump, don't override it.
        if ctx.get_agent_context_data() is not None:
            return

        _ = self.rollback_to_latest_checkpoint(ctx, strategy)

    def on_node_execution_completed(
        self,
        *,
        ctx: GraphContext,
        node: Any,
        node_path: str,
        node_input: Any,
        node_output: Any,
        is_technical: bool,
    ) -> None:
        _ = node
        _ = node_output
        if is_technical:
            return
        if not self.config.enable_automatic_persistence:
            return

        agent_id = self._agent_id(ctx)
        parent = self.config.storage.get_latest_checkpoint(agent_id)
        version = (parent.version + 1) if parent is not None else 0
        self.create_checkpoint(ctx=ctx, node_path=node_path, last_input=node_input, version=version)

    def on_strategy_completed(self, *, ctx: GraphContext, strategy: Strategy[Any, Any], result: Any) -> None:
        _ = strategy
        _ = result
        if not self.config.enable_automatic_persistence:
            return
        if self.config.rollback_strategy != RollbackStrategy.Default:
            return

        agent_id = self._agent_id(ctx)
        parent = self.config.storage.get_latest_checkpoint(agent_id)
        version = (parent.version + 1) if parent is not None else 0
        self.create_tombstone_checkpoint(agent_id=agent_id, version=version)

    # ----------------
    # Public operations
    # ----------------

    def create_checkpoint(
        self,
        *,
        ctx: GraphContext,
        node_path: str,
        last_input: Any,
        version: int,
        checkpoint_id: Optional[str] = None,
    ) -> AgentCheckpointData:
        agent_id = self._agent_id(ctx)
        checkpoint = AgentCheckpointData(
            checkpoint_id=str(checkpoint_id or f"cp-{int(time.time() * 1000)}"),
            message_history=self._session_prompt_serializable(ctx),
            node_path=str(node_path or ""),
            last_input_pickle=pickle.dumps(last_input, protocol=pickle.HIGHEST_PROTOCOL) if last_input is not None else b"",
            created_at=time.time(),
            version=int(version),
            tombstone=False,
        )
        self.config.storage.save_checkpoint(agent_id, checkpoint)
        return checkpoint

    def create_tombstone_checkpoint(self, *, agent_id: str, version: int) -> AgentCheckpointData:
        checkpoint = AgentCheckpointData(
            checkpoint_id=f"tombstone-{int(time.time() * 1000)}",
            message_history=[],
            node_path="",
            last_input_pickle=b"",
            created_at=time.time(),
            version=int(version),
            tombstone=True,
        )
        self.config.storage.save_checkpoint(agent_id, checkpoint)
        return checkpoint

    def get_latest_checkpoint(self, *, agent_id: str) -> Optional[AgentCheckpointData]:
        return self.config.storage.get_latest_checkpoint(agent_id)

    def get_checkpoints(self, *, agent_id: str) -> List[AgentCheckpointData]:
        return self.config.storage.get_checkpoints(agent_id)

    def set_execution_point(
        self,
        *,
        ctx: GraphContext,
        node_path: str,
        message_history: List[Dict[str, Any]],
        input_value: Any,
    ) -> None:
        ctx.store_agent_context_data(
            AgentContextData(
                message_history=list(message_history or []),
                node_path=str(node_path or ""),
                last_input=input_value,
                rollback_strategy=self.config.rollback_strategy,
            )
        )

    def rollback_to_latest_checkpoint(self, ctx: GraphContext, strategy: Strategy[Any, Any]) -> Optional[AgentCheckpointData]:
        agent_id = self._agent_id(ctx)
        checkpoint = self.config.storage.get_latest_checkpoint(agent_id)
        if checkpoint is None or checkpoint.is_tombstone():
            return None
        ctx.store_agent_context_data(
            AgentContextData(
                message_history=list(checkpoint.message_history or []),
                node_path=str(checkpoint.node_path or ""),
                last_input=checkpoint.last_input(),
                rollback_strategy=self.config.rollback_strategy,
            )
        )
        return checkpoint

    def rollback_to_checkpoint(
        self,
        *,
        checkpoint_id: str,
        ctx: GraphContext,
        strategy: Strategy[Any, Any],
    ) -> Optional[AgentCheckpointData]:
        agent_id = self._agent_id(ctx)
        all_cps = self.config.storage.get_checkpoints(agent_id)
        checkpoint = next((c for c in all_cps if c.checkpoint_id == checkpoint_id), None)
        if checkpoint is None:
            return None

        additional_actions: List[Callable[[GraphContext], None]] = []

        # Roll back tool side-effects by replaying rollback tools for tool calls after the checkpoint.
        current_hist = self._session_prompt_serializable(ctx)
        diff = self._message_history_diff(current=current_hist, checkpoint=list(checkpoint.message_history or []))
        tool_calls = [m for m in diff if str(m.get("role")) == "tool_call"]
        tool_calls.reverse()

        if tool_calls and self.config.rollback_tool_registry is not None:
            def _rollback(ctx2: GraphContext) -> None:
                _ = ctx2
                for tc in tool_calls:
                    tool_name = str(tc.get("tool") or "")
                    args = dict(tc.get("args") or {})
                    rollback_tool = self.config.rollback_tool_registry.get_rollback_tool(tool_name)
                    if rollback_tool is None:
                        continue
                    try:
                        decoded = rollback_tool.decode_args(args)
                        rollback_tool(decoded)
                    except Exception:
                        continue

            additional_actions.append(_rollback)

        ctx.store_agent_context_data(
            AgentContextData(
                message_history=list(checkpoint.message_history or []),
                node_path=str(checkpoint.node_path or ""),
                last_input=checkpoint.last_input(),
                rollback_strategy=self.config.rollback_strategy,
                additional_rollback_actions=additional_actions,
            )
        )
        return checkpoint


# -----------------------------
# Backwards-compatible helpers
# -----------------------------

def apply_strategy_checkpoint(*, strategy: Strategy[Any, Any], session: Any, checkpoint: AgentCheckpointData) -> None:
    if checkpoint.node_path:
        strategy.set_execution_point(checkpoint.node_path, checkpoint.last_input())
    if hasattr(session, "prompt"):
        session.prompt = checkpoint.prompt()


def make_strategy_checkpoint(*, node_path: str, input_value: Any, session: Any) -> AgentCheckpointData:
    prompt = getattr(session, "prompt", Prompt())
    if isinstance(prompt, Prompt):
        hist = prompt.to_serializable()
    else:
        hist = []
    return AgentCheckpointData(
        checkpoint_id=f"cp-{int(time.time() * 1000)}",
        message_history=hist,
        node_path=node_path,
        last_input_pickle=pickle.dumps(input_value, protocol=pickle.HIGHEST_PROTOCOL) if input_value is not None else b"",
        created_at=time.time(),
        version=0,
        tombstone=False,
    )


