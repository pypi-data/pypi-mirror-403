import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum

from hypergolic.session_context import SessionContext


class BranchCleanupResult(Enum):
    DELETED = "deleted"
    MERGED = "merged"
    PRESERVED = "preserved"
    NOT_FOUND = "not_found"


class WorktreeCleanupResult(Enum):
    DELETED = "deleted"
    MERGED = "merged"
    PRESERVED = "preserved"
    NOT_FOUND = "not_found"


class FileStatus(Enum):
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNKNOWN = "?"


@dataclass
class MergeResult:
    success: bool
    error_message: str | None = None


@dataclass
class FileDiff:
    path: str
    additions: int
    deletions: int
    status: FileStatus
    diff_content: str = ""
    old_path: str | None = None


@dataclass
class CommitInfo:
    sha: str
    message: str


@dataclass
class MergeDiffData:
    files: list[FileDiff] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    commit_count: int = 0
    commits: list[CommitInfo] = field(default_factory=list)
    agent_branch: str = ""
    original_branch: str = ""


_FILE_STATUS_MAP = {
    "A": FileStatus.ADDED,
    "M": FileStatus.MODIFIED,
    "D": FileStatus.DELETED,
    "R": FileStatus.RENAMED,
    "C": FileStatus.COPIED,
}


def get_merge_diff(session_context: SessionContext) -> MergeDiffData | None:
    if not branch_has_changes(session_context):
        return None

    diff_data = MergeDiffData(
        agent_branch=session_context.agent_branch,
        original_branch=session_context.original_branch,
    )

    diff_data.commits = _get_commits_since_base(session_context)
    diff_data.commit_count = len(diff_data.commits)

    file_stats = _get_diff_numstat(session_context)

    for path, additions, deletions, status, old_path in file_stats:
        file_diff = FileDiff(
            path=path,
            additions=additions,
            deletions=deletions,
            status=status,
            old_path=old_path,
            diff_content=_get_file_diff(session_context, path, old_path),
        )
        diff_data.files.append(file_diff)
        diff_data.total_additions += additions
        diff_data.total_deletions += deletions

    return diff_data


def _get_commits_since_base(
    session_context: SessionContext,
) -> list[CommitInfo]:
    result = subprocess.run(
        [
            "git",
            "log",
            "--oneline",
            "--reverse",
            f"{session_context.base_commit}..{session_context.agent_branch}",
        ],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            sha = parts[0]
            message = parts[1] if len(parts) > 1 else ""
            commits.append(CommitInfo(sha=sha, message=message))
    return commits


def _get_diff_numstat(
    session_context: SessionContext,
) -> list[tuple[str, int, int, FileStatus, str | None]]:
    numstat_result = subprocess.run(
        [
            "git",
            "diff",
            "--numstat",
            f"{session_context.base_commit}..{session_context.agent_branch}",
        ],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )

    status_result = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            f"{session_context.base_commit}..{session_context.agent_branch}",
        ],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )

    if numstat_result.returncode != 0:
        return []

    status_map: dict[str, tuple[FileStatus, str | None]] = {}
    for line in status_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            status_char = parts[0][0]
            status = _parse_file_status(status_char)
            if status == FileStatus.RENAMED and len(parts) >= 3:
                old_path = parts[1]
                new_path = parts[2]
                status_map[new_path] = (status, old_path)
            else:
                status_map[parts[1]] = (status, None)

    files = []
    for line in numstat_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                additions = int(parts[0]) if parts[0] != "-" else 0
                deletions = int(parts[1]) if parts[1] != "-" else 0
            except ValueError:
                additions = 0
                deletions = 0

            path = parts[2]
            if " => " in path:
                path = _parse_rename_path(path)

            status, old_path = status_map.get(path, (FileStatus.MODIFIED, None))
            files.append((path, additions, deletions, status, old_path))

    return files


def _parse_file_status(char: str) -> FileStatus:
    return _FILE_STATUS_MAP.get(char, FileStatus.UNKNOWN)


def _parse_rename_path(path: str) -> str:
    # Handles "prefix/{old => new}/suffix" and "old => new" formats
    if "{" in path and "}" in path:
        match = re.match(r"(.*)\{.* => (.*)\}(.*)", path)
        if match:
            prefix = match.group(1) or ""
            new_name = match.group(2)
            suffix = match.group(3) or ""
            return f"{prefix}{new_name}{suffix}"
    elif " => " in path:
        return path.split(" => ")[1]
    return path


def _get_file_diff(
    session_context: SessionContext,
    path: str,
    old_path: str | None = None,
) -> str:
    cmd = [
        "git",
        "diff",
        f"{session_context.base_commit}..{session_context.agent_branch}",
        "--",
    ]

    if old_path:
        cmd.extend([old_path, path])
    else:
        cmd.append(path)

    result = subprocess.run(
        cmd,
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def stash_dirty_branch(session_context: SessionContext):
    if not session_context.branch_dirty:
        return

    subprocess.run(
        [
            "git",
            "stash",
            "push",
            "-m",
            f'"stash for agent work: {session_context.agent_branch}"',
        ],
        cwd=session_context.project_root,
        check=True,
    )


def unstash_dirty_branch(session_context: SessionContext):
    if not session_context.branch_dirty:
        return
    subprocess.run(["git", "stash", "pop"], cwd=session_context.project_root, check=True)


def create_agent_branch(session_context: SessionContext) -> bool:
    """Create the agent branch. Returns True on success, False if it already exists."""
    result = subprocess.run(
        ["git", "branch", session_context.agent_branch, session_context.base_commit],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def checkout_agent_branch(session_context: SessionContext):
    subprocess.run(
        ["git", "checkout", session_context.agent_branch],
        cwd=session_context.worktree_root,
        check=True,
    )


def checkout_original_branch(session_context: SessionContext):
    subprocess.run(
        ["git", "checkout", session_context.original_branch],
        cwd=session_context.project_root,
        check=True,
    )


# Worktree management


def create_worktree(session_context: SessionContext) -> bool:
    """Create a git worktree for this session.

    Creates a worktree at session_context.worktree_root with the agent branch.
    The branch is created first, then a worktree is added pointing to it.
    """
    # Ensure the parent directory exists
    session_context.worktree_root.parent.mkdir(parents=True, exist_ok=True)

    # Create the branch first
    if not create_agent_branch(session_context):
        # Branch might already exist from a previous interrupted session
        # Prune any orphaned worktree references first, then try to delete and recreate
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=session_context.project_root,
            capture_output=True,
        )
        force_delete_agent_branch(session_context)
        if not create_agent_branch(session_context):
            return False

    # Create worktree with the branch
    result = subprocess.run(
        [
            "git",
            "worktree",
            "add",
            str(session_context.worktree_root),
            session_context.agent_branch,
        ],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Cleanup the branch we created if worktree creation failed
        force_delete_agent_branch(session_context)
        return False
    return True


def remove_worktree(session_context: SessionContext) -> bool:
    """Remove the git worktree for this session."""
    if not session_context.worktree_root.exists():
        return True  # Already removed

    result = subprocess.run(
        [
            "git",
            "worktree",
            "remove",
            str(session_context.worktree_root),
            "--force",
        ],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def cleanup_worktree(
    session_context: SessionContext,
    merge_if_changes: bool = False,
) -> WorktreeCleanupResult:
    """Clean up the worktree and optionally merge changes.

    This removes the worktree and either merges or preserves the branch.
    """
    agent_head = _get_branch_head(session_context)

    if agent_head is None:
        remove_worktree(session_context)
        return WorktreeCleanupResult.NOT_FOUND

    # Check if branch has no changes or is already merged
    if agent_head == session_context.base_commit or is_branch_merged(session_context):
        remove_worktree(session_context)
        if delete_agent_branch(session_context):
            return WorktreeCleanupResult.DELETED
        return WorktreeCleanupResult.PRESERVED

    # Branch has changes - remove worktree first
    remove_worktree(session_context)

    if merge_if_changes:
        merge_result = merge_agent_branch(session_context)
        if merge_result.success:
            delete_agent_branch(session_context)
            return WorktreeCleanupResult.MERGED

    return WorktreeCleanupResult.PRESERVED


def _get_branch_head(session_context: SessionContext) -> str | None:
    """Get the HEAD commit of the agent branch.

    Works from either the worktree or main repo.
    """
    result = subprocess.run(
        ["git", "rev-parse", session_context.agent_branch],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_branch_merged(session_context: SessionContext) -> bool:
    """Check if agent branch is merged into original branch."""
    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            session_context.agent_branch,
            session_context.original_branch,
        ],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def has_uncommitted_changes(session_context: SessionContext) -> bool:
    """Check if the working tree has uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def has_committed_changes(session_context: SessionContext) -> bool:
    """Check if the branch has commits beyond the base commit."""
    agent_head = _get_branch_head(session_context)
    if agent_head is None:
        return False
    return agent_head != session_context.base_commit


def branch_has_changes(session_context: SessionContext) -> bool:
    """Check if the branch has any changes (committed or uncommitted) vs the base."""
    return has_uncommitted_changes(session_context) or has_committed_changes(session_context)


def commit_all_changes(session_context: SessionContext, message: str) -> bool:
    """Stage and commit all changes in the working tree."""
    # Stage all changes
    add_result = subprocess.run(
        ["git", "add", "-A"],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    if add_result.returncode != 0:
        return False

    # Commit
    commit_result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    return commit_result.returncode == 0


def discard_uncommitted_changes(session_context: SessionContext) -> bool:
    """Discard all uncommitted changes in the working tree."""
    # Reset staged changes
    reset_result = subprocess.run(
        ["git", "reset", "--hard", "HEAD"],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    if reset_result.returncode != 0:
        return False

    # Clean untracked files
    clean_result = subprocess.run(
        ["git", "clean", "-fd"],
        cwd=session_context.worktree_root,
        capture_output=True,
        text=True,
    )
    return clean_result.returncode == 0


def merge_agent_branch(session_context: SessionContext) -> MergeResult:
    """Merge the agent branch into the original branch.

    This operates on the main git root, not the worktree.
    """
    agent_head = _get_branch_head(session_context)
    if agent_head is None or agent_head == session_context.base_commit:
        return MergeResult(success=False, error_message="No changes to merge")

    checkout_result = subprocess.run(
        ["git", "checkout", session_context.original_branch],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    if checkout_result.returncode != 0:
        return MergeResult(
            success=False,
            error_message=f"Failed to checkout {session_context.original_branch}: {checkout_result.stderr.strip()}",
        )

    merge_result = subprocess.run(
        ["git", "merge", session_context.agent_branch, "--no-edit"],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    if merge_result.returncode != 0:
        subprocess.run(
            ["git", "merge", "--abort"],
            cwd=session_context.project_root,
            check=False,
        )
        return MergeResult(
            success=False,
            error_message=f"Merge failed (possible conflicts): {merge_result.stderr.strip()}",
        )

    return MergeResult(success=True)


def delete_agent_branch(session_context: SessionContext) -> bool:
    """Delete the agent branch (must not have a worktree attached)."""
    result = subprocess.run(
        ["git", "branch", "-d", session_context.agent_branch],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def force_delete_agent_branch(session_context: SessionContext) -> bool:
    """Force delete the agent branch (must not have a worktree attached)."""
    result = subprocess.run(
        ["git", "branch", "-D", session_context.agent_branch],
        cwd=session_context.project_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def cleanup_agent_branch(
    session_context: SessionContext,
    merge_if_changes: bool = False,
) -> BranchCleanupResult:
    agent_head = _get_branch_head(session_context)

    if agent_head is None:
        return BranchCleanupResult.NOT_FOUND

    if agent_head == session_context.base_commit or is_branch_merged(session_context):
        if delete_agent_branch(session_context):
            return BranchCleanupResult.DELETED
        return BranchCleanupResult.PRESERVED

    if merge_if_changes:
        merge_result = merge_agent_branch(session_context)
        if merge_result.success:
            delete_agent_branch(session_context)
            return BranchCleanupResult.MERGED

    return BranchCleanupResult.PRESERVED
