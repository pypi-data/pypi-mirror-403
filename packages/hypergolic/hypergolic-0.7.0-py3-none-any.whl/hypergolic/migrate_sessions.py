#!/usr/bin/env python3
"""
Migrate existing JSON session logs to SQLite database.

Usage:
    python -m hypergolic.migrate_sessions [--dry-run] [--keep-json]

Options:
    --dry-run    Show what would be migrated without making changes
    --keep-json  Don't delete JSON files after successful migration
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from hypergolic.session_db import DB_PATH, init_db, save_session

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

SESSION_LOGS_DIR = Path.home() / ".hypergolic" / "logs" / "sessions"


def parse_session_id_from_filename(filename: str) -> str:
    """Extract session ID from filename like '2026-01-28_01-11-43_hypergolic_0d6fcd41.json'."""
    return filename.removesuffix(".json")


def migrate_json_file(filepath: Path) -> tuple[str, bool, str]:
    """Migrate a single JSON file to the database. Returns (session_id, success, message)."""
    session_id = parse_session_id_from_filename(filepath.name)

    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return session_id, False, f"Invalid JSON: {e}"
    except Exception as e:
        return session_id, False, f"Read error: {e}"

    # Handle both old format (flat) and new format (with segments)
    if "segments" in data:
        metadata = data.get("metadata", {})
        segments = data.get("segments", [])
    else:
        # Old format: convert to segments format
        metadata = data.get("metadata", {})
        segments = [
            {
                "segment_index": 0,
                "timestamp": metadata.get("timestamp"),
                "stats": data.get("stats", {}),
                "messages": data.get("messages", []),
                "sub_agent_traces": data.get("sub_agent_traces") or {},
            }
        ]

    try:
        save_session(session_id, metadata, segments)
        return session_id, True, "OK"
    except Exception as e:
        return session_id, False, f"DB error: {e}"


def get_json_files() -> list[Path]:
    """Get all JSON session files."""
    if not SESSION_LOGS_DIR.exists():
        return []
    return sorted(SESSION_LOGS_DIR.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate JSON session logs to SQLite database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--delete-json",
        action="store_true",
        help="Delete JSON files after successful migration (default: keep them)",
    )
    args = parser.parse_args()

    json_files = get_json_files()

    if not json_files:
        logger.info("No JSON session files found in %s", SESSION_LOGS_DIR)
        return 0

    logger.info("Found %d JSON session files", len(json_files))

    if args.dry_run:
        logger.info("\n[DRY RUN] Would migrate:")
        for f in json_files:
            size_kb = f.stat().st_size / 1024
            logger.info("  %s (%.1f KB)", f.name, size_kb)
        logger.info("\nDatabase would be created at: %s", DB_PATH)
        return 0

    # Initialize database
    logger.info("Initializing database at %s", DB_PATH)
    init_db()

    # Migrate files
    success_count = 0
    error_count = 0
    migrated_files: list[Path] = []

    logger.info("\nMigrating sessions...")
    for filepath in json_files:
        session_id, success, message = migrate_json_file(filepath)

        if success:
            success_count += 1
            migrated_files.append(filepath)
            logger.info("  ✓ %s", filepath.name)
        else:
            error_count += 1
            logger.error("  ✗ %s: %s", filepath.name, message)

    logger.info("\nMigration complete: %d succeeded, %d failed", success_count, error_count)

    # Calculate total size
    total_size = sum(f.stat().st_size for f in migrated_files)
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    logger.info("JSON total: %.1f KB -> DB size: %.1f KB", total_size / 1024, db_size / 1024)

    # Delete JSON files if requested
    if args.delete_json and migrated_files:
        logger.info("\nRemoving migrated JSON files...")
        for filepath in migrated_files:
            filepath.unlink()
            logger.info("  Deleted %s", filepath.name)

        # Remove empty directory
        if SESSION_LOGS_DIR.exists() and not any(SESSION_LOGS_DIR.iterdir()):
            SESSION_LOGS_DIR.rmdir()
            logger.info("Removed empty directory: %s", SESSION_LOGS_DIR)
    elif migrated_files:
        logger.info("\nJSON files kept (use --delete-json to remove)")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
