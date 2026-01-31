import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExplorationResult:
    output: str
    file_count: int
    truncated: bool
    depth_used: int
    error: str | None = None


DEFAULT_MAX_FILES = 500
REDUCED_DEPTH_THRESHOLD = 300


def explore_directory(
    path: str | Path,
    depth: int = 3,
    style: str = "tree",
    respect_gitignore: bool = True,
    max_files: int = DEFAULT_MAX_FILES,
    auto_reduce_depth: bool = True,
) -> ExplorationResult:
    path = Path(path).expanduser().resolve()

    if not path.exists():
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=depth,
            error=f"Path does not exist: {path}",
        )

    if not path.is_dir():
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=depth,
            error=f"Path is not a directory: {path}",
        )

    if style == "flat":
        return _explore_flat(path)

    return _explore_tree(
        path=path,
        depth=depth,
        respect_gitignore=respect_gitignore,
        max_files=max_files,
        auto_reduce_depth=auto_reduce_depth,
    )


def _explore_flat(path: Path) -> ExplorationResult:
    try:
        result = subprocess.run(
            ["ls", "-a", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return ExplorationResult(
                output="",
                file_count=0,
                truncated=False,
                depth_used=1,
                error=result.stderr,
            )

        lines = [
            line
            for line in result.stdout.strip().split("\n")
            if line and line not in (".", "..")
        ]

        return ExplorationResult(
            output=result.stdout,
            file_count=len(lines),
            truncated=False,
            depth_used=1,
        )
    except subprocess.TimeoutExpired:
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=1,
            error="Command timed out",
        )
    except Exception as e:
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=1,
            error=str(e),
        )


def _explore_tree(
    path: Path,
    depth: int,
    respect_gitignore: bool,
    max_files: int,
    auto_reduce_depth: bool,
) -> ExplorationResult:
    current_depth = depth

    while current_depth >= 1:
        result = _run_tree_command(path, current_depth, respect_gitignore)

        if result.error:
            return result

        if (
            auto_reduce_depth
            and result.file_count > REDUCED_DEPTH_THRESHOLD
            and current_depth > 1
        ):
            current_depth -= 1
            continue

        if result.file_count > max_files:
            if auto_reduce_depth and current_depth > 1:
                current_depth -= 1
                continue
            else:
                return ExplorationResult(
                    output=result.output,
                    file_count=result.file_count,
                    truncated=True,
                    depth_used=current_depth,
                )

        return ExplorationResult(
            output=result.output,
            file_count=result.file_count,
            truncated=False,
            depth_used=current_depth,
        )

    return _run_tree_command(path, 1, respect_gitignore)


def _run_tree_command(
    path: Path,
    depth: int,
    respect_gitignore: bool,
) -> ExplorationResult:
    cmd = ["tree", "-L", str(depth), "-a", "--noreport"]
    cmd.extend(["-I", ".git"])

    if respect_gitignore:
        cmd.append("--gitignore")

    cmd.append(str(path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            if respect_gitignore and "--gitignore" in result.stderr:
                return _run_tree_command(path, depth, respect_gitignore=False)

            if "command not found" in result.stderr or result.returncode == 127:
                return _fallback_tree(path, depth)

            return ExplorationResult(
                output="",
                file_count=0,
                truncated=False,
                depth_used=depth,
                error=result.stderr,
            )

        lines = [line for line in result.stdout.strip().split("\n") if line]
        file_count = max(0, len(lines) - 1)

        return ExplorationResult(
            output=result.stdout,
            file_count=file_count,
            truncated=False,
            depth_used=depth,
        )

    except subprocess.TimeoutExpired:
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=depth,
            error="Tree command timed out",
        )
    except FileNotFoundError:
        return _fallback_tree(path, depth)
    except Exception as e:
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=depth,
            error=str(e),
        )


def _fallback_tree(path: Path, depth: int) -> ExplorationResult:
    """Fallback using find when tree is not available. Uses simplified formatting."""
    try:
        cmd = [
            "find",
            str(path),
            "-maxdepth",
            str(depth),
            "-not",
            "-path",
            "*/.git/*",
            "-not",
            "-name",
            ".git",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return ExplorationResult(
                output="",
                file_count=0,
                truncated=False,
                depth_used=depth,
                error=result.stderr,
            )

        lines = sorted(result.stdout.strip().split("\n"))
        formatted_lines = _format_as_tree(lines, path)

        return ExplorationResult(
            output="\n".join(formatted_lines),
            file_count=len(lines) - 1,
            truncated=False,
            depth_used=depth,
        )

    except Exception as e:
        return ExplorationResult(
            output="",
            file_count=0,
            truncated=False,
            depth_used=depth,
            error=f"Fallback tree failed: {e}",
        )


def _format_as_tree(paths: list[str], root: Path) -> list[str]:
    """Format paths as simplified tree structure (always uses '├── ' prefix)."""
    if not paths:
        return []

    result = [str(root)]
    root_str = str(root)

    for filepath in paths:
        if filepath == root_str:
            continue

        rel_path = filepath[len(root_str) :].lstrip("/")
        parts = rel_path.split("/")
        depth = len(parts) - 1

        prefix = "│   " * depth + "├── "
        result.append(f"{prefix}{parts[-1]}")

    return result
