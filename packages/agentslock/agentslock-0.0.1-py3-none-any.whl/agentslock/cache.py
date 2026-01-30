"""Git cache management for agents.lock."""

from __future__ import annotations

import fcntl
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agentslock.exceptions import CacheError
from agentslock.paths import get_cache_dir
from agentslock.util import ensure_dir, safe_remove


@dataclass
class RepoMetadata:
    """Metadata for a cached git repository."""

    repo_url: str
    default_branch: str | None = None
    last_fetch: datetime | None = None
    refs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_url": self.repo_url,
            "default_branch": self.default_branch,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
            "refs": self.refs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepoMetadata:
        last_fetch = None
        if data.get("last_fetch"):
            last_fetch = datetime.fromisoformat(data["last_fetch"])
        return cls(
            repo_url=data["repo_url"],
            default_branch=data.get("default_branch"),
            last_fetch=last_fetch,
            refs=data.get("refs", {}),
        )


class GitCache:
    """Manages git repository cache with bare clones and worktrees."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or get_cache_dir()
        self.git_dir = self.cache_dir / "git"
        self.locks_dir = self.cache_dir / "locks"
        ensure_dir(self.git_dir)
        ensure_dir(self.locks_dir)

    def _repo_hash(self, repo_url: str) -> str:
        return hashlib.sha256(repo_url.encode()).hexdigest()[:16]

    def _repo_dir_name(self, repo_url: str) -> str:
        parsed = urlparse(repo_url)
        host = parsed.netloc.replace(":", "_")
        path = parsed.path.rstrip("/").lstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return f"{host}/{path}"

    def _repo_path(self, repo_url: str) -> Path:
        return self.git_dir / self._repo_dir_name(repo_url)

    def _bare_repo_path(self, repo_url: str) -> Path:
        return self._repo_path(repo_url) / "repo.git"

    def _worktrees_path(self, repo_url: str) -> Path:
        return self._repo_path(repo_url) / "worktrees"

    def _worktree_path(self, repo_url: str, rev: str) -> Path:
        return self._worktrees_path(repo_url) / rev[:12]

    def _metadata_path(self, repo_url: str) -> Path:
        return self._repo_path(repo_url) / "metadata.json"

    def _lock_path(self, repo_url: str) -> Path:
        return self.locks_dir / f"{self._repo_hash(repo_url)}.lock"

    def _acquire_lock(self, repo_url: str) -> int:
        lock_path = self._lock_path(repo_url)
        ensure_dir(lock_path.parent)
        fd = open(lock_path, "w")
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
            return fd.fileno()
        except Exception:
            fd.close()
            raise

    def _release_lock(self, fd: int) -> None:
        import os

        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except Exception:
            pass

    def _run_git(self, args: list[str], cwd: Path | None = None) -> str:
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise CacheError(f"Git command failed: {' '.join(cmd)}\n{e.stderr}")

    def _load_metadata(self, repo_url: str) -> RepoMetadata | None:
        path = self._metadata_path(repo_url)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return RepoMetadata.from_dict(data)
        except Exception:
            return None

    def _save_metadata(self, repo_url: str, metadata: RepoMetadata) -> None:
        path = self._metadata_path(repo_url)
        ensure_dir(path.parent)
        path.write_text(json.dumps(metadata.to_dict(), indent=2))

    def has_repo(self, repo_url: str) -> bool:
        return self._bare_repo_path(repo_url).exists()

    def has_rev(self, repo_url: str, rev: str) -> bool:
        worktree = self._worktree_path(repo_url, rev)
        return worktree.exists()

    def clone(self, repo_url: str) -> RepoMetadata:
        """Clone a repository as a bare repo."""
        lock_fd = self._acquire_lock(repo_url)
        try:
            bare_path = self._bare_repo_path(repo_url)
            if bare_path.exists():
                return self._load_metadata(repo_url) or RepoMetadata(repo_url=repo_url)

            ensure_dir(bare_path.parent)
            self._run_git(["clone", "--bare", repo_url, str(bare_path)])

            # Get default branch
            default_branch = self._get_default_branch(bare_path)

            metadata = RepoMetadata(
                repo_url=repo_url,
                default_branch=default_branch,
                last_fetch=datetime.now(timezone.utc),
            )
            self._save_metadata(repo_url, metadata)
            return metadata
        finally:
            self._release_lock(lock_fd)

    def _get_default_branch(self, bare_path: Path) -> str | None:
        try:
            output = self._run_git(["symbolic-ref", "HEAD"], cwd=bare_path)
            if output.startswith("refs/heads/"):
                return output[len("refs/heads/") :]
        except CacheError:
            pass
        return None

    def fetch(self, repo_url: str) -> RepoMetadata:
        lock_fd = self._acquire_lock(repo_url)
        try:
            bare_path = self._bare_repo_path(repo_url)
            if not bare_path.exists():
                return self.clone(repo_url)

            self._run_git(["fetch", "--prune", "origin"], cwd=bare_path)

            metadata = self._load_metadata(repo_url) or RepoMetadata(repo_url=repo_url)
            metadata.last_fetch = datetime.now(timezone.utc)
            self._save_metadata(repo_url, metadata)
            return metadata
        finally:
            self._release_lock(lock_fd)

    def resolve_ref(self, repo_url: str, ref: str) -> str:
        bare_path = self._bare_repo_path(repo_url)
        if not bare_path.exists():
            self.clone(repo_url)

        try:
            return self._run_git(["rev-parse", ref], cwd=bare_path)
        except CacheError:
            # Try fetching first
            self.fetch(repo_url)
            return self._run_git(["rev-parse", ref], cwd=bare_path)

    def has_commit(self, repo_url: str, rev: str) -> bool:
        bare_path = self._bare_repo_path(repo_url)
        if not bare_path.exists():
            return False
        try:
            self._run_git(["cat-file", "-t", rev], cwd=bare_path)
            return True
        except CacheError:
            return False

    def checkout(self, repo_url: str, rev: str, force_fetch: bool = False) -> Path:
        """
        Get or create a worktree for a specific revision.

        Returns the path to the worktree.
        """
        lock_fd = self._acquire_lock(repo_url)
        try:
            worktree_path = self._worktree_path(repo_url, rev)

            # Return existing worktree
            if worktree_path.exists():
                return worktree_path

            bare_path = self._bare_repo_path(repo_url)
            if not bare_path.exists():
                self.clone(repo_url)

            # Check if commit exists
            if not self.has_commit(repo_url, rev):
                if force_fetch:
                    self.fetch(repo_url)
                    if not self.has_commit(repo_url, rev):
                        raise CacheError(f"Commit {rev} not found in {repo_url}")
                else:
                    # Try fetching once
                    self.fetch(repo_url)
                    if not self.has_commit(repo_url, rev):
                        raise CacheError(f"Commit {rev} not found in {repo_url}")

            # Create worktree
            ensure_dir(worktree_path.parent)
            self._run_git(
                ["worktree", "add", "--detach", str(worktree_path), rev],
                cwd=bare_path,
            )

            return worktree_path
        finally:
            self._release_lock(lock_fd)

    def get_worktree(self, repo_url: str, rev: str) -> Path | None:
        worktree = self._worktree_path(repo_url, rev)
        if worktree.exists():
            return worktree
        return None

    def list_worktrees(self, repo_url: str) -> list[str]:
        worktrees_path = self._worktrees_path(repo_url)
        if not worktrees_path.exists():
            return []
        return [d.name for d in worktrees_path.iterdir() if d.is_dir()]

    def remove_worktree(self, repo_url: str, rev: str) -> None:
        lock_fd = self._acquire_lock(repo_url)
        try:
            worktree_path = self._worktree_path(repo_url, rev)
            bare_path = self._bare_repo_path(repo_url)

            if worktree_path.exists():
                self._run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=bare_path)
        finally:
            self._release_lock(lock_fd)

    def prune_worktrees(self, repo_url: str, keep_revs: list[str]) -> list[str]:
        removed = []
        for rev in self.list_worktrees(repo_url):
            if rev not in [r[:12] for r in keep_revs]:
                self.remove_worktree(repo_url, rev)
                removed.append(rev)
        return removed

    def list_repos(self) -> list[str]:
        repos = []
        for meta_file in self.git_dir.rglob("metadata.json"):
            try:
                data = json.loads(meta_file.read_text())
                if "repo_url" in data:
                    repos.append(data["repo_url"])
            except Exception:
                continue
        return repos

    def remove_repo(self, repo_url: str) -> None:
        lock_fd = self._acquire_lock(repo_url)
        try:
            repo_path = self._repo_path(repo_url)
            safe_remove(repo_path)
        finally:
            self._release_lock(lock_fd)

    def clear(self) -> None:
        safe_remove(self.git_dir)
        ensure_dir(self.git_dir)

    def get_stats(self) -> dict[str, Any]:
        repos = self.list_repos()
        total_worktrees = 0
        for repo_url in repos:
            total_worktrees += len(self.list_worktrees(repo_url))

        return {
            "cache_dir": str(self.cache_dir),
            "repos": len(repos),
            "worktrees": total_worktrees,
        }
