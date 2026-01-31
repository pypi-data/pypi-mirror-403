"""Error logging for Hypergolic.

Logs unhandled exceptions and crashes to ~/.hypergolic/logs/errors/
for post-mortem debugging.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path.home() / ".hypergolic" / "logs" / "errors"

# Keep a single error.log for backward compatibility
LEGACY_LOG_PATH = Path.home() / ".hypergolic" / "logs" / "error.log"


def save_crash_log(exc_type, exc_value, exc_tb) -> None:
    """Save crash information to the error log file.

    Writes to:
    - ~/.hypergolic/logs/errors/error_YYYY-MM-DD_HH-MM-SS.log (individual crash file)
    - ~/.hypergolic/logs/error.log (appended, for backward compatibility)

    Args:
        exc_type: The exception type.
        exc_value: The exception instance.
        exc_tb: The traceback object.
    """
    # Ensure log directories exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Format the crash log entry
    timestamp = datetime.now()
    timestamp_str = timestamp.isoformat()
    timestamp_file = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_str = "".join(tb_lines)

    crash_entry = f"""================================================================================
CRASH REPORT: {timestamp_str}
================================================================================
Exception Type: {exc_type.__name__}
Exception Message: {exc_value}

Traceback:
{tb_str}
"""

    # Write individual crash file
    crash_file = LOGS_DIR / f"error_{timestamp_file}.log"
    try:
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(crash_entry)
    except OSError:
        pass  # Don't fail if we can't write

    # Append to legacy log file
    try:
        with open(LEGACY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + crash_entry)
    except OSError:
        pass

    print(f"\nCrash logged to: {crash_file}", file=sys.stderr)

    # Clean up old logs
    cleanup_old_logs()


def get_crash_log_path() -> Path:
    """Get the path to the crash log file (legacy single-file path)."""
    return LEGACY_LOG_PATH


def cleanup_old_logs(max_age_days: int = 30, max_files: int = 100) -> None:
    """Remove old error logs to prevent unbounded growth.

    Keeps at most max_files logs, and removes any older than max_age_days.
    """
    if not LOGS_DIR.exists():
        return

    log_files = sorted(LOGS_DIR.glob("error_*.log"), key=lambda p: p.stat().st_mtime)

    # Remove files exceeding max count (keep newest)
    if len(log_files) > max_files:
        for old_file in log_files[: len(log_files) - max_files]:
            try:
                old_file.unlink()
            except OSError:
                pass
        # Update list after deletion
        log_files = log_files[len(log_files) - max_files :]

    # Remove files older than max_age_days
    cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
    for log_file in log_files:
        try:
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
        except OSError:
            pass
