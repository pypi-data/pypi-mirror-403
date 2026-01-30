"""Source resolution for agents.lock resources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentslock.cache import GitCache
from agentslock.exceptions import ResolveError
from agentslock.model import (
    Agent,
    GitSource,
    InlineSource,
    Instructions,
    Lockfile,
    PathSource,
    Skill,
    Source,
)
from agentslock.paths import get_default_instructions_path


@dataclass
class ResolvedSource:
    """Result of resolving a source to a local path or content."""

    path: Path | None = None
    content: str | None = None
    is_directory: bool = False

    @property
    def exists(self) -> bool:
        if self.content is not None:
            return True
        if self.path:
            return self.path.exists()
        return False


class SourceResolver:
    """Resolves sources to local paths using the git cache."""

    def __init__(self, lockfile: Lockfile, cache: GitCache | None = None):
        self.lockfile = lockfile
        self.cache = cache or GitCache()
        self.lockfile_dir = lockfile.path.parent if lockfile.path else Path.cwd()

    def resolve(self, source: Source | None, allow_missing: bool = False) -> ResolvedSource:
        if source is None:
            # Default to instructions file
            default_path = get_default_instructions_path(
                self.lockfile.path or (self.lockfile_dir / "AGENTS.lock")
            )
            if not default_path.exists() and not allow_missing:
                raise ResolveError(
                    f"Default instructions file not found: {default_path}\n"
                    "Create it or specify a source explicitly."
                )
            return ResolvedSource(path=default_path)

        if isinstance(source, GitSource):
            return self._resolve_git(source)
        elif isinstance(source, PathSource):
            return self._resolve_path(source, allow_missing)
        elif isinstance(source, InlineSource):
            return ResolvedSource(content=source.content)
        else:
            raise ResolveError(f"Unknown source type: {type(source)}")

    def _resolve_git(self, source: GitSource) -> ResolvedSource:
        worktree = self.cache.checkout(source.repo, source.rev)

        if source.subdir:
            path = worktree / source.subdir
        else:
            path = worktree

        if source.file:
            path = path / source.file
            return ResolvedSource(path=path, is_directory=False)

        return ResolvedSource(path=path, is_directory=path.is_dir())

    def _resolve_path(self, source: PathSource, allow_missing: bool = False) -> ResolvedSource:
        path = Path(source.path)
        if not path.is_absolute():
            path = (self.lockfile_dir / path).resolve()

        # Validate path doesn't escape lockfile directory for relative paths
        if not source.path.startswith("/"):
            try:
                path.relative_to(self.lockfile_dir)
            except ValueError:
                raise ResolveError(f"Path '{source.path}' escapes the lockfile directory.")

        if not path.exists() and not allow_missing:
            raise ResolveError(f"Path not found: {path}")

        return ResolvedSource(path=path, is_directory=path.is_dir() if path.exists() else False)

    def resolve_skill(self, skill: Skill) -> ResolvedSource:
        return self.resolve(skill.source)

    def resolve_agent(self, agent: Agent) -> ResolvedSource:
        return self.resolve(agent.source)

    def resolve_instructions(self, instructions: Instructions) -> ResolvedSource:
        return self.resolve(instructions.source)

    def ensure_all(self, force_fetch: bool = False) -> dict[str, list[str]]:
        """
        Ensure all git sources are cached.

        Returns dict with lists of fetched/cached repos.
        """
        fetched = []
        cached = []

        git_sources = self._collect_git_sources()
        for source in git_sources:
            if self.cache.has_rev(source.repo, source.rev):
                cached.append(source.repo)
            else:
                self.cache.checkout(source.repo, source.rev, force_fetch=force_fetch)
                fetched.append(source.repo)

        return {"fetched": fetched, "cached": cached}

    def _collect_git_sources(self) -> list[GitSource]:
        sources = []
        seen = set()

        for skill in self.lockfile.skills:
            if isinstance(skill.source, GitSource):
                key = (skill.source.repo, skill.source.rev)
                if key not in seen:
                    sources.append(skill.source)
                    seen.add(key)

        for agent in self.lockfile.agents:
            if isinstance(agent.source, GitSource):
                key = (agent.source.repo, agent.source.rev)
                if key not in seen:
                    sources.append(agent.source)
                    seen.add(key)

        for instr in self.lockfile.instructions:
            if isinstance(instr.source, GitSource):
                key = (instr.source.repo, instr.source.rev)
                if key not in seen:
                    sources.append(instr.source)
                    seen.add(key)

        return sources


def find_skill_root(path: Path) -> Path | None:
    """
    Find the skill root directory by looking for SKILL.md.

    Searches upward from the given path.
    """
    current = path if path.is_dir() else path.parent

    while current != current.parent:
        skill_md = current / "SKILL.md"
        if skill_md.exists():
            return current
        current = current.parent

    return None


def find_agent_file(path: Path) -> Path | None:
    """
    Find an agent definition file.

    Looks for .md files with agent frontmatter.
    """
    if path.is_file() and path.suffix == ".md":
        return path

    if path.is_dir():
        for md_file in path.glob("*.md"):
            content = md_file.read_text()
            if "---" in content:  # Has frontmatter
                return md_file

    return None


def scan_for_skills(path: Path) -> list[Path]:
    skills = []
    for skill_md in path.rglob("SKILL.md"):
        skills.append(skill_md.parent)
    return skills


def scan_for_agents(path: Path) -> list[Path]:
    agents = []
    for md_file in path.rglob("*.md"):
        if md_file.name == "SKILL.md":
            continue
        # Simple heuristic: has frontmatter
        try:
            content = md_file.read_text()
            if content.startswith("---"):
                agents.append(md_file)
        except Exception:
            continue
    return agents
