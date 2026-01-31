from __future__ import annotations

import pickle
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class SqliteCheckpointer:
    """
    Minimal SQLite checkpointer to replace LangGraph's SqliteSaver.

    Stores the *latest* state per `thread_id` as a pickled blob (supports Pydantic objects, etc.).
    """

    db_path: Path
    _conn: Optional[sqlite3.Connection] = None

    @classmethod
    def from_conn_string(cls, conn_string: str) -> "SqliteCheckpointer":
        # We keep the name for drop-in compatibility with existing code.
        return cls(db_path=Path(conn_string))

    def __enter__(self) -> "SqliteCheckpointer":
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS koog_checkpoints (
              thread_id TEXT PRIMARY KEY,
              state_blob BLOB NOT NULL,
              updated_at REAL NOT NULL
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

    def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        if not thread_id:
            return None
        if self._conn is None:
            raise RuntimeError("SqliteCheckpointer is not open (use it as a context manager).")

        cur = self._conn.execute(
            "SELECT state_blob FROM koog_checkpoints WHERE thread_id = ?",
            (thread_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        blob = row[0]
        state = pickle.loads(blob)
        if not isinstance(state, dict):
            raise TypeError(f"Checkpoint state must be a dict, got: {type(state)}")
        return state

    def save(self, thread_id: str, state: Dict[str, Any]) -> None:
        if not thread_id:
            return
        if self._conn is None:
            raise RuntimeError("SqliteCheckpointer is not open (use it as a context manager).")

        blob = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        ts = time.time()
        self._conn.execute(
            """
            INSERT INTO koog_checkpoints(thread_id, state_blob, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET
              state_blob = excluded.state_blob,
              updated_at = excluded.updated_at
            """,
            (thread_id, blob, ts),
        )
        self._conn.commit()


