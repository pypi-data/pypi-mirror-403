# takopi-pinnacle

A Takopi **command plugin** that generates *single-file handoff bundles* for your LLM workflow:

- **Plan bundle**: a repo snapshot + repo map + planning system prompt template
- **Review bundle**: repo snapshot + `diff.patch` + review system prompt template + delta stats

It’s designed to make “upload a zip to GPT-5.2 Pro” and “review a PR from a patch” frictionless from a phone.

## Install

> Important: Takopi discovers plugins via Python entrypoints, so the plugin must be installed **into the same environment as takopi**.

If you installed takopi with `uv` (recommended):

```bash
uv tool install -U takopi --with takopi-pinnacle
```

If you installed takopi with `pip`:

```bash
pip install -U takopi-pinnacle
```

## Usage

### Generate a plan bundle

From a Takopi chat (within a project/worktree context):

```
/pinnacle plan
```

### Generate a PR review bundle

```
/pinnacle review
```

Optional base override:

```
/pinnacle review --base origin/main
```

### Download the bundle to your phone

Takopi already supports file transfer. After running a command, the plugin tells you the exact command to fetch the zip:

```
/file get .pinnacle/bundle.zip
```

Upload that zip to GPT-5.2 Pro.

## Configuration

Takopi exposes plugin config under `plugins.<plugin_id>`.

Example (TOML):

```toml
[plugins.pinnacle]
out_dir = ".pinnacle"
max_repo_files = 8000
max_top_level_entries = 80
```

## Philosophy

- Output is **bundle-first**, not chat-first. Telegram message limits are avoided by writing artifacts to disk.
- The bundle is **single zip**, with:
  - `repo/` snapshot (tracked files)
  - `diff.patch` (review bundles only)
  - `context.md` (repo map, git metadata, delta stats)
  - `prompts/` (system prompt templates)

## License

MIT
# takopi-pinnacle
# takopi-flow
