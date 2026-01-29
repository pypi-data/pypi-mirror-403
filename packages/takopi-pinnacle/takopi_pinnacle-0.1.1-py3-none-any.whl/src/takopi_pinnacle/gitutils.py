from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitInfo:
    repo_root: Path
    branch: str
    head_sha: str
    head_summary: str
    is_dirty: bool


def _run_git(
    repo_root: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc


def git_path(repo_root: Path, git_relpath: str) -> Path:
    """Return a path inside .git, compatible with worktrees."""
    proc = _run_git(repo_root, ["rev-parse", "--git-path", git_relpath])
    path_str = proc.stdout.strip()
    if not path_str:
        raise GitError(f"git rev-parse --git-path {git_relpath} returned empty path.")
    path = Path(path_str)
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    return path


def ensure_local_ignore_dir(repo_root: Path, rel_dir: Path) -> None:
    """Add a local ignore rule for a repo-relative dir (e.g. .pinnacle/)."""
    exclude_file = git_path(repo_root, "info/exclude")
    exclude_file.parent.mkdir(parents=True, exist_ok=True)
    rel_str = rel_dir.as_posix().strip("/")
    rule = f"/{rel_str}/\n"
    existing = ""
    if exclude_file.exists():
        existing = exclude_file.read_text(encoding="utf-8", errors="ignore")
    if rule not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        exclude_file.write_text(existing + rule, encoding="utf-8")


def discover_repo_root(cwd: Path | None = None) -> Path:
    cwd = cwd or Path.cwd()
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GitError("Not a git repository (or git unavailable).")
    return Path(proc.stdout.strip()).resolve()


def get_git_info(repo_root: Path) -> GitInfo:
    branch = _run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    head_sha = _run_git(repo_root, ["rev-parse", "HEAD"]).stdout.strip()
    head_summary = _run_git(repo_root, ["log", "-1", "--pretty=%s"]).stdout.strip()
    status = _run_git(repo_root, ["status", "--porcelain"], check=True).stdout
    return GitInfo(
        repo_root=repo_root,
        branch=branch,
        head_sha=head_sha,
        head_summary=head_summary,
        is_dirty=bool(status.strip()),
    )


def best_effort_base_ref(repo_root: Path) -> str:
    """Pick a sensible base ref for diffs.

    Order:
    1) Upstream tracking branch (@{upstream})
    2) origin/HEAD (e.g. origin/main)
    3) main
    """
    upstream = _run_git(
        repo_root,
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        check=False,
    )
    if upstream.returncode == 0:
        return upstream.stdout.strip()

    origin_head = _run_git(
        repo_root,
        ["symbolic-ref", "refs/remotes/origin/HEAD"],
        check=False,
    )
    if origin_head.returncode == 0:
        # refs/remotes/origin/main -> origin/main
        ref = origin_head.stdout.strip().removeprefix("refs/remotes/")
        return ref

    return "main"


def merge_base(repo_root: Path, base_ref: str) -> str:
    return _run_git(repo_root, ["merge-base", "HEAD", base_ref]).stdout.strip()


def diff_patch(repo_root: Path, *, from_commit: str, to_commit: str = "HEAD") -> str:
    # --binary preserves changes for binary files when possible.
    return _run_git(repo_root, ["diff", "--binary", f"{from_commit}..{to_commit}"]).stdout


def diff_stat(repo_root: Path, *, from_commit: str, to_commit: str = "HEAD") -> str:
    return _run_git(repo_root, ["diff", "--stat", f"{from_commit}..{to_commit}"]).stdout


def dirty_patch(repo_root: Path) -> str:
    """Patch for local (uncommitted) changes vs HEAD."""
    return _run_git(repo_root, ["diff", "--binary"]).stdout


def dirty_cached_patch(repo_root: Path) -> str:
    """Patch for staged changes vs HEAD."""
    return _run_git(repo_root, ["diff", "--binary", "--cached"]).stdout


def list_untracked_files(repo_root: Path) -> list[str]:
    proc = _run_git(repo_root, ["ls-files", "--others", "--exclude-standard"])
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def git_archive_zip(repo_root: Path, *, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "archive", "--format=zip", "-o", str(out_path), "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GitError(f"git archive failed: {proc.stderr.strip()}")
