"""Tests for path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentslock.model import ClientId
from agentslock.paths import (
    ClientPaths,
    get_default_instructions_path,
    get_default_lockfile_path,
    get_managed_prefix,
)


class TestGetDefaultLockfilePath:
    def test_default_in_cwd(self, temp_dir: Path, monkeypatch):
        monkeypatch.chdir(temp_dir)
        path = get_default_lockfile_path()
        assert path == temp_dir / "AGENTS.lock"

    def test_with_search_dir(self, temp_dir: Path):
        path = get_default_lockfile_path(temp_dir)
        assert path == temp_dir / "AGENTS.lock"


class TestGetDefaultInstructionsPath:
    def test_instructions_path(self, temp_dir: Path):
        lockfile_path = temp_dir / "AGENTS.lock"
        path = get_default_instructions_path(lockfile_path)
        assert path == temp_dir / "AGENTS.lock.instructions"


class TestClientPaths:
    def test_claude_project_paths(self, temp_dir: Path):
        paths = ClientPaths(ClientId.CLAUDE, temp_dir)

        assert paths.skills_dir("project") == temp_dir / ".claude" / "skills"
        assert paths.agents_dir("project") == temp_dir / ".claude" / "agents"
        assert paths.mcp_config_path("project") == temp_dir / ".mcp.json"
        assert paths.instructions_path("project") == temp_dir / "CLAUDE.md"

    def test_claude_global_paths(self, temp_dir: Path):
        paths = ClientPaths(ClientId.CLAUDE, temp_dir)

        assert paths.skills_dir("global") == Path.home() / ".claude" / "skills"
        assert paths.agents_dir("global") == Path.home() / ".claude" / "agents"
        assert paths.mcp_config_path("global") == Path.home() / ".claude.json"

    def test_codex_project_paths(self, temp_dir: Path):
        paths = ClientPaths(ClientId.CODEX, temp_dir)

        assert paths.skills_dir("project") == temp_dir / ".codex" / "skills"
        assert paths.agents_dir("project") is None  # Codex doesn't support agents
        assert paths.instructions_path("project") == temp_dir / "AGENTS.md"

    def test_copilot_project_paths(self, temp_dir: Path):
        paths = ClientPaths(ClientId.COPILOT, temp_dir)

        assert paths.skills_dir("project") == temp_dir / ".github" / "skills"
        assert paths.agents_dir("project") == temp_dir / ".github" / "agents"
        assert paths.instructions_path("project") == temp_dir / "AGENTS.md"

    def test_gemini_project_paths(self, temp_dir: Path):
        paths = ClientPaths(ClientId.GEMINI, temp_dir)

        assert paths.skills_dir("project") == temp_dir / ".gemini" / "skills"
        assert paths.agents_dir("project") is None  # Gemini doesn't support agents

    def test_skill_path(self, temp_dir: Path):
        paths = ClientPaths(ClientId.CLAUDE, temp_dir)
        path = paths.skill_path("my-skill", "project")
        assert path == temp_dir / ".claude" / "skills" / "my-skill"

    def test_agent_path(self, temp_dir: Path):
        paths = ClientPaths(ClientId.CLAUDE, temp_dir)
        path = paths.agent_path("my-agent", "project")
        assert path == temp_dir / ".claude" / "agents" / "my-agent.md"

    def test_supports_agents(self, temp_dir: Path):
        assert ClientPaths(ClientId.CLAUDE, temp_dir).supports_agents() is True
        assert ClientPaths(ClientId.COPILOT, temp_dir).supports_agents() is True
        assert ClientPaths(ClientId.CODEX, temp_dir).supports_agents() is False
        assert ClientPaths(ClientId.GEMINI, temp_dir).supports_agents() is False

    def test_supports_mcp(self, temp_dir: Path):
        # Project scope
        assert ClientPaths(ClientId.CLAUDE, temp_dir).supports_mcp("project") is True
        assert ClientPaths(ClientId.CODEX, temp_dir).supports_mcp("project") is False

        # Global scope
        assert ClientPaths(ClientId.CLAUDE, temp_dir).supports_mcp("global") is True
        assert ClientPaths(ClientId.CODEX, temp_dir).supports_mcp("global") is True
        assert ClientPaths(ClientId.GEMINI, temp_dir).supports_mcp("global") is True
        assert ClientPaths(ClientId.COPILOT, temp_dir).supports_mcp("global") is True


class TestGetManagedPrefix:
    def test_prefix(self):
        prefix = get_managed_prefix()
        assert prefix == "al__"
