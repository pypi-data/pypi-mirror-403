from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .gitutils import (
    GitError,
    GitInfo,
    best_effort_base_ref,
    diff_patch,
    diff_stat,
    dirty_cached_patch,
    dirty_patch,
    ensure_local_ignore_dir,
    get_git_info,
    git_archive_zip,
    list_untracked_files,
    merge_base,
)
from .repomap import RepoMapConfig, render_repo_map
from .ship import (
    ShipConfig,
    ShipResult,
    format_pr_create_command,
    pr_base_branch,
    ship_repo,
)


class BundleError(RuntimeError):
    pass


@dataclass(frozen=True)
class PinnacleConfig:
    out_dir: str = ".pinnacle"
    max_repo_files: int = 8000
    max_top_level_entries: int = 80


@dataclass(frozen=True)
class BundleResult:
    mode: str  # "plan" | "review"
    out_dir: Path
    bundle_zip: Path
    base_ref: str | None
    merge_base: str | None
    head_sha: str
    ship: ShipResult | None = None


def _ensure_relative_dir(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        raise BundleError(
            f"out_dir must be a relative path (got absolute: {path_str})."
        )
    if str(p) in {".", ""}:
        raise BundleError("out_dir must not be repo root.")
    return p


def _safe_clean_dir(repo_root: Path, rel_out_dir: Path) -> Path:
    out_dir = (repo_root / rel_out_dir).resolve()
    repo_root = repo_root.resolve()
    if repo_root not in out_dir.parents:
        raise BundleError("Refusing to delete outside repo root.")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ensure_local_ignore_dir(repo_root, rel_out_dir)
    return out_dir


def _pinnacle_prefix() -> str:
    return "__pinnacle__"


def _write_zip_text(zf: zipfile.ZipFile, arcname: str, text: str) -> None:
    # Ensure POSIX paths inside the zip.
    arcname = arcname.replace("\\", "/")
    zf.writestr(arcname, text)


def _git_meta(git: GitInfo) -> dict[str, Any]:
    data = asdict(git)
    data["repo_root"] = str(data["repo_root"])
    return data


def _render_context_md(
    *,
    mode: str,
    git: GitInfo,
    repo_map_md: str,
    base_ref: str | None,
    merge_base_sha: str | None,
    diffstat: str | None,
    dirty: dict[str, bool],
    untracked_files: list[str],
    ship: ShipResult | None = None,
    ship_note_lines: list[str] | None = None,
) -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines: list[str] = []
    lines.append(f"# Pinnacle bundle context ({mode})")
    lines.append("")
    lines.append(f"Generated: `{now}`")
    lines.append(f"Pinnacle version: `{__version__}`")
    lines.append("")

    lines.append("## Git")
    lines.append(f"- Repo root: `{git.repo_root}`")
    lines.append(f"- Branch: `{git.branch}`")
    lines.append(f"- HEAD: `{git.head_sha}`")
    lines.append(f"- HEAD summary: {git.head_summary}")
    lines.append(f"- Working tree dirty: `{git.is_dirty}`")
    if dirty.get("staged"):
        lines.append("- Dirty staged changes: `true`")
    if dirty.get("unstaged"):
        lines.append("- Dirty unstaged changes: `true`")
    lines.append("")

    if ship is not None:
        lines.append("## Shipping")
        lines.append(f"- Remote: `{ship.remote}`")
        lines.append(f"- Branch: `{ship.branch}`")
        if ship.commit_sha:
            lines.append(f"- Commit: `{ship.commit_sha}`")
        lines.append(f"- Pushed: `{ship.pushed}`")
        if ship.pr_url:
            lines.append(f"- PR: {ship.pr_url}")
        if ship.dry_run:
            lines.append("- Dry run: `true`")
        lines.append("")

    if ship_note_lines:
        lines.append("## Shipping notes")
        lines.extend(ship_note_lines)
        lines.append("")

    if untracked_files:
        lines.append("## Untracked files")
        lines.append("These are not included in the bundle snapshot or patches.")
        for rel in untracked_files:
            lines.append(f"- `{rel}`")
        lines.append("")

    if mode == "review":
        lines.append("## Diff base")
        lines.append(f"- Base ref: `{base_ref}`")
        lines.append(f"- Merge-base: `{merge_base_sha}`")
        lines.append("")

    if diffstat:
        lines.append("## Diffstat")
        lines.append("```")
        lines.append(diffstat.rstrip())
        lines.append("```")
        lines.append("")

    lines.append(repo_map_md.strip())
    lines.append("")

    lines.append("## Bundle contents")
    lines.append(f"- `__pinnacle__/context.md`")
    if mode == "plan":
        lines.append("- `__pinnacle__/prompts/plan_system.md`")
    if mode == "review":
        lines.append("- `__pinnacle__/diff.patch`")
        lines.append("- `__pinnacle__/prompts/review_system.md`")
    if dirty.get("staged"):
        lines.append("- `__pinnacle__/dirty_cached.patch`")
    if dirty.get("unstaged"):
        lines.append("- `__pinnacle__/dirty.patch`")
    lines.append("")

    lines.append(
        "## How to use with GPT\n"
        "Upload this zip to your GPT session.\n"
        "Then apply the included system prompt (in `__pinnacle__/prompts/`).\n"
        "Use `__pinnacle__/context.md` as the repo orientation + metadata.\n"
    )

    return "\n".join(lines)


def _load_package_prompt(name: str) -> str:
    # importlib.resources is stdlib. Keep local import for speed and compatibility.
    from importlib.resources import files

    path = files("takopi_pinnacle").joinpath("prompts").joinpath(name)
    return path.read_text(encoding="utf-8")


def build_plan_bundle(repo_root: Path, cfg: PinnacleConfig) -> BundleResult:
    rel_out = _ensure_relative_dir(cfg.out_dir)
    out_dir = _safe_clean_dir(repo_root, rel_out)
    bundle_zip = out_dir / "bundle.zip"

    git = get_git_info(repo_root)
    untracked = list_untracked_files(repo_root)
    repo_map_md = render_repo_map(
        repo_root,
        RepoMapConfig(
            max_repo_files=cfg.max_repo_files,
            max_top_level_entries=cfg.max_top_level_entries,
        ),
    )

    # Start with a faithful repo snapshot.
    git_archive_zip(repo_root, out_path=bundle_zip)

    dirty = {
        "staged": bool(dirty_cached_patch(repo_root).strip()),
        "unstaged": bool(dirty_patch(repo_root).strip()),
    }

    context_md = _render_context_md(
        mode="plan",
        git=git,
        repo_map_md=repo_map_md,
        base_ref=None,
        merge_base_sha=None,
        diffstat=None,
        dirty=dirty,
        untracked_files=untracked,
    )

    plan_prompt = _load_package_prompt("plan_system.md")

    meta = {
        "mode": "plan",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pinnacle_version": __version__,
        "git": _git_meta(git),
        "config": asdict(cfg),
        "untracked_files": untracked,
    }

    with zipfile.ZipFile(bundle_zip, mode="a", compression=zipfile.ZIP_DEFLATED) as zf:
        _write_zip_text(zf, f"{_pinnacle_prefix()}/context.md", context_md)
        _write_zip_text(zf, f"{_pinnacle_prefix()}/prompts/plan_system.md", plan_prompt)
        _write_zip_text(zf, f"{_pinnacle_prefix()}/bundle_meta.json", json.dumps(meta, indent=2))
        if dirty["staged"]:
            _write_zip_text(
                zf,
                f"{_pinnacle_prefix()}/dirty_cached.patch",
                dirty_cached_patch(repo_root),
            )
        if dirty["unstaged"]:
            _write_zip_text(
                zf,
                f"{_pinnacle_prefix()}/dirty.patch",
                dirty_patch(repo_root),
            )

    # Also write context.md next to the zip for quick inspection.
    (out_dir / "context.md").write_text(context_md, encoding="utf-8")
    (out_dir / "plan_system.md").write_text(plan_prompt, encoding="utf-8")

    return BundleResult(
        mode="plan",
        out_dir=out_dir,
        bundle_zip=bundle_zip,
        base_ref=None,
        merge_base=None,
        head_sha=git.head_sha,
    )


def build_review_bundle(
    repo_root: Path,
    cfg: PinnacleConfig,
    *,
    base_ref: str | None = None,
    ship: ShipConfig | None = None,
) -> BundleResult:
    rel_out = _ensure_relative_dir(cfg.out_dir)
    out_dir = _safe_clean_dir(repo_root, rel_out)
    bundle_zip = out_dir / "bundle.zip"

    chosen_base = base_ref or best_effort_base_ref(repo_root)
    ship_result: ShipResult | None = None
    ship_note_lines: list[str] | None = None
    if ship is not None and ship.enabled:
        ship_result = ship_repo(repo_root, ship, base_ref=chosen_base, out_dir=rel_out)
        if ship.open_pr and ship_result.pr_url is None:
            base_branch = pr_base_branch(repo_root, chosen_base)
            pr_cmd = format_pr_create_command(ship, base=base_branch, head=ship_result.branch)
            reason = "dry run" if ship_result.dry_run else "gh missing or unauthenticated"
            ship_note_lines = [
                f"PR not created ({reason}).",
                "Run this manually:",
                "```",
                pr_cmd,
                "```",
            ]

    git = get_git_info(repo_root)
    untracked = list_untracked_files(repo_root)
    repo_map_md = render_repo_map(
        repo_root,
        RepoMapConfig(
            max_repo_files=cfg.max_repo_files,
            max_top_level_entries=cfg.max_top_level_entries,
        ),
    )

    mb = merge_base(repo_root, chosen_base)
    patch = diff_patch(repo_root, from_commit=mb)
    stat = diff_stat(repo_root, from_commit=mb)

    git_archive_zip(repo_root, out_path=bundle_zip)

    dirty = {
        "staged": bool(dirty_cached_patch(repo_root).strip()),
        "unstaged": bool(dirty_patch(repo_root).strip()),
    }

    context_md = _render_context_md(
        mode="review",
        git=git,
        repo_map_md=repo_map_md,
        base_ref=chosen_base,
        merge_base_sha=mb,
        diffstat=stat,
        dirty=dirty,
        untracked_files=untracked,
        ship=ship_result,
        ship_note_lines=ship_note_lines,
    )

    review_prompt = _load_package_prompt("review_system.md")

    meta = {
        "mode": "review",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pinnacle_version": __version__,
        "git": _git_meta(git),
        "config": asdict(cfg),
        "base_ref": chosen_base,
        "merge_base": mb,
        "untracked_files": untracked,
        "ship": asdict(ship_result) if ship_result else None,
    }

    with zipfile.ZipFile(bundle_zip, mode="a", compression=zipfile.ZIP_DEFLATED) as zf:
        _write_zip_text(zf, f"{_pinnacle_prefix()}/context.md", context_md)
        _write_zip_text(zf, f"{_pinnacle_prefix()}/diff.patch", patch)
        _write_zip_text(zf, f"{_pinnacle_prefix()}/prompts/review_system.md", review_prompt)
        _write_zip_text(zf, f"{_pinnacle_prefix()}/bundle_meta.json", json.dumps(meta, indent=2))
        if dirty["staged"]:
            _write_zip_text(
                zf,
                f"{_pinnacle_prefix()}/dirty_cached.patch",
                dirty_cached_patch(repo_root),
            )
        if dirty["unstaged"]:
            _write_zip_text(
                zf,
                f"{_pinnacle_prefix()}/dirty.patch",
                dirty_patch(repo_root),
            )

    (out_dir / "context.md").write_text(context_md, encoding="utf-8")
    (out_dir / "review_system.md").write_text(review_prompt, encoding="utf-8")
    (out_dir / "diff.patch").write_text(patch, encoding="utf-8")

    return BundleResult(
        mode="review",
        out_dir=out_dir,
        bundle_zip=bundle_zip,
        base_ref=chosen_base,
        merge_base=mb,
        head_sha=git.head_sha,
        ship=ship_result,
    )


def load_config(plugin_config: dict[str, Any] | None) -> PinnacleConfig:
    if not plugin_config:
        return PinnacleConfig()

    def _get_int(key: str, default: int) -> int:
        v = plugin_config.get(key, default)
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    out_dir = str(plugin_config.get("out_dir", PinnacleConfig.out_dir))

    return PinnacleConfig(
        out_dir=out_dir,
        max_repo_files=_get_int("max_repo_files", PinnacleConfig.max_repo_files),
        max_top_level_entries=_get_int(
            "max_top_level_entries", PinnacleConfig.max_top_level_entries
        ),
    )
