"""Pytest fixtures for agents.lock tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_lockfile_content() -> str:
    """Return a sample AGENTS.lock content."""
    return '''version = 1

[project]
name = "test-project"
description = "A test project"

[defaults]
clients = ["claude", "codex"]
groups = ["default"]

[groups]
default = "Default group"
coding = "Coding tools"

[[skills]]
name = "skill-one"
flavor = "claude-skill-v1"
groups = ["default"]

  [skills.source]
  type = "path"
  path = "./skills/skill-one"

[[skills]]
name = "skill-two"
flavor = "claude-skill-v1"
groups = ["default", "coding"]

  [skills.source]
  type = "path"
  path = "./skills/skill-two"

[[mcp_servers]]
name = "test-server"
flavor = "mcp-v1"
groups = ["default"]

  [mcp_servers.config]
  transport = "stdio"
  command = "node"
  args = ["server.js"]
  tool_filters = { include = ["search"], exclude = ["dangerous"] }

[[instructions]]
name = "main-instructions"
kind = "agents-md"
mode = "replace"
'''


@pytest.fixture
def sample_lockfile(temp_dir: Path, sample_lockfile_content: str) -> Path:
    """Create a sample AGENTS.lock file."""
    lockfile_path = temp_dir / "AGENTS.lock"
    lockfile_path.write_text(sample_lockfile_content)

    # Create skill directories
    skill_dir1 = temp_dir / "skills" / "skill-one"
    skill_dir1.mkdir(parents=True)
    (skill_dir1 / "SKILL.md").write_text("# Skill One\n\nThis is a test skill.")

    skill_dir2 = temp_dir / "skills" / "skill-two"
    skill_dir2.mkdir(parents=True)
    (skill_dir2 / "SKILL.md").write_text("# Skill Two\n\nThis is another test skill.")

    # Create instructions file
    (temp_dir / "AGENTS.lock.instructions").write_text("# Test Instructions\n\nBe helpful.")

    return lockfile_path
