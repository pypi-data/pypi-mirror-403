import subprocess
from pathlib import Path


def perform_command(parts: list[str], cwd: Path | None = None) -> str:
    if cwd is None:
        cwd = Path.cwd()
    return subprocess.run(
        parts,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def get_current_git_branch() -> str:
    return perform_command(parts=["git", "rev-parse", "--show-toplevel"])
