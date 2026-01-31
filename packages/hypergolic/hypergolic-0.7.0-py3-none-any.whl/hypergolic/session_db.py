"""
SQLite-based session history storage.

Stores session logs in a normalized SQLite database for efficient querying
and analytics across sessions.
"""

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from hypergolic.session_schema import MIGRATIONS, SCHEMA, SCHEMA_VERSION

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".hypergolic" / "sessions.db"

_db_initialized: set[Path] = set()


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Get a database connection with foreign keys enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def get_schema_version(db_path: Path = DB_PATH) -> int | None:
    """Get the current schema version, or None if DB doesn't exist."""
    if not db_path.exists():
        return None

    with get_connection(db_path) as conn:
        try:
            cursor = conn.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            )
            row = cursor.fetchone()
            return int(row["value"]) if row else None
        except sqlite3.OperationalError:
            return None


def _run_migrations(conn: sqlite3.Connection, from_version: int) -> None:
    """Run migrations from from_version to SCHEMA_VERSION."""
    current = from_version
    while current < SCHEMA_VERSION:
        next_version = current + 1
        key = (current, next_version)
        if key not in MIGRATIONS:
            raise ValueError(f"No migration path from v{current} to v{next_version}")

        logger.info("Migrating database from v%d to v%d", current, next_version)
        for statement in MIGRATIONS[key].strip().split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(statement)

        current = next_version

    conn.execute(
        "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize the database schema, running migrations if needed."""
    current_version = get_schema_version(db_path)

    with get_connection(db_path) as conn:
        if current_version is None:
            # Fresh database
            conn.executescript(SCHEMA)
            conn.execute(
                "INSERT INTO schema_meta (key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
            conn.execute(
                "INSERT INTO schema_meta (key, value) VALUES (?, ?)",
                ("created_at", datetime.now().isoformat()),
            )
            conn.commit()
            logger.info(
                "Database initialized at %s (schema v%d)", db_path, SCHEMA_VERSION
            )
        elif current_version < SCHEMA_VERSION:
            _run_migrations(conn, current_version)
            logger.info(
                "Database migrated to v%d at %s", SCHEMA_VERSION, db_path
            )


def save_session(
    session_id: str,
    metadata: dict[str, Any],
    segments: list[dict[str, Any]],
    db_path: Path = DB_PATH,
) -> None:
    """Save a complete session to the database."""
    if db_path not in _db_initialized:
        init_db(db_path)
        _db_initialized.add(db_path)

    with get_connection(db_path) as conn:
        # Calculate final stats from last segment
        final_stats = segments[-1].get("stats", {}) if segments else {}

        # Insert session
        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (
                id, created_at, project, agent_branch, original_branch,
                base_commit, git_root, remote_url,
                final_context_tokens, final_output_tokens,
                final_cache_read_tokens, final_cache_creation_tokens,
                final_cost_usd, final_message_count, final_tool_count,
                final_summarization_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                metadata.get("timestamp"),
                metadata.get("project"),
                metadata.get("branch"),
                metadata.get("original_branch"),
                metadata.get("base_commit"),
                metadata.get("git_root"),
                metadata.get("remote_url"),
                final_stats.get("context_tokens"),
                final_stats.get("output_tokens"),
                final_stats.get("cache_read_tokens"),
                final_stats.get("cache_creation_tokens"),
                final_stats.get("cost_usd"),
                final_stats.get("message_count"),
                final_stats.get("tool_count"),
                final_stats.get("summarization_count"),
            ),
        )

        # Delete existing segments for this session (for updates)
        conn.execute("DELETE FROM segments WHERE session_id = ?", (session_id,))

        # Insert segments
        for segment in segments:
            _insert_segment(conn, session_id, segment)

        conn.commit()


def _insert_segment(
    conn: sqlite3.Connection,
    session_id: str,
    segment: dict[str, Any],
) -> int:
    """Insert a segment and its messages. Returns segment ID."""
    stats = segment.get("stats", {})

    cursor = conn.execute(
        """
        INSERT INTO segments (
            session_id, segment_index, timestamp, is_post_summarization,
            context_tokens, output_tokens, cache_read_tokens,
            cache_creation_tokens, cost_usd, message_count,
            tool_count, summarization_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            segment.get("segment_index", 0),
            segment.get("timestamp"),
            1 if segment.get("is_post_summarization") else 0,
            stats.get("context_tokens"),
            stats.get("output_tokens"),
            stats.get("cache_read_tokens"),
            stats.get("cache_creation_tokens"),
            stats.get("cost_usd"),
            stats.get("message_count"),
            stats.get("tool_count"),
            stats.get("summarization_count"),
        ),
    )
    segment_id = cursor.lastrowid
    assert segment_id is not None

    # Insert messages
    for msg_index, message in enumerate(segment.get("messages", [])):
        _insert_message(conn, segment_id, msg_index, message)

    # Insert sub-agent traces if present
    for agent_id, trace_data in segment.get("sub_agent_traces", {}).items():
        conn.execute(
            """
            INSERT INTO sub_agent_traces (segment_id, agent_id, trace_data)
            VALUES (?, ?, ?)
            """,
            (segment_id, agent_id, json.dumps(trace_data)),
        )

    return segment_id


def _insert_message(
    conn: sqlite3.Connection,
    segment_id: int,
    msg_index: int,
    message: dict[str, Any],
) -> int:
    """Insert a message and its content blocks. Returns message ID."""
    snapshot = message.get("usage_snapshot", {})

    cursor = conn.execute(
        """
        INSERT INTO messages (
            segment_id, message_index, role, content_length,
            snapshot_context_tokens, snapshot_output_tokens,
            snapshot_cache_read_tokens, snapshot_cache_creation_tokens,
            snapshot_cost_usd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            segment_id,
            msg_index,
            message.get("role"),
            message.get("content_length"),
            snapshot.get("context_tokens"),
            snapshot.get("output_tokens"),
            snapshot.get("cache_read_tokens"),
            snapshot.get("cache_creation_tokens"),
            snapshot.get("cost_usd"),
        ),
    )
    message_id = cursor.lastrowid
    assert message_id is not None

    # Insert content blocks
    content = message.get("content", [])
    if isinstance(content, str):
        # Simple string content
        conn.execute(
            """
            INSERT INTO content_blocks (
                message_id, block_index, block_type, content_length, text_content
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, 0, "text", len(content), content),
        )
    elif isinstance(content, list):
        for block_index, block in enumerate(content):
            _insert_content_block(conn, message_id, block_index, block)

    return message_id


def _insert_content_block(
    conn: sqlite3.Connection,
    message_id: int,
    block_index: int,
    block: dict[str, Any],
) -> None:
    """Insert a content block."""
    block_type = block.get("type", "unknown")

    # Extract tool result content for v2 fields
    tool_result_content = None
    tool_result_length = None
    if block_type == "tool_result":
        raw_content = block.get("content")
        if isinstance(raw_content, str):
            tool_result_content = raw_content[:1000]  # Truncate for storage
            tool_result_length = len(raw_content)
        elif isinstance(raw_content, list):
            # Concatenate text blocks
            texts = []
            total_len = 0
            for item in raw_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    texts.append(text)
                    total_len += len(text)
            if texts:
                full_text = "\n".join(texts)
                tool_result_content = full_text[:1000]
                tool_result_length = total_len

    conn.execute(
        """
        INSERT INTO content_blocks (
            message_id, block_index, block_type, content_length,
            text_content, tool_use_id, tool_name, tool_input,
            tool_result_id, is_error,
            tool_result_content, tool_result_length, execution_duration_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            block_index,
            block_type,
            block.get("content_length"),
            block.get("text") if block_type == "text" else None,
            block.get("id") if block_type == "tool_use" else None,
            block.get("name") if block_type == "tool_use" else None,
            json.dumps(block.get("input")) if block_type == "tool_use" and block.get("input") else None,
            block.get("tool_use_id") if block_type == "tool_result" else None,
            1 if block.get("is_error") else 0 if block_type == "tool_result" else None,
            tool_result_content,
            tool_result_length,
            block.get("execution_duration_ms"),
        ),
    )


# Query helpers


def get_all_sessions(
    db_path: Path = DB_PATH,
    project: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Get all sessions, optionally filtered by project."""
    if not db_path.exists():
        return []

    with get_connection(db_path) as conn:
        query = "SELECT * FROM sessions"
        params: list[Any] = []

        if project:
            query += " WHERE project = ?"
            params.append(project)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_session(session_id: str, db_path: Path = DB_PATH) -> dict[str, Any] | None:
    """Get a complete session with all segments and messages."""
    if not db_path.exists():
        return None

    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session_row = cursor.fetchone()
        if not session_row:
            return None

        session = dict(session_row)
        session["segments"] = []

        cursor = conn.execute(
            "SELECT * FROM segments WHERE session_id = ? ORDER BY segment_index",
            (session_id,),
        )
        for seg_row in cursor.fetchall():
            segment = dict(seg_row)
            segment["messages"] = _get_segment_messages(conn, segment["id"])
            segment["sub_agent_traces"] = _get_segment_traces(conn, segment["id"])
            session["segments"].append(segment)

        return session


def _get_segment_messages(conn: sqlite3.Connection, segment_id: int) -> list[dict]:
    """Get all messages for a segment with their content blocks."""
    cursor = conn.execute(
        "SELECT * FROM messages WHERE segment_id = ? ORDER BY message_index",
        (segment_id,),
    )
    messages = []
    for msg_row in cursor.fetchall():
        message = dict(msg_row)
        message["content"] = _get_message_content(conn, message["id"])
        messages.append(message)
    return messages


def _get_message_content(conn: sqlite3.Connection, message_id: int) -> list[dict]:
    """Get content blocks for a message."""
    cursor = conn.execute(
        "SELECT * FROM content_blocks WHERE message_id = ? ORDER BY block_index",
        (message_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _get_segment_traces(conn: sqlite3.Connection, segment_id: int) -> dict[str, Any]:
    """Get sub-agent traces for a segment."""
    cursor = conn.execute(
        "SELECT agent_id, trace_data FROM sub_agent_traces WHERE segment_id = ?",
        (segment_id,),
    )
    return {row["agent_id"]: json.loads(row["trace_data"]) for row in cursor.fetchall()}


def get_total_cost(db_path: Path = DB_PATH, project: str | None = None) -> float:
    """Get total cost across all sessions, optionally filtered by project."""
    if not db_path.exists():
        return 0.0

    with get_connection(db_path) as conn:
        query = "SELECT SUM(final_cost_usd) as total FROM sessions"
        params: list[Any] = []

        if project:
            query += " WHERE project = ?"
            params.append(project)

        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return row["total"] or 0.0 if row else 0.0


def get_tool_usage_stats(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    """Get tool usage statistics across all sessions."""
    if not db_path.exists():
        return []

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT tool_name, COUNT(*) as count
            FROM content_blocks
            WHERE tool_name IS NOT NULL
            GROUP BY tool_name
            ORDER BY count DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_expensive_tool_results(
    db_path: Path = DB_PATH,
    min_length: int = 5000,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Get tool results with large content for efficiency analysis."""
    if not db_path.exists():
        return []

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT
                cb.tool_result_id,
                cb.tool_result_length,
                cb.tool_result_content,
                prev_cb.tool_name,
                s.project,
                s.id as session_id
            FROM content_blocks cb
            JOIN messages m ON cb.message_id = m.id
            JOIN segments seg ON m.segment_id = seg.id
            JOIN sessions s ON seg.session_id = s.id
            LEFT JOIN content_blocks prev_cb ON prev_cb.tool_use_id = cb.tool_result_id
            WHERE cb.block_type = 'tool_result'
              AND cb.tool_result_length > ?
            ORDER BY cb.tool_result_length DESC
            LIMIT ?
            """,
            (min_length, limit),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_session_start_patterns(
    db_path: Path = DB_PATH,
    first_n_tools: int = 5,
) -> list[dict[str, Any]]:
    """Analyze which tools are called at the start of sessions."""
    if not db_path.exists():
        return []

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT tool_name, COUNT(*) as frequency
            FROM (
                SELECT cb.tool_name, m.message_index, seg.session_id
                FROM content_blocks cb
                JOIN messages m ON cb.message_id = m.id
                JOIN segments seg ON m.segment_id = seg.id
                WHERE cb.tool_name IS NOT NULL
                  AND seg.segment_index = 0
                  AND m.message_index < ?
            )
            GROUP BY tool_name
            ORDER BY frequency DESC
            """,
            (first_n_tools * 2,),  # *2 to account for user/assistant pairs
        )
        return [dict(row) for row in cursor.fetchall()]
