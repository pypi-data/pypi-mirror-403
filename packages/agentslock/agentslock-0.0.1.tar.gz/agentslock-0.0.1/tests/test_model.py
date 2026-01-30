"""Tests for data models."""

from __future__ import annotations

import pytest

from agentslock.exceptions import ValidationError
from agentslock.model import (
    ClientId,
    Defaults,
    GitSource,
    InlineSource,
    InstructionKind,
    InstructionMode,
    Instructions,
    Lockfile,
    MCPConfig,
    MCPServer,
    PathSource,
    Project,
    Skill,
    Transport,
    validate_flavor,
    validate_git_sha,
    validate_name,
)


class TestValidateName:
    def test_valid_names(self):
        assert validate_name("skill-one") == "skill-one"
        assert validate_name("a") == "a"
        assert validate_name("skill123") == "skill123"
        assert validate_name("my-skill-v2") == "my-skill-v2"

    def test_invalid_names(self):
        with pytest.raises(ValidationError):
            validate_name("Skill-One")  # uppercase
        with pytest.raises(ValidationError):
            validate_name("-skill")  # starts with hyphen
        with pytest.raises(ValidationError):
            validate_name("skill_one")  # underscore
        with pytest.raises(ValidationError):
            validate_name("")  # empty


class TestValidateFlavor:
    def test_valid_flavors(self):
        assert validate_flavor("claude-skill-v1") == "claude-skill-v1"
        assert validate_flavor("mcp-v2") == "mcp-v2"
        assert validate_flavor("agent-v10") == "agent-v10"

    def test_invalid_flavors(self):
        with pytest.raises(ValidationError):
            validate_flavor("skill")  # no version
        with pytest.raises(ValidationError):
            validate_flavor("skill-v")  # incomplete version
        with pytest.raises(ValidationError):
            validate_flavor("Skill-v1")  # uppercase


class TestValidateGitSha:
    def test_valid_shas(self):
        assert validate_git_sha("abc1234") == "abc1234"
        assert validate_git_sha("abc1234567890abcdef1234567890abcdef1234") == "abc1234567890abcdef1234567890abcdef1234"

    def test_invalid_shas(self):
        with pytest.raises(ValidationError):
            validate_git_sha("abc123")  # too short
        with pytest.raises(ValidationError):
            validate_git_sha("xyz1234")  # invalid hex
        with pytest.raises(ValidationError):
            validate_git_sha("")  # empty


class TestClientId:
    def test_from_str(self):
        assert ClientId.from_str("claude") == ClientId.CLAUDE
        assert ClientId.from_str("CLAUDE") == ClientId.CLAUDE
        assert ClientId.from_str("codex") == ClientId.CODEX

    def test_from_str_invalid(self):
        with pytest.raises(ValidationError):
            ClientId.from_str("invalid")


class TestGitSource:
    def test_valid_source(self):
        source = GitSource(repo="https://github.com/test/repo", rev="abc1234")
        assert source.type == "git"
        assert source.repo == "https://github.com/test/repo"

    def test_with_subdir(self):
        source = GitSource(repo="https://github.com/test/repo", rev="abc1234", subdir="skills/foo")
        assert source.subdir == "skills/foo"

    def test_invalid_subdir(self):
        with pytest.raises(ValidationError):
            GitSource(repo="https://github.com/test/repo", rev="abc1234", subdir="../escape")

    def test_invalid_absolute_subdir(self):
        with pytest.raises(ValidationError):
            GitSource(repo="https://github.com/test/repo", rev="abc1234", subdir="/absolute/path")


class TestPathSource:
    def test_valid_source(self):
        source = PathSource(path="./skills/foo")
        assert source.type == "path"
        assert source.path == "./skills/foo"


class TestInlineSource:
    def test_valid_source(self):
        source = InlineSource(content="# Instructions\nBe helpful.")
        assert source.type == "inline"
        assert source.content == "# Instructions\nBe helpful."


class TestMCPConfig:
    def test_stdio_transport(self):
        config = MCPConfig(transport=Transport.STDIO, command="node", args=["server.js"])
        assert config.transport == Transport.STDIO
        assert config.command == "node"

    def test_http_transport(self):
        config = MCPConfig(transport=Transport.HTTP, url="http://localhost:8080")
        assert config.url == "http://localhost:8080"

    def test_stdio_requires_command(self):
        with pytest.raises(ValidationError):
            MCPConfig(transport=Transport.STDIO)

    def test_http_requires_url(self):
        with pytest.raises(ValidationError):
            MCPConfig(transport=Transport.HTTP)


class TestSkill:
    def test_create_skill(self):
        skill = Skill(
            name="my-skill",
            flavor="claude-skill-v1",
            source=PathSource(path="./skills/my-skill"),
        )
        assert skill.name == "my-skill"
        assert skill.enabled is True
        assert skill.groups == ["default"]

    def test_invalid_name(self):
        with pytest.raises(ValidationError):
            Skill(
                name="Invalid_Name",
                flavor="claude-skill-v1",
                source=PathSource(path="./skills/foo"),
            )


class TestLockfile:
    def test_create_lockfile(self):
        lockfile = Lockfile(
            version=1,
            project=Project(name="test"),
            defaults=Defaults(),
            groups={"default": "Default group"},
        )
        assert lockfile.version == 1
        assert lockfile.project.name == "test"

    def test_invalid_version(self):
        with pytest.raises(ValidationError):
            Lockfile(
                version=99,
                project=Project(name="test"),
                defaults=Defaults(),
                groups={"default": "Default group"},
            )

    def test_undefined_group(self):
        with pytest.raises(ValidationError):
            Lockfile(
                version=1,
                project=Project(name="test"),
                defaults=Defaults(),
                groups={"default": "Default"},
                skills=[
                    Skill(
                        name="skill",
                        flavor="claude-skill-v1",
                        source=PathSource(path="./skills/skill"),
                        groups=["undefined-group"],
                    )
                ],
            )

    def test_duplicate_skill_names(self):
        with pytest.raises(ValidationError):
            Lockfile(
                version=1,
                project=Project(name="test"),
                defaults=Defaults(),
                groups={"default": "Default"},
                skills=[
                    Skill(name="dup", flavor="claude-skill-v1", source=PathSource(path="./a")),
                    Skill(name="dup", flavor="claude-skill-v1", source=PathSource(path="./b")),
                ],
            )

    def test_filter_by_groups(self):
        lockfile = Lockfile(
            version=1,
            project=Project(name="test"),
            defaults=Defaults(),
            groups={"default": "Default", "coding": "Coding"},
            skills=[
                Skill(name="skill-a", flavor="claude-skill-v1", source=PathSource(path="./a"), groups=["default"]),
                Skill(name="skill-b", flavor="claude-skill-v1", source=PathSource(path="./b"), groups=["coding"]),
            ],
        )

        filtered = lockfile.filter_by_groups(["coding"])
        assert len(filtered.skills) == 1
        assert filtered.skills[0].name == "skill-b"

    def test_filter_enabled(self):
        lockfile = Lockfile(
            version=1,
            project=Project(name="test"),
            defaults=Defaults(),
            groups={"default": "Default"},
            skills=[
                Skill(name="enabled", flavor="claude-skill-v1", source=PathSource(path="./a"), enabled=True),
                Skill(name="disabled", flavor="claude-skill-v1", source=PathSource(path="./b"), enabled=False),
            ],
        )

        filtered = lockfile.filter_enabled()
        assert len(filtered.skills) == 1
        assert filtered.skills[0].name == "enabled"
