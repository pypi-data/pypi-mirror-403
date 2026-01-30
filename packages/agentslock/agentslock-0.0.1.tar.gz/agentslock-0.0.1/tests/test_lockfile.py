"""Tests for lockfile parsing and serialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentslock.exceptions import LockfileError, ValidationError
from agentslock.lockfile import (
    create_default_lockfile,
    parse_lockfile,
    parse_lockfile_str,
    serialize_lockfile,
)
from agentslock.model import ClientId, InstructionKind


class TestParseLockfile:
    def test_parse_valid_lockfile(self, sample_lockfile: Path):
        lockfile = parse_lockfile(sample_lockfile)

        assert lockfile.version == 1
        assert lockfile.project.name == "test-project"
        assert len(lockfile.skills) == 2
        assert len(lockfile.mcp_servers) == 1
        assert len(lockfile.instructions) == 1

    def test_parse_skills(self, sample_lockfile: Path):
        lockfile = parse_lockfile(sample_lockfile)

        skill_one = lockfile.get_skill("skill-one")
        assert skill_one is not None
        assert skill_one.flavor == "claude-skill-v1"
        assert skill_one.source.type == "path"

        skill_two = lockfile.get_skill("skill-two")
        assert skill_two is not None
        assert skill_two.source.type == "path"
        assert "coding" in skill_two.groups

    def test_parse_mcp_servers(self, sample_lockfile: Path):
        lockfile = parse_lockfile(sample_lockfile)

        mcp = lockfile.get_mcp_server("test-server")
        assert mcp is not None
        assert mcp.config.command == "node"
        assert mcp.config.args == ["server.js"]
        assert mcp.config.tool_filters == {"include": ["search"], "exclude": ["dangerous"]}

    def test_parse_nonexistent_file(self, temp_dir: Path):
        with pytest.raises(LockfileError, match="not found"):
            parse_lockfile(temp_dir / "nonexistent.lock")

    def test_parse_invalid_toml(self, temp_dir: Path):
        path = temp_dir / "AGENTS.lock"
        path.write_text("invalid [ toml content")
        with pytest.raises(LockfileError, match="Invalid TOML"):
            parse_lockfile(path)


class TestParseLockfileStr:
    def test_parse_minimal(self):
        content = '''
version = 1

[project]
name = "minimal"

[groups]
default = "Default"
'''
        lockfile = parse_lockfile_str(content)
        assert lockfile.version == 1
        assert lockfile.project.name == "minimal"

    def test_missing_version(self):
        content = '''
[project]
name = "test"
'''
        with pytest.raises(ValidationError, match="Missing required field 'version'"):
            parse_lockfile_str(content)

    def test_missing_skill_name(self):
        content = '''
version = 1

[project]
name = "test"

[groups]
default = "Default"

[[skills]]
flavor = "claude-skill-v1"

  [skills.source]
  type = "path"
  path = "./skill"
'''
        with pytest.raises(ValidationError, match="missing required field 'name'"):
            parse_lockfile_str(content)

    def test_invalid_client(self):
        content = '''
version = 1

[project]
name = "test"

[defaults]
clients = ["invalid-client"]

[groups]
default = "Default"
'''
        with pytest.raises(ValidationError, match="Invalid client"):
            parse_lockfile_str(content)

    def test_claude_md_alias(self):
        content = '''
version = 1

[project]
name = "test"

[[instructions]]
name = "main"
kind = "claude-md"
'''
        lockfile = parse_lockfile_str(content)
        assert lockfile.instructions[0].kind == InstructionKind.AGENTS_MD


class TestSerializeLockfile:
    def test_serialize_roundtrip(self, sample_lockfile: Path):
        original = parse_lockfile(sample_lockfile)
        serialized = serialize_lockfile(original)
        reparsed = parse_lockfile_str(serialized)

        assert reparsed.version == original.version
        assert reparsed.project.name == original.project.name
        assert len(reparsed.skills) == len(original.skills)
        assert len(reparsed.mcp_servers) == len(original.mcp_servers)

    def test_serialize_minimal(self):
        lockfile = create_default_lockfile("test")
        serialized = serialize_lockfile(lockfile)

        assert "version = 1" in serialized
        assert 'name = "test"' in serialized


class TestCreateDefaultLockfile:
    def test_create_default(self):
        lockfile = create_default_lockfile("my-project")

        assert lockfile.version == 1
        assert lockfile.project.name == "my-project"
        assert ClientId.CLAUDE in lockfile.defaults.clients
        assert "default" in lockfile.groups
        assert len(lockfile.skills) == 0
        assert len(lockfile.agents) == 0
        assert len(lockfile.mcp_servers) == 0
        assert len(lockfile.instructions) == 0
