"""Base renderer class for client configurations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from agentslock.model import (
    Agent,
    ClientId,
    ClientOverride,
    Instructions,
    MCPServer,
    Skill,
)
from agentslock.paths import ClientPaths, Scope, get_managed_prefix

if TYPE_CHECKING:
    from agentslock.model import Lockfile
    from agentslock.resolve import SourceResolver

INSTRUCTION_MARKER_BEGIN = "<!-- agents.lock:begin name={name} -->"
INSTRUCTION_MARKER_END = "<!-- agents.lock:end -->"


@dataclass
class FileOutput:
    """Represents a file to be written."""

    path: Path
    content: str | bytes
    is_binary: bool = False


@dataclass
class DirectoryOutput:
    """Represents a directory to be copied."""

    path: Path
    source_path: Path


@dataclass
class ConfigUpdate:
    """Represents an update to a config file (merge operation)."""

    path: Path
    key: str
    value: dict | None  # None means delete


@dataclass
class RenderResult:
    """Result of rendering a client configuration."""

    client: ClientId
    files: list[FileOutput] = field(default_factory=list)
    directories: list[DirectoryOutput] = field(default_factory=list)
    config_updates: list[ConfigUpdate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class BaseRenderer(ABC):
    """Base class for client configuration renderers."""

    client: ClientId

    def __init__(
        self,
        lockfile: "Lockfile",
        resolver: "SourceResolver",
        scope: Scope,
        project_root: Path | None = None,
    ):
        self.lockfile = lockfile
        self.resolver = resolver
        self.scope: Scope = scope
        self.project_root = project_root or Path.cwd()
        self.paths = ClientPaths(self.client, self.project_root)
        self.prefix = get_managed_prefix()

    def render(self) -> RenderResult:
        result = RenderResult(client=self.client)

        self._render_skills(result)
        self._render_agents(result)
        self._render_mcp_servers(result)
        self._render_instructions(result)

        return result

    def _get_override(self, entry: Skill | Agent | MCPServer | Instructions) -> ClientOverride | None:
        return entry.client_overrides.get(self.client.value)

    def _is_enabled(self, entry: Skill | Agent | MCPServer | Instructions) -> bool:
        override = self._get_override(entry)
        if override and override.enabled is not None:
            return override.enabled
        return entry.enabled

    def _get_name(self, entry: Skill | Agent | MCPServer | Instructions) -> str:
        override = self._get_override(entry)
        if override and override.name:
            return override.name
        return entry.name

    @abstractmethod
    def _render_skills(self, result: RenderResult) -> None:
        pass

    @abstractmethod
    def _render_agents(self, result: RenderResult) -> None:
        pass

    @abstractmethod
    def _render_mcp_servers(self, result: RenderResult) -> None:
        pass

    @abstractmethod
    def _render_instructions(self, result: RenderResult) -> None:
        pass

    def _wrap_instructions_content(self, name: str, content: str) -> str:
        begin = INSTRUCTION_MARKER_BEGIN.format(name=name)
        end = INSTRUCTION_MARKER_END
        return f"{begin}\n{content}\n{end}"

    def _extract_managed_section(self, content: str, name: str) -> tuple[str | None, int, int]:
        """
        Find managed section in content.

        Returns (section_content, start_pos, end_pos) or (None, -1, -1).
        """
        begin = INSTRUCTION_MARKER_BEGIN.format(name=name)
        end = INSTRUCTION_MARKER_END

        start = content.find(begin)
        if start == -1:
            return None, -1, -1

        end_marker_start = content.find(end, start)
        if end_marker_start == -1:
            return None, -1, -1

        end_pos = end_marker_start + len(end)

        # Include trailing newline if present
        if end_pos < len(content) and content[end_pos] == "\n":
            end_pos += 1

        section = content[start:end_pos]
        return section, start, end_pos

    def _managed_key(self, name: str) -> str:
        return f"{self.prefix}{name}"
