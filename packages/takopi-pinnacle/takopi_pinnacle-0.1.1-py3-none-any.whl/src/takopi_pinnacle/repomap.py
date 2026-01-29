from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .gitutils import _run_git


@dataclass(frozen=True)
class RepoMapConfig:
    max_repo_files: int = 8000
    max_top_level_entries: int = 80


def _top_level(path: str) -> str:
    parts = path.split("/", 1)
    return parts[0] + ("/" if len(parts) > 1 else "")


def list_tracked_files(repo_root: Path, max_files: int) -> list[str]:
    """Return tracked file paths (POSIX) relative to repo root."""
    proc = _run_git(repo_root, ["ls-files"]).stdout
    files = [line.strip() for line in proc.splitlines() if line.strip()]
    if len(files) > max_files:
        # Deterministic: keep lexical order and truncate.
        files = sorted(files)[:max_files]
    return files


def extension_histogram(paths: list[str]) -> Counter[str]:
    exts: list[str] = []
    for p in paths:
        name = p.rsplit("/", 1)[-1]
        if "." not in name or name.startswith("."):
            continue
        exts.append(name.rsplit(".", 1)[-1].lower())
    return Counter(exts)


def top_level_summary(paths: list[str]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter(_top_level(p) for p in paths)
    # Sort: most files first, then name.
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def find_present_files(repo_root: Path, candidates: list[str]) -> list[str]:
    present: list[str] = []
    for rel in candidates:
        if (repo_root / rel).exists():
            present.append(rel)
    return present


def render_repo_map(repo_root: Path, cfg: RepoMapConfig) -> str:
    paths = list_tracked_files(repo_root, cfg.max_repo_files)
    total_files = len(paths)
    top = top_level_summary(paths)[: cfg.max_top_level_entries]
    ext_hist = extension_histogram(paths)

    key_files = find_present_files(
        repo_root,
        [
            "pyproject.toml",
            "poetry.lock",
            "uv.lock",
            "requirements.txt",
            "Pipfile",
            "setup.cfg",
            "setup.py",
            "tox.ini",
            "package.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "Cargo.toml",
            "go.mod",
            "Makefile",
            "Justfile",
            "Dockerfile",
            ".github/workflows",
            "README.md",
        ],
    )

    lines: list[str] = []
    lines.append("# Repo map")
    lines.append("")
    lines.append(f"Tracked files (capped): **{total_files}**")
    if total_files >= cfg.max_repo_files:
        lines.append(f"(Note: list truncated to first {cfg.max_repo_files} tracked files.)")
    lines.append("")

    lines.append("## Top-level layout")
    for name, count in top:
        lines.append(f"- `{name}` — {count}")
    lines.append("")

    if key_files:
        lines.append("## Key config/entry files present")
        for rel in key_files:
            lines.append(f"- `{rel}`")
        lines.append("")

    if ext_hist:
        lines.append("## Extension histogram")
        for ext, count in ext_hist.most_common(20):
            lines.append(f"- `{ext}` — {count}")
        lines.append("")

    return "\n".join(lines)
