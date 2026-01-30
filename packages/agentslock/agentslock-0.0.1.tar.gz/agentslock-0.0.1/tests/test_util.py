"""Tests for utility functions."""

from __future__ import annotations

import pytest

from agentslock.util import parse_github_url


class TestParseGitHubUrl:
    def test_simple_repo_url(self):
        result = parse_github_url("https://github.com/owner/repo")
        assert result["repo"] == "https://github.com/owner/repo"
        assert result["ref"] is None
        assert result["subdir"] == ""

    def test_repo_url_with_git_suffix(self):
        result = parse_github_url("https://github.com/owner/repo.git")
        assert result["repo"] == "https://github.com/owner/repo"
        assert result["ref"] is None

    def test_repo_url_with_tree(self):
        result = parse_github_url("https://github.com/anthropics/skills/tree/main/skills/canvas-design")
        assert result["repo"] == "https://github.com/anthropics/skills"
        assert result["ref"] == "main"
        assert result["subdir"] == "skills/canvas-design"

    def test_repo_url_with_tree_no_subdir(self):
        result = parse_github_url("https://github.com/owner/repo/tree/develop")
        assert result["repo"] == "https://github.com/owner/repo"
        assert result["ref"] == "develop"
        assert result["subdir"] == ""

    def test_repo_url_with_blob(self):
        result = parse_github_url("https://github.com/owner/repo/blob/main/path/to/file.md")
        assert result["repo"] == "https://github.com/owner/repo"
        assert result["ref"] == "main"
        assert result["file"] == "path/to/file.md"

    def test_ssh_url(self):
        result = parse_github_url("git@github.com:owner/repo.git")
        assert result["repo"] == "https://github.com/owner/repo"
        assert result["ref"] is None

    def test_ssh_url_no_git_suffix(self):
        result = parse_github_url("git@github.com:owner/repo")
        assert result["repo"] == "https://github.com/owner/repo"

    def test_nested_subdir(self):
        result = parse_github_url("https://github.com/org/monorepo/tree/v2.0/packages/core/lib")
        assert result["repo"] == "https://github.com/org/monorepo"
        assert result["ref"] == "v2.0"
        assert result["subdir"] == "packages/core/lib"

    def test_trailing_slash(self):
        result = parse_github_url("https://github.com/owner/repo/")
        assert result["repo"] == "https://github.com/owner/repo"

    def test_gitlab_url_with_tree(self):
        result = parse_github_url("https://gitlab.com/owner/repo/tree/main/subdir")
        assert result["repo"] == "https://gitlab.com/owner/repo"
        assert result["ref"] == "main"
        assert result["subdir"] == "subdir"
