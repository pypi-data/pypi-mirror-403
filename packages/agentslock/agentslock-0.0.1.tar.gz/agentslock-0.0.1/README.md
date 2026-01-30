<p align="center">
<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://gist.githubusercontent.com/OKUA1/a9434342b05cd23a1e263fa2d0730854/raw/cfb905cffdbcf4df7192a4eea7cfdadd74f19ce4/al-black-cropped.svg" >
  <source media="(prefers-color-scheme: dark)" srcset="https://gist.githubusercontent.com/OKUA1/a9434342b05cd23a1e263fa2d0730854/raw/cfb905cffdbcf4df7192a4eea7cfdadd74f19ce4/al-white-cropped.svg">
  <img alt="Hashnode logo" src="https://gist.githubusercontent.com/OKUA1/a9434342b05cd23a1e263fa2d0730854/raw/cfb905cffdbcf4df7192a4eea7cfdadd74f19ce4/al-black-cropped.svg" height = "250">
</picture>
</p>



AGENTS.lock is a package manager for AI agent configurations. It keeps skills, agents, MCP servers,
and instructions kept in sync across Claude, Codex, Gemini, and Copilot CLI tools. The lockfile is the
single source of truth for both project and global scopes.

Install AGENTS.lock: 
```bash
pip install agentslock
```

> **⚠️ Warning:** This is an early release. Breaking changes may occur in future versions.

Usage:
```bash
al init          # Initialize a new AGENTS.lock file
al set clients claude,codex # Set CLI clients for the project
al add skill https://github.com/anthropics/skills/tree/main/skills/frontend-design # Add a skill
al sync          # Sync skills and agents as per the lockfile
```

This will make an entry in `AGENTS.lock` and sync the skill to the appropriate locations for the specified clients. From that point, it is not necessary to manually manage the skills across different clients, but simply maintain a single `AGENTS.lock` file and run `al sync` to keep everything up to date.

Currently supported clients and features:

| Client  | AGENTS.md | Skills | MCP |
|---------|-----------|--------|-----|
| Claude  | ✓         | ✓      | ✓   |
| Codex   | ✓         | ✓      | ✗   |
| Copilot | ✓         | ✓      | ✗   |
| Gemini  | ✓         | ✓      | ✗   |


## Lockfile basics

`AGENTS.lock` is a TOML file that records project metadata, default clients, and the full set of
configured resources. Each entry carries a source, which can be a pinned git revision, a path
relative to the lockfile, or inline content for instructions. Groups provide a way to filter
subsets of resources during sync so teams can target specific workflows.

## Install to project or global scope

Project scope writes within the repository. Global scope writes to user-level configuration paths.

```bash
al sync
al --global sync
```

## Use lockfile aliases (alias file workflows)

If you manage multiple lockfiles, create an alias and target it via `--lockfile`.

```bash
al alias add work /path/to/AGENTS.lock
al --lockfile work sync
```