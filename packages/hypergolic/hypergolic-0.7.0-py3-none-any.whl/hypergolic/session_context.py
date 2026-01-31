import subprocess
import uuid
from pathlib import Path

from pydantic import BaseModel

from hypergolic.tools.common import perform_command


class SessionContext(BaseModel):
    agent_branch: str
    base_commit: str
    original_branch: str
    file_browser_root: Path  # Where user launched from (for sidebar UI)
    branch_dirty: bool
    worktree_root: Path  # Isolated worktree where file operations happen
    project_root: Path  # Original repo location (avoid writing here)
    project_name: str
    remote_url: str | None = None


def build_session_context(original_branch: str | None = None) -> SessionContext:
    """Build session context for a new session.

    Args:
        original_branch: If provided, use this as the original branch instead of
            detecting from current HEAD. Used when creating new tabs to ensure
            all sessions branch from the same base (e.g., 'main').
    """
    if original_branch is None:
        original_branch = perform_command(["git", "branch", "--show-current"])

    git_root = perform_command(["git", "rev-parse", "--show-toplevel"])
    git_root_path = Path(git_root)
    session_id = uuid.uuid4().hex[:8]
    agent_branch = f"agent/session-{session_id}"
    project_name = git_root_path.name

    staged_changes = run_subprocess(["git", "diff", "--cached", "--quiet"])
    unstaged_changes = run_subprocess(["git", "diff", "--quiet"])
    # Get base commit from the original branch, not current HEAD
    base_commit = perform_command(["git", "rev-parse", original_branch])
    branch_dirty = staged_changes.returncode != 0 or unstaged_changes.returncode != 0

    remote_url = get_remote_url()

    # Worktree lives in ~/.hypergolic/worktrees/{project}/{session_id}
    worktrees_dir = Path.home() / ".hypergolic" / "worktrees" / project_name
    worktree_root = worktrees_dir / session_id

    return SessionContext(
        agent_branch=agent_branch,
        base_commit=base_commit,
        branch_dirty=branch_dirty,
        original_branch=original_branch,
        file_browser_root=Path.cwd(),
        worktree_root=worktree_root,
        project_root=git_root_path,
        project_name=project_name,
        remote_url=remote_url,
    )


def get_remote_url() -> str | None:
    result = run_subprocess(["git", "remote", "get-url", "origin"])
    if result.returncode == 0:
        url = result.stdout.strip()
        if url:
            return url
    return None


def run_subprocess(parts: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        parts,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
