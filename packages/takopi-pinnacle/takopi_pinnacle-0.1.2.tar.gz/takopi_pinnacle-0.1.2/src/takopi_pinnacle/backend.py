from __future__ import annotations

import shlex
from pathlib import Path

from takopi.api import CommandContext, CommandResult

from .bundle import BundleError, build_plan_bundle, build_review_bundle, load_config
from .gitutils import GitError, discover_repo_root
from .ship import ShipConfig


def _normalize_tokens(ctx: CommandContext) -> list[str]:
    args = getattr(ctx, "args", "")
    if isinstance(args, str):
        return shlex.split(args)
    if isinstance(args, (list, tuple)):
        return [str(x) for x in args]
    return []


def _best_effort_start_dir(ctx: CommandContext) -> Path:
    """Try to locate the repo/worktree directory from ctx.

    Takopi may evolve its context object; this keeps the plugin resilient.
    """

    for attr in ("repo_root", "workdir", "cwd", "path"):
        v = getattr(ctx, attr, None)
        if v:
            return Path(v)

    session = getattr(ctx, "session", None)
    if session is not None:
        for attr in ("workdir", "cwd", "repo_root", "path"):
            v = getattr(session, attr, None)
            if v:
                return Path(v)

    return Path.cwd()


HELP = """
/pinnacle plan
  - Create a plan handoff bundle.zip in the repo.

/pinnacle review [--base <ref>] [--ship]
                 [--remote <name>] [--branch <name>]
                 [--commit-msg "<msg>"]
                 [--open-pr] [--draft|--ready]
                 [--pr-title "<title>"]
                 [--dry-run]
  - Create a PR review handoff bundle.zip (includes __pinnacle__/diff.patch).

Artifacts are written to: <repo>/.pinnacle/
Download via Takopi:
  /file get .pinnacle/bundle.zip
""".strip()


class PinnacleCommandBackend:
    id = "pinnacle"
    description = "Generate single-file planning and PR-review bundles for GPT-based workflows."

    async def handle(self, ctx: CommandContext) -> CommandResult:
        tokens = _normalize_tokens(ctx)
        if not tokens or tokens[0] in {"help", "-h", "--help"}:
            return CommandResult(text=HELP)

        subcmd = tokens[0]
        plugin_cfg = getattr(ctx, "plugin_config", None)
        cfg = load_config(plugin_cfg)

        try:
            repo_root = discover_repo_root(_best_effort_start_dir(ctx))
        except GitError as e:
            return CommandResult(text=f"pinnacle error: {e}\n\n{HELP}")

        if subcmd == "plan":
            try:
                result = build_plan_bundle(repo_root, cfg)
            except (BundleError, GitError) as e:
                return CommandResult(text=f"pinnacle plan failed: {e}")

            return CommandResult(
                text=(
                    "✅ Pinnacle plan bundle created\n"
                    f"- Repo: {repo_root}\n"
                    f"- Output dir: {result.out_dir}\n"
                    f"- Bundle: {result.bundle_zip}\n\n"
                    "Download:\n"
                    f"/file get {cfg.out_dir}/bundle.zip"
                )
            )

        if subcmd == "review":
            base_ref = None
            ship = ShipConfig(enabled=False)
            ship_flags_seen = False
            # Very small flag parser to avoid argparse noise in Telegram.
            # Accept: --base <ref> and ship flags.
            i = 1
            while i < len(tokens):
                t = tokens[i]
                if t == "--base" and i + 1 < len(tokens):
                    base_ref = tokens[i + 1]
                    i += 2
                    continue
                if t == "--ship":
                    ship = ship.with_enabled(True)
                    i += 1
                    continue
                if t == "--remote" and i + 1 < len(tokens):
                    ship = ship.with_remote(tokens[i + 1])
                    ship_flags_seen = True
                    i += 2
                    continue
                if t == "--branch" and i + 1 < len(tokens):
                    ship = ship.with_branch(tokens[i + 1])
                    ship_flags_seen = True
                    i += 2
                    continue
                if t == "--commit-msg" and i + 1 < len(tokens):
                    ship = ship.with_commit_msg(tokens[i + 1])
                    ship_flags_seen = True
                    i += 2
                    continue
                if t == "--open-pr":
                    ship = ship.with_open_pr(True)
                    ship_flags_seen = True
                    i += 1
                    continue
                if t == "--draft":
                    ship = ship.with_pr_draft(True)
                    ship_flags_seen = True
                    i += 1
                    continue
                if t == "--ready":
                    ship = ship.with_pr_draft(False)
                    ship_flags_seen = True
                    i += 1
                    continue
                if t == "--pr-title" and i + 1 < len(tokens):
                    ship = ship.with_pr_title(tokens[i + 1])
                    ship_flags_seen = True
                    i += 2
                    continue
                if t == "--dry-run":
                    ship = ship.with_dry_run(True)
                    ship_flags_seen = True
                    i += 1
                    continue
                return CommandResult(text=f"Unknown argument: {t}\n\n{HELP}")

            if ship_flags_seen and not ship.enabled:
                return CommandResult(
                    text=f"Shipping flags require --ship.\n\n{HELP}"
                )

            try:
                result = build_review_bundle(repo_root, cfg, base_ref=base_ref, ship=ship)
            except (BundleError, GitError) as e:
                return CommandResult(text=f"pinnacle review failed: {e}")

            ship_lines = ""
            if result.ship is not None:
                ship_lines = (
                    f"- Branch: {result.ship.branch}\n"
                    f"- Commit: {result.ship.commit_sha or '(none)'}\n"
                    f"- Pushed: {result.ship.pushed}\n"
                )
                if result.ship.pr_url:
                    ship_lines += f"- PR: {result.ship.pr_url}\n"

            base_line = (
                f"- Base: {result.base_ref} (merge-base {result.merge_base})\n"
                if result.base_ref
                else ""
            )
            return CommandResult(
                text=(
                    "✅ Pinnacle review bundle created\n"
                    f"- Repo: {repo_root}\n"
                    f"- HEAD: {result.head_sha}\n"
                    + base_line
                    + ship_lines
                    + f"- Output dir: {result.out_dir}\n"
                    + f"- Bundle: {result.bundle_zip}\n\n"
                    "Download:\n"
                    f"/file get {cfg.out_dir}/bundle.zip"
                )
            )

        return CommandResult(text=f"Unknown subcommand: {subcmd}\n\n{HELP}")


BACKEND = PinnacleCommandBackend()
