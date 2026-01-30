"""Tests for renderers."""

from __future__ import annotations

from pathlib import Path

from agentslock.model import ClientId, Defaults, Lockfile, MCPConfig, MCPServer, PathSource, Project, Skill, Transport
from agentslock.render.claude import ClaudeRenderer
from agentslock.render.codex import CodexRenderer
from agentslock.resolve import ResolvedSource, SourceResolver


class DummyResolver(SourceResolver):
    def __init__(self, lockfile: Lockfile, resolved: ResolvedSource) -> None:
        super().__init__(lockfile)
        self._resolved = resolved

    def resolve_skill(self, skill: Skill) -> ResolvedSource:
        return self._resolved


def test_claude_renderer_warns_on_missing_skill_path(tmp_path: Path) -> None:
    lockfile = Lockfile(
        version=1,
        project=Project(name="test"),
        defaults=Defaults(clients=[ClientId.CLAUDE]),
        groups={"default": "Default group"},
        skills=[
            Skill(
                name="skill-one",
                flavor="claude-skill-v1",
                source=PathSource(path="./skills/skill-one"),
            )
        ],
        agents=[],
        mcp_servers=[],
        instructions=[],
        path=tmp_path / "AGENTS.lock",
    )
    resolver = DummyResolver(lockfile, ResolvedSource(content="# Skill", is_directory=False))

    renderer = ClaudeRenderer(lockfile, resolver, scope="project", project_root=tmp_path)
    result = renderer.render()

    assert any("Skill source path missing" in warning for warning in result.warnings)
    assert result.files == []
    assert result.directories == []


def test_codex_renderer_includes_tool_filters(tmp_path: Path) -> None:
    lockfile = Lockfile(
        version=1,
        project=Project(name="test"),
        defaults=Defaults(clients=[ClientId.CODEX]),
        groups={"default": "Default group"},
        skills=[],
        agents=[],
        mcp_servers=[
            MCPServer(
                name="example-mcp",
                flavor="mcp-v1",
                config=MCPConfig(
                    transport=Transport.STDIO,
                    command="node",
                    args=["server.js"],
                    tool_filters={"include": ["search"], "exclude": ["dangerous"]},
                ),
            )
        ],
        instructions=[],
        path=tmp_path / "AGENTS.lock",
    )
    resolver = SourceResolver(lockfile)
    renderer = CodexRenderer(lockfile, resolver, scope="global", project_root=tmp_path)
    result = renderer.render()

    assert len(result.config_updates) == 1
    config = result.config_updates[0].value
    assert config is not None
    assert config["tool_filters"] == {"include": ["search"], "exclude": ["dangerous"]}
