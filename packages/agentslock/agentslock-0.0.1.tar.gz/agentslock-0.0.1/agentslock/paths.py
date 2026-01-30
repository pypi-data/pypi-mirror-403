"""Path resolution for OS and client-specific locations."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from agentslock.model import ClientId

Scope = Literal["project", "global"]


def get_xdg_config_home() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".config"


def get_xdg_cache_home() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg)
    return Path.home() / ".cache"


def get_global_config_dir() -> Path:
    config_home = get_xdg_config_home()
    # Prefer ~/.agents.lock for simplicity, fall back to XDG
    legacy = Path.home() / ".agents.lock"
    if legacy.exists():
        return legacy
    return config_home / "agents.lock"


def get_global_config_path() -> Path:
    return get_global_config_dir() / "config.toml"


def get_cache_dir() -> Path:
    cache_home = get_xdg_cache_home()
    # Prefer ~/.agents.lock/cache, fall back to XDG
    legacy = Path.home() / ".agents.lock" / "cache"
    if legacy.exists():
        return legacy
    return cache_home / "agents.lock"


def get_default_lockfile_path(search_dir: Path | None = None) -> Path:
    if search_dir is None:
        search_dir = Path.cwd()
    return search_dir / "AGENTS.lock"


def get_default_instructions_path(lockfile_path: Path) -> Path:
    return lockfile_path.parent / "AGENTS.lock.instructions"


@dataclass(frozen=True)
class ClientPathSpec:
    project_skills: Path
    global_skills: Path
    project_agents: Path | None
    global_agents: Path | None
    project_mcp: Path | None
    global_mcp: Path | None
    project_instructions: Path | None
    global_instructions: Path | None
    extra_instructions: dict[str, Path] = field(default_factory=dict)


def _build_client_spec(client: ClientId, project_root: Path) -> ClientPathSpec:
    if client == ClientId.CLAUDE:
        return ClientPathSpec(
            project_skills=project_root / ".claude" / "skills",
            global_skills=Path.home() / ".claude" / "skills",
            project_agents=project_root / ".claude" / "agents",
            global_agents=Path.home() / ".claude" / "agents",
            project_mcp=project_root / ".mcp.json",
            global_mcp=Path.home() / ".claude.json",
            project_instructions=project_root / "CLAUDE.md",
            global_instructions=Path.home() / "CLAUDE.md",
        )
    if client == ClientId.CODEX:
        return ClientPathSpec(
            project_skills=project_root / ".codex" / "skills",
            global_skills=Path.home() / ".codex" / "skills",
            project_agents=None,
            global_agents=None,
            project_mcp=None,
            global_mcp=Path.home() / ".codex" / "config.toml",
            project_instructions=project_root / "AGENTS.md",
            global_instructions=Path.home() / ".codex" / "AGENTS.md",
        )
    if client == ClientId.GEMINI:
        return ClientPathSpec(
            project_skills=project_root / ".gemini" / "skills",
            global_skills=Path.home() / ".gemini" / "skills",
            project_agents=None,
            global_agents=None,
            project_mcp=None,
            global_mcp=Path.home() / ".gemini" / "settings.json",
            project_instructions=project_root / "AGENTS.md",
            global_instructions=Path.home() / ".gemini" / "AGENTS.md",
        )
    if client == ClientId.COPILOT:
        return ClientPathSpec(
            project_skills=project_root / ".github" / "skills",
            global_skills=Path.home() / ".copilot" / "skills",
            project_agents=project_root / ".github" / "agents",
            global_agents=Path.home() / ".copilot" / "agents",
            project_mcp=None,
            global_mcp=Path.home() / ".copilot" / "mcp-config.json",
            project_instructions=project_root / "AGENTS.md",
            global_instructions=Path.home() / ".copilot" / "AGENTS.md",
            extra_instructions={
                "copilot-instructions-md": project_root / ".github" / "copilot-instructions.md"
            },
        )
    raise ValueError(f"Unknown client: {client}")


class ClientPaths:
    """Path resolution for a specific client."""

    def __init__(self, client: ClientId, project_root: Path | None = None):
        self.client = client
        self.project_root = project_root or Path.cwd()
        self._spec = _build_client_spec(self.client, self.project_root)

    # Public interface

    def skills_dir(self, scope: Scope) -> Path:
        if scope == "global":
            return self._spec.global_skills
        return self._spec.project_skills

    def skill_path(self, skill_name: str, scope: Scope) -> Path:
        return self.skills_dir(scope) / skill_name

    def agents_dir(self, scope: Scope) -> Path | None:
        if scope == "global":
            return self._spec.global_agents
        return self._spec.project_agents

    def agent_path(self, agent_name: str, scope: Scope) -> Path | None:
        agents_dir = self.agents_dir(scope)
        if agents_dir is None:
            return None
        return agents_dir / f"{agent_name}.md"

    def mcp_config_path(self, scope: Scope) -> Path | None:
        if scope == "global":
            return self._spec.global_mcp
        return self._spec.project_mcp

    def instructions_path(self, scope: Scope, kind: str | None = None) -> Path | None:
        if scope == "global":
            return self._spec.global_instructions

        if kind and kind in self._spec.extra_instructions:
            return self._spec.extra_instructions[kind]

        return self._spec.project_instructions

    def supports_agents(self) -> bool:
        return self.client in (ClientId.CLAUDE, ClientId.COPILOT)

    def supports_mcp(self, scope: Scope) -> bool:
        if scope == "project":
            return self.client == ClientId.CLAUDE
        return self.client in (ClientId.CLAUDE, ClientId.CODEX, ClientId.GEMINI, ClientId.COPILOT)


def get_state_dir(scope: Scope, project_root: Path | None = None) -> Path:
    if scope == "global":
        return get_global_config_dir()
    if project_root is None:
        project_root = Path.cwd()
    return project_root / ".agents.lock"


def get_state_path(scope: Scope, project_root: Path | None = None) -> Path:
    return get_state_dir(scope, project_root) / "state.json"


def get_managed_prefix() -> str:
    return "al__"
