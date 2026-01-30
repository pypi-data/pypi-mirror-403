"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from agentslock.cli import cli
from agentslock.lockfile import parse_lockfile


@pytest.fixture
def runner():
    return CliRunner()


class TestInit:
    def test_init_creates_lockfile(self, runner: CliRunner, temp_dir: Path):
        with runner.isolated_filesystem(temp_dir=temp_dir):
            result = runner.invoke(cli, ["--yes", "init"])

            assert result.exit_code == 0
            assert "Created" in result.output
            assert (Path.cwd() / "AGENTS.lock").exists()

    def test_init_creates_instructions(self, runner: CliRunner, temp_dir: Path):
        with runner.isolated_filesystem(temp_dir=temp_dir):
            result = runner.invoke(cli, ["--yes", "init"])

            assert result.exit_code == 0
            assert (Path.cwd() / "AGENTS.lock.instructions").exists()
            lockfile = parse_lockfile(Path.cwd() / "AGENTS.lock")
            assert len(lockfile.instructions) == 1
            assert lockfile.instructions[0].name == "project-instructions"

    def test_init_no_instructions(self, runner: CliRunner, temp_dir: Path):
        with runner.isolated_filesystem(temp_dir=temp_dir):
            result = runner.invoke(cli, ["--yes", "init", "--no-instructions"])

            assert result.exit_code == 0
            assert not (Path.cwd() / "AGENTS.lock.instructions").exists()
            lockfile = parse_lockfile(Path.cwd() / "AGENTS.lock")
            assert lockfile.instructions == []

    def test_init_existing_fails_without_force(self, runner: CliRunner, temp_dir: Path):
        with runner.isolated_filesystem(temp_dir=temp_dir):
            (Path.cwd() / "AGENTS.lock").write_text("version = 1")

            result = runner.invoke(cli, ["--yes", "init"])

            assert result.exit_code == 1
            assert "already exists" in result.output


class TestValidate:
    def test_validate_valid_lockfile(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "validate"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_invalid_lockfile(self, runner: CliRunner, temp_dir: Path):
        lockfile = temp_dir / "AGENTS.lock"
        lockfile.write_text("invalid content")

        result = runner.invoke(cli, ["--lockfile", str(lockfile), "validate"])

        assert result.exit_code == 1


class TestList:
    def test_list_all(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "list"])

        assert result.exit_code == 0
        assert "test-project" in result.output

    def test_list_skills(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "list", "--skills"])

        assert result.exit_code == 0
        assert "skill-one" in result.output
        assert "skill-two" in result.output

    def test_list_mcp(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "list", "--mcp"])

        assert result.exit_code == 0
        assert "test-server" in result.output

    def test_list_json(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "--json", "list", "--skills"])

        assert result.exit_code == 0
        assert '"skills"' in result.output


class TestSetClients:
    def test_set_clients(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "set", "clients", "claude,gemini"])

        assert result.exit_code == 0
        assert "claude" in result.output.lower()
        assert "gemini" in result.output.lower()

    def test_set_invalid_client(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(cli, ["--lockfile", str(sample_lockfile), "set", "clients", "invalid"])

        assert result.exit_code == 1
        assert "Unknown client" in result.output


class TestAddSkill:
    def test_add_skill_from_path(self, runner: CliRunner, sample_lockfile: Path):
        skill_dir = sample_lockfile.parent / "new-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# New Skill")

        result = runner.invoke(
            cli,
            [
                "--lockfile", str(sample_lockfile),
                "--yes",
                "add", "skill", str(skill_dir),
                "--name", "new-skill",
            ],
        )

        assert result.exit_code == 0
        assert "Added skill" in result.output


class TestAddMcp:
    def test_add_mcp_with_flags(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(
            cli,
            [
                "--lockfile", str(sample_lockfile),
                "--yes",
                "add", "mcp",
                "--name", "new-mcp",
                "--transport", "stdio",
                "--command", "node",
                "--arg", "server.js",
                "--env", "KEY=VALUE",
                "--tool-include", "search",
                "--tool-exclude", "dangerous",
            ],
        )

        assert result.exit_code == 0
        lockfile = parse_lockfile(sample_lockfile)
        mcp = lockfile.get_mcp_server("new-mcp")
        assert mcp is not None
        assert mcp.config.env == {"KEY": "VALUE"}
        assert mcp.config.tool_filters == {"include": ["search"], "exclude": ["dangerous"]}


class TestRemove:
    def test_remove_skill(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(
            cli,
            ["--lockfile", str(sample_lockfile), "--yes", "remove", "skill", "skill-one"],
        )

        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_remove_nonexistent(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(
            cli,
            ["--lockfile", str(sample_lockfile), "--yes", "remove", "skill", "nonexistent"],
        )

        assert result.exit_code == 1
        assert "not found" in result.output


class TestSync:
    def test_sync_dry_run(self, runner: CliRunner, sample_lockfile: Path):
        result = runner.invoke(
            cli,
            ["--lockfile", str(sample_lockfile), "--dry-run", "sync"],
        )

        # Should succeed even if nothing to sync
        assert result.exit_code == 0


class TestDoctor:
    def test_doctor(self, runner: CliRunner):
        result = runner.invoke(cli, ["doctor"])

        # Should succeed and show client info
        assert result.exit_code == 0
        assert "claude" in result.output.lower()
