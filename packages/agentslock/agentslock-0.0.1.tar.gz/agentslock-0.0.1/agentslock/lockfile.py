"""AGENTS.lock file parsing, validation, and serialization."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.items import Table

from agentslock.exceptions import LockfileError, ValidationError
from agentslock.model import (
    Agent,
    ClientId,
    ClientOverride,
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
)

CURRENT_VERSION = 1


def parse_lockfile(path: Path) -> Lockfile:
    """Parse an AGENTS.lock file and return a Lockfile object."""
    if not path.exists():
        raise LockfileError(f"Lockfile not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as e:
        raise LockfileError(f"Invalid TOML in {path}: {e}")

    return _parse_data(data, path)


def parse_lockfile_str(content: str, path: Path | None = None) -> Lockfile:
    """Parse AGENTS.lock content from a string."""
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as e:
        raise LockfileError(f"Invalid TOML: {e}")

    return _parse_data(data, path)


def _parse_data(data: dict[str, Any], path: Path | None) -> Lockfile:
    """Parse raw TOML data into a Lockfile object."""
    version = data.get("version")
    if version is None:
        raise ValidationError("Missing required field 'version'.")
    if not isinstance(version, int):
        raise ValidationError(f"Field 'version' must be an integer, got {type(version).__name__}.")

    project = _parse_project(data.get("project", {}))
    defaults = _parse_defaults(data.get("defaults", {}))
    groups = _parse_groups(data.get("groups", {"default": "Default group"}))

    skills = [_parse_skill(s) for s in data.get("skills", [])]
    agents = [_parse_agent(a) for a in data.get("agents", [])]
    mcp_servers = [_parse_mcp_server(m) for m in data.get("mcp_servers", [])]
    instructions = [_parse_instructions(i) for i in data.get("instructions", [])]

    return Lockfile(
        version=version,
        project=project,
        defaults=defaults,
        groups=groups,
        skills=skills,
        agents=agents,
        mcp_servers=mcp_servers,
        instructions=instructions,
        path=path,
    )


def _parse_project(data: dict[str, Any]) -> Project:
    return Project(
        name=data.get("name", "unnamed"),
        description=data.get("description", ""),
    )


def _parse_defaults(data: dict[str, Any]) -> Defaults:
    clients_raw = data.get("clients", ["claude"])
    clients = [ClientId.from_str(c) for c in clients_raw]
    groups = data.get("groups", ["default"])
    return Defaults(clients=clients, groups=groups)


def _parse_groups(data: dict[str, str]) -> dict[str, str]:
    if "default" not in data:
        data["default"] = "Default group"
    return data


def _parse_source(data: dict[str, Any], allow_inline: bool = False) -> GitSource | PathSource | InlineSource:
    """Parse a source table."""
    src_type = data.get("type")
    if src_type == "git":
        return GitSource(
            repo=data.get("repo", ""),
            rev=data.get("rev", ""),
            ref=data.get("ref"),
            subdir=data.get("subdir", ""),
            file=data.get("file", ""),
        )
    elif src_type == "path":
        return PathSource(path=data.get("path", ""))
    elif src_type == "inline" and allow_inline:
        return InlineSource(content=data.get("content", ""))
    else:
        valid = "git, path" + (", inline" if allow_inline else "")
        raise ValidationError(f"Invalid source type '{src_type}'. Valid types: {valid}")


def _parse_client_overrides(data: dict[str, Any]) -> dict[str, ClientOverride]:
    """Parse client_overrides table."""
    overrides = {}
    for client_str, override_data in data.items():
        try:
            client = ClientId.from_str(client_str)
        except ValidationError:
            continue  # Skip unknown clients
        overrides[client.value] = ClientOverride(
            enabled=override_data.get("enabled"),
            name=override_data.get("name"),
            config=override_data.get("config"),
        )
    return overrides


def _parse_skill(data: dict[str, Any]) -> Skill:
    if "name" not in data:
        raise ValidationError("Skill entry missing required field 'name'.")
    if "flavor" not in data:
        raise ValidationError(f"Skill '{data['name']}' missing required field 'flavor'.")
    if "source" not in data:
        raise ValidationError(f"Skill '{data['name']}' missing required field 'source'.")

    source = _parse_source(data["source"])
    if isinstance(source, InlineSource):
        raise ValidationError(f"Skill '{data['name']}' cannot use inline source.")

    return Skill(
        name=data["name"],
        flavor=data["flavor"],
        source=source,
        groups=data.get("groups", ["default"]),
        enabled=data.get("enabled", True),
        client_overrides=_parse_client_overrides(data.get("client_overrides", {})),
    )


def _parse_agent(data: dict[str, Any]) -> Agent:
    if "name" not in data:
        raise ValidationError("Agent entry missing required field 'name'.")
    if "flavor" not in data:
        raise ValidationError(f"Agent '{data['name']}' missing required field 'flavor'.")
    if "source" not in data:
        raise ValidationError(f"Agent '{data['name']}' missing required field 'source'.")

    source = _parse_source(data["source"])
    if isinstance(source, InlineSource):
        raise ValidationError(f"Agent '{data['name']}' cannot use inline source.")

    return Agent(
        name=data["name"],
        flavor=data["flavor"],
        source=source,
        groups=data.get("groups", ["default"]),
        enabled=data.get("enabled", True),
        client_overrides=_parse_client_overrides(data.get("client_overrides", {})),
    )


def _parse_mcp_config(data: dict[str, Any]) -> MCPConfig:
    """Parse MCP server config table."""
    transport_str = data.get("transport", "stdio")
    try:
        transport = Transport(transport_str)
    except ValueError:
        valid = ", ".join(t.value for t in Transport)
        raise ValidationError(f"Invalid transport '{transport_str}'. Valid: {valid}")

    return MCPConfig(
        transport=transport,
        command=data.get("command"),
        args=data.get("args", []),
        env=data.get("env", {}),
        cwd=data.get("cwd"),
        url=data.get("url"),
        headers=data.get("headers", {}),
        timeout=data.get("timeout"),
        tool_filters=data.get("tool_filters"),
    )


def _parse_mcp_server(data: dict[str, Any]) -> MCPServer:
    if "name" not in data:
        raise ValidationError("MCP server entry missing required field 'name'.")
    if "flavor" not in data:
        raise ValidationError(f"MCP server '{data['name']}' missing required field 'flavor'.")
    if "config" not in data:
        raise ValidationError(f"MCP server '{data['name']}' missing required field 'config'.")

    return MCPServer(
        name=data["name"],
        flavor=data["flavor"],
        config=_parse_mcp_config(data["config"]),
        groups=data.get("groups", ["default"]),
        enabled=data.get("enabled", True),
        client_overrides=_parse_client_overrides(data.get("client_overrides", {})),
    )


def _parse_instructions(data: dict[str, Any]) -> Instructions:
    if "name" not in data:
        raise ValidationError("Instructions entry missing required field 'name'.")
    if "kind" not in data:
        raise ValidationError(f"Instructions '{data['name']}' missing required field 'kind'.")

    kind_str = data["kind"]
    if kind_str == "claude-md":
        kind = InstructionKind.AGENTS_MD
    else:
        try:
            kind = InstructionKind(kind_str)
        except ValueError:
            valid = ", ".join(k.value for k in InstructionKind)
            raise ValidationError(f"Invalid instruction kind '{kind_str}'. Valid: {valid}")

    source = None
    if "source" in data:
        source = _parse_source(data["source"], allow_inline=True)

    targets = None
    if "targets" in data:
        targets = [ClientId.from_str(t) for t in data["targets"]]

    mode_str = data.get("mode", "replace")
    try:
        mode = InstructionMode(mode_str)
    except ValueError:
        valid = ", ".join(m.value for m in InstructionMode)
        raise ValidationError(f"Invalid instruction mode '{mode_str}'. Valid: {valid}")

    return Instructions(
        name=data["name"],
        kind=kind,
        source=source,
        targets=targets,
        groups=data.get("groups", ["default"]),
        enabled=data.get("enabled", True),
        mode=mode,
        delimiter=data.get("delimiter"),
        output_path=data.get("output_path"),
        client_overrides=_parse_client_overrides(data.get("client_overrides", {})),
    )


# Serialization


def serialize_lockfile(lockfile: Lockfile) -> str:
    """Serialize a Lockfile object to TOML string."""
    doc = tomlkit.document()

    doc.add("version", tomlkit.item(lockfile.version))
    doc.add(tomlkit.nl())

    # Project
    project = tomlkit.table()
    project.add("name", lockfile.project.name)
    if lockfile.project.description:
        project.add("description", lockfile.project.description)
    doc.add("project", project)
    doc.add(tomlkit.nl())

    # Defaults
    defaults = tomlkit.table()
    defaults.add("clients", [c.value for c in lockfile.defaults.clients])
    defaults.add("groups", lockfile.defaults.groups)
    doc.add("defaults", defaults)
    doc.add(tomlkit.nl())

    # Groups
    groups = tomlkit.table()
    for name, desc in lockfile.groups.items():
        groups.add(name, desc)
    doc.add("groups", groups)
    doc.add(tomlkit.nl())

    # Skills (array of tables)
    if lockfile.skills:
        skills_aot = tomlkit.aot()
        for skill in lockfile.skills:
            skills_aot.append(_create_skill_table(skill))
        doc.add("skills", skills_aot)

    # Agents (array of tables)
    if lockfile.agents:
        agents_aot = tomlkit.aot()
        for agent in lockfile.agents:
            agents_aot.append(_create_agent_table(agent))
        doc.add("agents", agents_aot)

    # MCP Servers (array of tables)
    if lockfile.mcp_servers:
        mcp_aot = tomlkit.aot()
        for mcp in lockfile.mcp_servers:
            mcp_aot.append(_create_mcp_server_table(mcp))
        doc.add("mcp_servers", mcp_aot)

    # Instructions (array of tables)
    if lockfile.instructions:
        instr_aot = tomlkit.aot()
        for instr in lockfile.instructions:
            instr_aot.append(_create_instructions_table(instr))
        doc.add("instructions", instr_aot)

    return tomlkit.dumps(doc)


def _add_source(table: Table, source: GitSource | PathSource | InlineSource) -> None:
    """Add source subtable to a table."""
    src = tomlkit.table()
    src.add("type", source.type)

    if isinstance(source, GitSource):
        src.add("repo", source.repo)
        src.add("rev", source.rev)
        if source.ref:
            src.add("ref", source.ref)
        if source.subdir:
            src.add("subdir", source.subdir)
        if source.file:
            src.add("file", source.file)
    elif isinstance(source, PathSource):
        src.add("path", source.path)
    elif isinstance(source, InlineSource):
        src.add("content", source.content)

    table.add("source", src)


def _add_client_overrides(table: Table, overrides: dict[str, ClientOverride]) -> None:
    """Add client_overrides subtable if non-empty."""
    if not overrides:
        return

    co = tomlkit.table()
    for client_str, override in overrides.items():
        override_table = tomlkit.table()
        if override.enabled is not None:
            override_table.add("enabled", override.enabled)
        if override.name is not None:
            override_table.add("name", override.name)
        if override.config is not None:
            override_table.add("config", override.config)
        if override_table:
            co.add(client_str, override_table)

    if co:
        table.add("client_overrides", co)


def _create_skill_table(skill: Skill) -> Table:
    """Create a skill table entry."""
    table = tomlkit.table()
    table.add("name", skill.name)
    table.add("flavor", skill.flavor)
    if skill.groups != ["default"]:
        table.add("groups", skill.groups)
    if not skill.enabled:
        table.add("enabled", False)

    _add_source(table, skill.source)
    _add_client_overrides(table, skill.client_overrides)

    return table


def _create_agent_table(agent: Agent) -> Table:
    """Create an agent table entry."""
    table = tomlkit.table()
    table.add("name", agent.name)
    table.add("flavor", agent.flavor)
    if agent.groups != ["default"]:
        table.add("groups", agent.groups)
    if not agent.enabled:
        table.add("enabled", False)

    _add_source(table, agent.source)
    _add_client_overrides(table, agent.client_overrides)

    return table


def _create_mcp_server_table(mcp: MCPServer) -> Table:
    """Create an MCP server table entry."""
    table = tomlkit.table()
    table.add("name", mcp.name)
    table.add("flavor", mcp.flavor)
    if mcp.groups != ["default"]:
        table.add("groups", mcp.groups)
    if not mcp.enabled:
        table.add("enabled", False)

    # Config
    cfg = tomlkit.table()
    cfg.add("transport", mcp.config.transport.value)
    if mcp.config.command:
        cfg.add("command", mcp.config.command)
    if mcp.config.args:
        cfg.add("args", mcp.config.args)
    if mcp.config.env:
        cfg.add("env", mcp.config.env)
    if mcp.config.cwd:
        cfg.add("cwd", mcp.config.cwd)
    if mcp.config.url:
        cfg.add("url", mcp.config.url)
    if mcp.config.headers:
        cfg.add("headers", mcp.config.headers)
    if mcp.config.timeout:
        cfg.add("timeout", mcp.config.timeout)
    if mcp.config.tool_filters:
        cfg.add("tool_filters", mcp.config.tool_filters)
    table.add("config", cfg)

    _add_client_overrides(table, mcp.client_overrides)

    return table


def _create_instructions_table(instr: Instructions) -> Table:
    """Create an instructions table entry."""
    table = tomlkit.table()
    table.add("name", instr.name)
    table.add("kind", instr.kind.value)
    if instr.groups != ["default"]:
        table.add("groups", instr.groups)
    if not instr.enabled:
        table.add("enabled", False)
    if instr.mode != InstructionMode.REPLACE:
        table.add("mode", instr.mode.value)
    if instr.delimiter:
        table.add("delimiter", instr.delimiter)
    if instr.output_path:
        table.add("output_path", instr.output_path)
    if instr.targets:
        table.add("targets", [t.value for t in instr.targets])

    if instr.source:
        _add_source(table, instr.source)

    _add_client_overrides(table, instr.client_overrides)

    return table


def write_lockfile(lockfile: Lockfile, path: Path) -> None:
    """Write a Lockfile to disk."""
    from agentslock.util import atomic_write

    content = serialize_lockfile(lockfile)
    atomic_write(path, content)


def create_default_lockfile(project_name: str = "my-project") -> Lockfile:
    """Create a new default lockfile."""
    return Lockfile(
        version=CURRENT_VERSION,
        project=Project(name=project_name),
        defaults=Defaults(),
        groups={"default": "Default group"},
        skills=[],
        agents=[],
        mcp_servers=[],
        instructions=[],
    )


def create_default_instructions_content() -> str:
    """Create default content for AGENTS.lock.instructions file."""
    return """# Project Instructions

This file contains instructions that will be synced to AI CLI clients.

## Guidelines

- Keep responses concise and focused
- Follow the project's coding standards
- Ask for clarification when requirements are unclear
"""
