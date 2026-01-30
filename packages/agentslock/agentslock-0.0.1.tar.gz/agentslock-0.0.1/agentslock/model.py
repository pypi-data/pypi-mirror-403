"""Data models for agents.lock lockfile entries and configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from agentslock.exceptions import ValidationError

# Name pattern: lowercase, hyphenated, 1-64 chars
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
# Flavor pattern: lowercase-v + version number
FLAVOR_PATTERN = re.compile(r"^[a-z0-9-]+-v[0-9]+$")
# Git SHA pattern: 7+ hex chars or full 40
GIT_SHA_PATTERN = re.compile(r"^[a-f0-9]{7,40}$")


class ClientId(str, Enum):
    """Supported AI CLI client identifiers."""

    CLAUDE = "claude"
    CODEX = "codex"
    GEMINI = "gemini"
    COPILOT = "copilot"

    @classmethod
    def from_str(cls, value: str) -> ClientId:
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(c.value for c in cls)
            raise ValidationError(f"Invalid client '{value}'. Valid clients: {valid}")


class Transport(str, Enum):
    """MCP server transport types."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class InstructionKind(str, Enum):
    """Instruction file kind."""

    AGENTS_MD = "agents-md"
    COPILOT_INSTRUCTIONS_MD = "copilot-instructions-md"
    CUSTOM = "custom"


class InstructionMode(str, Enum):
    """How instructions are applied to target files."""

    REPLACE = "replace"
    APPEND = "append"
    PREPEND = "prepend"


def validate_name(name: str) -> str:
    if not NAME_PATTERN.match(name):
        raise ValidationError(
            f"Invalid name '{name}'. Must be lowercase, hyphenated, 1-64 chars, "
            "matching pattern: ^[a-z0-9][a-z0-9-]{{0,63}}$"
        )
    return name


def validate_flavor(flavor: str) -> str:
    if not FLAVOR_PATTERN.match(flavor):
        raise ValidationError(
            f"Invalid flavor '{flavor}'. Must match pattern: ^[a-z0-9-]+-v[0-9]+$"
        )
    return flavor


def validate_git_sha(sha: str) -> str:
    if not GIT_SHA_PATTERN.match(sha):
        raise ValidationError(
            f"Invalid git SHA '{sha}'. Must be 7-40 hex characters."
        )
    return sha


@dataclass
class GitSource:
    """Git repository source with pinned commit."""

    repo: str
    rev: str
    ref: str | None = None
    subdir: str = ""
    file: str = ""

    def __post_init__(self) -> None:
        validate_git_sha(self.rev)
        if self.subdir:
            if ".." in self.subdir or self.subdir.startswith("/"):
                raise ValidationError(
                    f"Invalid subdir '{self.subdir}'. Must be relative without '..'."
                )
        if self.file and ".." in self.file:
            raise ValidationError(
                f"Invalid file path '{self.file}'. Must not contain '..'."
            )

    @property
    def type(self) -> Literal["git"]:
        return "git"


@dataclass
class PathSource:
    """Local path source with relative path."""

    path: str

    def __post_init__(self) -> None:
        # Allow absolute paths on input but validate traversal
        if ".." in Path(self.path).parts:
            # Check if it escapes the lockfile directory (validated at resolve time)
            pass

    @property
    def type(self) -> Literal["path"]:
        return "path"


@dataclass
class InlineSource:
    """Inline content source (instructions only)."""

    content: str

    @property
    def type(self) -> Literal["inline"]:
        return "inline"


Source = GitSource | PathSource | InlineSource


@dataclass
class ClientOverride:
    """Per-client override for a resource."""

    enabled: bool | None = None
    name: str | None = None
    config: dict[str, Any] | None = None


@dataclass
class MCPConfig:
    """Normalized MCP server configuration."""

    transport: Transport
    # stdio transport
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    # http/sse transport
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    # common
    timeout: int | None = None
    tool_filters: dict[str, list[str]] | None = None

    def __post_init__(self) -> None:
        if self.transport == Transport.STDIO:
            if not self.command:
                raise ValidationError("stdio transport requires 'command' field.")
        elif self.transport in (Transport.HTTP, Transport.SSE):
            if not self.url:
                raise ValidationError(f"{self.transport.value} transport requires 'url' field.")


@dataclass
class Skill:
    """Skill entry in the lockfile."""

    name: str
    flavor: str
    source: GitSource | PathSource
    groups: list[str] = field(default_factory=lambda: ["default"])
    enabled: bool = True
    client_overrides: dict[str, ClientOverride] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = validate_name(self.name)
        self.flavor = validate_flavor(self.flavor)


@dataclass
class Agent:
    """Agent entry in the lockfile."""

    name: str
    flavor: str
    source: GitSource | PathSource
    groups: list[str] = field(default_factory=lambda: ["default"])
    enabled: bool = True
    client_overrides: dict[str, ClientOverride] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = validate_name(self.name)
        self.flavor = validate_flavor(self.flavor)


@dataclass
class MCPServer:
    """MCP server entry in the lockfile."""

    name: str
    flavor: str
    config: MCPConfig
    groups: list[str] = field(default_factory=lambda: ["default"])
    enabled: bool = True
    client_overrides: dict[str, ClientOverride] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = validate_name(self.name)
        self.flavor = validate_flavor(self.flavor)


@dataclass
class Instructions:
    """Instructions entry in the lockfile."""

    name: str
    kind: InstructionKind
    source: Source | None = None
    targets: list[ClientId] | None = None
    groups: list[str] = field(default_factory=lambda: ["default"])
    enabled: bool = True
    mode: InstructionMode = InstructionMode.REPLACE
    delimiter: str | None = None
    output_path: str | None = None
    client_overrides: dict[str, ClientOverride] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.name = validate_name(self.name)


@dataclass
class Project:
    """Project metadata in the lockfile."""

    name: str
    description: str = ""


@dataclass
class Defaults:
    """Default settings in the lockfile."""

    clients: list[ClientId] = field(default_factory=lambda: [ClientId.CLAUDE])
    groups: list[str] = field(default_factory=lambda: ["default"])


@dataclass
class Lockfile:
    """Complete parsed AGENTS.lock structure."""

    version: int
    project: Project
    defaults: Defaults
    groups: dict[str, str]
    skills: list[Skill] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    mcp_servers: list[MCPServer] = field(default_factory=list)
    instructions: list[Instructions] = field(default_factory=list)
    path: Path | None = None

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValidationError(
                f"Unknown lockfile version {self.version}. Supported: 1"
            )
        self._validate_groups()
        self._validate_unique_names()
        self._validate_instructions()

    def _validate_groups(self) -> None:
        defined_groups = set(self.groups.keys())
        for skill in self.skills:
            for g in skill.groups:
                if g not in defined_groups:
                    raise ValidationError(
                        f"Skill '{skill.name}' references undefined group '{g}'."
                    )
        for agent in self.agents:
            for g in agent.groups:
                if g not in defined_groups:
                    raise ValidationError(
                        f"Agent '{agent.name}' references undefined group '{g}'."
                    )
        for mcp in self.mcp_servers:
            for g in mcp.groups:
                if g not in defined_groups:
                    raise ValidationError(
                        f"MCP server '{mcp.name}' references undefined group '{g}'."
                    )
        for instr in self.instructions:
            for g in instr.groups:
                if g not in defined_groups:
                    raise ValidationError(
                        f"Instructions '{instr.name}' references undefined group '{g}'."
                    )

    def _validate_unique_names(self) -> None:
        skill_names = [s.name for s in self.skills]
        if len(skill_names) != len(set(skill_names)):
            raise ValidationError("Duplicate skill names found.")

        agent_names = [a.name for a in self.agents]
        if len(agent_names) != len(set(agent_names)):
            raise ValidationError("Duplicate agent names found.")

        mcp_names = [m.name for m in self.mcp_servers]
        if len(mcp_names) != len(set(mcp_names)):
            raise ValidationError("Duplicate MCP server names found.")

        instr_names = [i.name for i in self.instructions]
        if len(instr_names) != len(set(instr_names)):
            raise ValidationError("Duplicate instructions names found.")

    def _validate_instructions(self) -> None:
        # Check for conflicting modes on same output path
        output_modes: dict[str, list[tuple[str, InstructionMode]]] = {}
        for instr in self.instructions:
            if instr.output_path:
                key = instr.output_path
            elif instr.kind == InstructionKind.COPILOT_INSTRUCTIONS_MD:
                key = ".github/copilot-instructions.md"
            else:
                # agents-md maps to multiple files, validated per-client
                continue
            output_modes.setdefault(key, []).append((instr.name, instr.mode))

        for path, modes in output_modes.items():
            replace_entries = [n for n, m in modes if m == InstructionMode.REPLACE]
            if len(replace_entries) > 1:
                raise ValidationError(
                    f"Multiple instructions use 'replace' mode for '{path}': "
                    f"{replace_entries}"
                )
            if replace_entries and len(modes) > 1:
                raise ValidationError(
                    f"Instructions '{replace_entries[0]}' uses 'replace' mode for "
                    f"'{path}', but other instructions also target it."
                )

    def get_skill(self, name: str) -> Skill | None:
        for s in self.skills:
            if s.name == name:
                return s
        return None

    def get_agent(self, name: str) -> Agent | None:
        for a in self.agents:
            if a.name == name:
                return a
        return None

    def get_mcp_server(self, name: str) -> MCPServer | None:
        for m in self.mcp_servers:
            if m.name == name:
                return m
        return None

    def get_instructions(self, name: str) -> Instructions | None:
        for i in self.instructions:
            if i.name == name:
                return i
        return None

    def filter_by_groups(self, groups: list[str]) -> Lockfile:
        """Return a new Lockfile with only entries matching the given groups."""
        return Lockfile(
            version=self.version,
            project=self.project,
            defaults=self.defaults,
            groups=self.groups,
            skills=[s for s in self.skills if any(g in groups for g in s.groups)],
            agents=[a for a in self.agents if any(g in groups for g in a.groups)],
            mcp_servers=[m for m in self.mcp_servers if any(g in groups for g in m.groups)],
            instructions=[i for i in self.instructions if any(g in groups for g in i.groups)],
            path=self.path,
        )

    def filter_enabled(self) -> Lockfile:
        """Return a new Lockfile with only enabled entries."""
        return Lockfile(
            version=self.version,
            project=self.project,
            defaults=self.defaults,
            groups=self.groups,
            skills=[s for s in self.skills if s.enabled],
            agents=[a for a in self.agents if a.enabled],
            mcp_servers=[m for m in self.mcp_servers if m.enabled],
            instructions=[i for i in self.instructions if i.enabled],
            path=self.path,
        )


@dataclass
class GlobalConfig:
    """Global configuration stored in ~/.agents.lock/config.toml."""

    defaults: Defaults = field(default_factory=Defaults)
    aliases: dict[str, str] = field(default_factory=dict)
