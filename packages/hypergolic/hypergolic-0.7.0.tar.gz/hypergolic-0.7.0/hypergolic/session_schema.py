"""
SQLite schema definitions for session history storage.

Schema v2 adds efficiency analysis fields to content_blocks:
- tool_result_content: truncated tool result text
- tool_result_length: full length before truncation
- execution_duration_ms: tool execution time
"""

SCHEMA_VERSION = 2

SCHEMA = """
-- Schema metadata for migrations
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Core session metadata
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    project TEXT NOT NULL,
    agent_branch TEXT NOT NULL,
    original_branch TEXT NOT NULL,
    base_commit TEXT NOT NULL,
    git_root TEXT NOT NULL,
    remote_url TEXT,
    -- Denormalized final stats (for fast queries)
    final_context_tokens INTEGER,
    final_output_tokens INTEGER,
    final_cache_read_tokens INTEGER,
    final_cache_creation_tokens INTEGER,
    final_cost_usd REAL,
    final_message_count INTEGER,
    final_tool_count INTEGER,
    final_summarization_count INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_cost ON sessions(final_cost_usd);

-- Segments (for summarization boundaries)
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    is_post_summarization INTEGER DEFAULT 0,
    -- Segment-level stats snapshot
    context_tokens INTEGER,
    output_tokens INTEGER,
    cache_read_tokens INTEGER,
    cache_creation_tokens INTEGER,
    cost_usd REAL,
    message_count INTEGER,
    tool_count INTEGER,
    summarization_count INTEGER,
    UNIQUE(session_id, segment_index)
);

-- Individual messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    content_length INTEGER,
    -- Usage snapshot (for assistant messages)
    snapshot_context_tokens INTEGER,
    snapshot_output_tokens INTEGER,
    snapshot_cache_read_tokens INTEGER,
    snapshot_cache_creation_tokens INTEGER,
    snapshot_cost_usd REAL,
    UNIQUE(segment_id, message_index)
);

CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- Content blocks (the actual message content)
CREATE TABLE IF NOT EXISTS content_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    block_index INTEGER NOT NULL,
    block_type TEXT NOT NULL,
    content_length INTEGER,
    -- Type-specific fields (sparse columns)
    text_content TEXT,
    tool_use_id TEXT,
    tool_name TEXT,
    tool_input TEXT,
    tool_result_id TEXT,
    is_error INTEGER,
    -- v2: efficiency analysis fields
    tool_result_content TEXT,
    tool_result_length INTEGER,
    execution_duration_ms INTEGER,
    UNIQUE(message_id, block_index)
);

CREATE INDEX IF NOT EXISTS idx_content_blocks_tool_name ON content_blocks(tool_name);
CREATE INDEX IF NOT EXISTS idx_content_blocks_type ON content_blocks(block_type);

-- Sub-agent traces
CREATE TABLE IF NOT EXISTS sub_agent_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    trace_data TEXT NOT NULL,
    UNIQUE(segment_id, agent_id)
);
"""

# Migration from v1 to v2
MIGRATIONS = {
    (1, 2): """
        ALTER TABLE content_blocks ADD COLUMN tool_result_content TEXT;
        ALTER TABLE content_blocks ADD COLUMN tool_result_length INTEGER;
        ALTER TABLE content_blocks ADD COLUMN execution_duration_ms INTEGER;
    """,
}


def get_migration_path(from_version: int, to_version: int) -> list[str]:
    """Get list of migration scripts to run from one version to another."""
    scripts = []
    current = from_version
    while current < to_version:
        next_version = current + 1
        key = (current, next_version)
        if key not in MIGRATIONS:
            raise ValueError(f"No migration path from v{current} to v{next_version}")
        scripts.append(MIGRATIONS[key])
        current = next_version
    return scripts
