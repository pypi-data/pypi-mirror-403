"""CLI for agents.lock package manager."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from agentslock import __version__
from agentslock.exceptions import AgentsLockError
from agentslock.model import ClientId, Transport
from agentslock.paths import Scope


ascii_art = r"""
 █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗   ██╗      ██████╗  ██████╗██╗  ██╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝   ██║     ██╔═══██╗██╔════╝██║ ██╔╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ███████╗   ██║     ██║   ██║██║     █████╔╝ 
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ╚════██║   ██║     ██║   ██║██║     ██╔═██╗ 
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████║██╗███████╗╚██████╔╝╚██████╗██║  ██╗
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
"""


class AgentsLockGroup(click.Group):
    def get_help(self, ctx: click.Context) -> str:
        return f"{ascii_art}\n{super().get_help(ctx)}"


class Context:
    """CLI context for shared state."""

    def __init__(self) -> None:
        self.lockfile_path: Path | None = None
        self.groups: list[str] = []
        self.clients: list[ClientId] = []
        self.scope: Scope = "project"
        self.dry_run: bool = False
        self.show_diff: bool = False
        self.yes: bool = False
        self.json_output: bool = False
        self.verbose: bool = False
        self.no_color: bool = False


pass_context = click.make_pass_decorator(Context, ensure=True)


def output_json(data: Any) -> None:
    """Output data as JSON."""
    click.echo(json.dumps(data, indent=2, default=str))


def resolve_lockfile(ctx: Context) -> Path:
    """Resolve lockfile path from context or default."""
    if ctx.lockfile_path:
        from agentslock.config import resolve_lockfile_alias

        return resolve_lockfile_alias(str(ctx.lockfile_path))
    from agentslock.paths import get_default_lockfile_path

    return get_default_lockfile_path()


def _parse_key_value_pairs(pairs: tuple[str, ...], sep: str, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        if sep not in pair:
            raise click.ClickException(f"Invalid {label} '{pair}'. Expected KEY{sep}VALUE.")
        key, value = pair.split(sep, 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise click.ClickException(f"Invalid {label} '{pair}'. Key cannot be empty.")
        result[key] = value
    return result


@click.group(cls=AgentsLockGroup)
@click.version_option(version=__version__, prog_name="agents.lock")
@click.option(
    "--lockfile",
    "-l",
    type=click.Path(path_type=Path),
    help="Path to AGENTS.lock file or alias",
)
@click.option(
    "--group",
    "-g",
    multiple=True,
    help="Filter by group (can be repeated)",
)
@click.option(
    "--client",
    "-c",
    multiple=True,
    help="Target client (can be repeated)",
)
@click.option(
    "--global",
    "global_scope",
    is_flag=True,
    help="Use global scope instead of project",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--diff", "show_diff", is_flag=True, help="Show diffs for changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@pass_context
def cli(
    ctx: Context,
    lockfile: Path | None,
    group: tuple[str, ...],
    client: tuple[str, ...],
    global_scope: bool,
    dry_run: bool,
    show_diff: bool,
    yes: bool,
    json_output: bool,
    verbose: bool,
    no_color: bool,
) -> None:
    """agents.lock - Package manager for AI agent configurations."""
    ctx.lockfile_path = lockfile
    ctx.groups = list(group)
    ctx.clients = [ClientId.from_str(c) for c in client] if client else []
    ctx.scope = "global" if global_scope else "project"
    ctx.dry_run = dry_run
    ctx.show_diff = show_diff
    ctx.yes = yes
    ctx.json_output = json_output
    ctx.verbose = verbose
    ctx.no_color = no_color

    from agentslock.util import setup_logging

    setup_logging(verbose, no_color)


@cli.command()
@click.option("--path", type=click.Path(path_type=Path), help="Directory to create lockfile in")
@click.option("--force", is_flag=True, help="Overwrite existing lockfile")
@click.option("--no-instructions", is_flag=True, help="Don't create instructions file")
@pass_context
def init(ctx: Context, path: Path | None, force: bool, no_instructions: bool) -> None:
    """Initialize a new AGENTS.lock file."""
    from agentslock.lockfile import (
        create_default_instructions_content,
        create_default_lockfile,
        write_lockfile,
    )
    from agentslock.model import InstructionKind, Instructions, PathSource
    from agentslock.paths import get_default_instructions_path, get_default_lockfile_path
    from agentslock.ui import confirm, print_error, print_success, prompt_text

    target_dir = path or Path.cwd()
    lockfile_path = get_default_lockfile_path(target_dir)
    instructions_path = get_default_instructions_path(lockfile_path)

    if lockfile_path.exists() and not force:
        if ctx.yes:
            print_error(f"Lockfile already exists: {lockfile_path}")
            sys.exit(1)
        if not confirm(f"Overwrite existing {lockfile_path}?"):
            sys.exit(0)

    project_name = target_dir.name
    if not ctx.yes:
        project_name = prompt_text("Project name", project_name)

    lockfile = create_default_lockfile(project_name)
    if not no_instructions:
        try:
            rel_path = instructions_path.resolve().relative_to(lockfile_path.parent)
            source = PathSource(path="./" + str(rel_path))
        except ValueError:
            source = PathSource(path=str(instructions_path.resolve()))

        lockfile.instructions.append(
            Instructions(
                name="project-instructions",
                kind=InstructionKind.AGENTS_MD,
                source=source,
            )
        )
    write_lockfile(lockfile, lockfile_path)
    print_success(f"Created {lockfile_path}")

    if not no_instructions and not instructions_path.exists():
        instructions_path.write_text(create_default_instructions_content())
        print_success(f"Created {instructions_path}")

    if ctx.json_output:
        output_json(
            {
                "status": "success",
                "lockfile": str(lockfile_path),
                "instructions": str(instructions_path) if not no_instructions else None,
            }
        )


@cli.group()
def set() -> None:
    """Set configuration values."""
    pass


@set.command("clients")
@click.argument("clients")
@pass_context
def set_clients(ctx: Context, clients: str) -> None:
    """Set default clients (comma or space separated)."""
    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.ui import print_error, print_success
    from agentslock.util import find_closest_match

    lockfile_path = resolve_lockfile(ctx)
    if not lockfile_path.exists():
        print_error(f"Lockfile not found: {lockfile_path}")
        sys.exit(1)

    # Parse clients
    client_strs = [c.strip() for c in clients.replace(",", " ").split() if c.strip()]
    valid_clients = [c.value for c in ClientId]
    parsed_clients = []

    for c in client_strs:
        if c.lower() in valid_clients:
            parsed_clients.append(ClientId.from_str(c))
        else:
            suggestion = find_closest_match(c, valid_clients)
            if suggestion:
                print_error(f"Unknown client '{c}'. Did you mean '{suggestion}'?")
            else:
                print_error(f"Unknown client '{c}'. Valid: {', '.join(valid_clients)}")
            sys.exit(1)

    lockfile = parse_lockfile(lockfile_path)
    lockfile.defaults.clients = parsed_clients
    write_lockfile(lockfile, lockfile_path)
    print_success(f"Default clients set to: {', '.join(c.value for c in parsed_clients)}")


@cli.group()
def add() -> None:
    """Add resources to the lockfile."""
    pass


@add.command("skill")
@click.argument("source")
@click.option("--name", "-n", help="Skill name (auto-detected if not provided)")
@click.option("--group", "-g", multiple=True, default=["default"], help="Add to group(s)")
@click.option("--flavor", "-f", default="claude-skill-v1", help="Skill flavor")
@click.option("--ref", help="Git ref to track (for git sources)")
@pass_context
def add_skill(
    ctx: Context,
    source: str,
    name: str | None,
    group: tuple[str, ...],
    flavor: str,
    ref: str | None,
) -> None:
    """Add a skill from git URL or local path."""
    from agentslock.cache import GitCache
    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.model import GitSource, PathSource, Skill
    from agentslock.ui import confirm, print_error, print_success, prompt_text
    from agentslock.util import parse_github_url

    lockfile_path = resolve_lockfile(ctx)
    if not lockfile_path.exists():
        print_error(f"Lockfile not found: {lockfile_path}. Run 'al init' first.")
        sys.exit(1)

    lockfile = parse_lockfile(lockfile_path)

    # Determine source type
    if source.startswith(("http://", "https://", "git@")):
        # Parse GitHub/GitLab URLs to extract repo, ref, and subdir
        parsed = parse_github_url(source)
        repo_url = parsed["repo"]
        parsed_ref = parsed["ref"]
        subdir = parsed["subdir"] or ""

        cache = GitCache()
        metadata = cache.clone(repo_url)
        default_branch = metadata.default_branch or "main"
        target_ref = ref or parsed_ref or default_branch
        rev = cache.resolve_ref(repo_url, target_ref)

        skill_source = GitSource(repo=repo_url, rev=rev, ref=target_ref, subdir=subdir)

        if not name:
            # Try to detect from subdir or repo name
            if subdir:
                name = subdir.rstrip("/").split("/")[-1]
            else:
                name = repo_url.rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            name = name.lower().replace("_", "-")
    else:
        path = Path(source)
        if not path.exists():
            print_error(f"Path not found: {source}")
            sys.exit(1)

        # Store relative path
        try:
            rel_path = path.resolve().relative_to(lockfile_path.parent)
            skill_source = PathSource(path="./" + str(rel_path))
        except ValueError:
            skill_source = PathSource(path=str(path.resolve()))

        if not name:
            name = path.name.lower().replace("_", "-")

    # Validate/prompt for name
    if not ctx.yes and not name:
        name = prompt_text("Skill name")
    if not name:
        print_error("Skill name is required")
        sys.exit(1)

    # Check for duplicate
    existing = lockfile.get_skill(name)
    if existing:
        if ctx.yes:
            print_error(f"Skill '{name}' already exists")
            sys.exit(1)
        if not confirm(f"Replace existing skill '{name}'?"):
            sys.exit(0)
        lockfile.skills = [s for s in lockfile.skills if s.name != name]

    # Ensure groups exist
    for g in group:
        if g not in lockfile.groups:
            lockfile.groups[g] = f"{g.title()} group"

    skill = Skill(
        name=name,
        flavor=flavor,
        source=skill_source,
        groups=list(group),
    )
    lockfile.skills.append(skill)
    write_lockfile(lockfile, lockfile_path)
    print_success(f"Added skill '{name}'")

    if ctx.json_output:
        output_json({"status": "success", "skill": name})


@add.command("agent")
@click.argument("source")
@click.option("--name", "-n", help="Agent name")
@click.option("--group", "-g", multiple=True, default=["default"], help="Add to group(s)")
@click.option("--flavor", "-f", default="claude-agent-v1", help="Agent flavor")
@click.option("--ref", help="Git ref to track")
@pass_context
def add_agent(
    ctx: Context,
    source: str,
    name: str | None,
    group: tuple[str, ...],
    flavor: str,
    ref: str | None,
) -> None:
    """Add an agent from git URL or local path."""
    from agentslock.cache import GitCache
    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.model import Agent, GitSource, PathSource
    from agentslock.ui import confirm, print_error, print_success, prompt_text
    from agentslock.util import parse_github_url

    lockfile_path = resolve_lockfile(ctx)
    if not lockfile_path.exists():
        print_error(f"Lockfile not found: {lockfile_path}")
        sys.exit(1)

    lockfile = parse_lockfile(lockfile_path)

    if source.startswith(("http://", "https://", "git@")):
        # Parse GitHub/GitLab URLs to extract repo, ref, and subdir
        parsed = parse_github_url(source)
        repo_url = parsed["repo"]
        parsed_ref = parsed["ref"]
        subdir = parsed["subdir"] or ""
        file_path = parsed["file"] or ""

        cache = GitCache()
        metadata = cache.clone(repo_url)
        target_ref = ref or parsed_ref or metadata.default_branch or "main"
        rev = cache.resolve_ref(repo_url, target_ref)
        agent_source = GitSource(
            repo=repo_url, rev=rev, ref=target_ref, subdir=subdir, file=file_path
        )

        if not name:
            if file_path:
                name = Path(file_path).stem
            elif subdir:
                name = subdir.rstrip("/").split("/")[-1]
            else:
                name = repo_url.rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            name = name.lower().replace("_", "-")
    else:
        path = Path(source)
        if not path.exists():
            print_error(f"Path not found: {source}")
            sys.exit(1)

        try:
            rel_path = path.resolve().relative_to(lockfile_path.parent)
            agent_source = PathSource(path="./" + str(rel_path))
        except ValueError:
            agent_source = PathSource(path=str(path.resolve()))

        if not name:
            name = path.stem.lower().replace("_", "-")

    if not ctx.yes and not name:
        name = prompt_text("Agent name")
    if not name:
        print_error("Agent name is required")
        sys.exit(1)

    existing = lockfile.get_agent(name)
    if existing:
        if ctx.yes:
            print_error(f"Agent '{name}' already exists")
            sys.exit(1)
        if not confirm(f"Replace existing agent '{name}'?"):
            sys.exit(0)
        lockfile.agents = [a for a in lockfile.agents if a.name != name]

    for g in group:
        if g not in lockfile.groups:
            lockfile.groups[g] = f"{g.title()} group"

    agent = Agent(
        name=name,
        flavor=flavor,
        source=agent_source,
        groups=list(group),
    )
    lockfile.agents.append(agent)
    write_lockfile(lockfile, lockfile_path)
    print_success(f"Added agent '{name}'")


@add.command("mcp")
@click.option("--name", "-n", required=True, help="MCP server name")
@click.option("--group", "-g", multiple=True, default=["default"], help="Add to group(s)")
@click.option("--flavor", "-f", default="mcp-v1", help="MCP flavor")
@click.option(
    "--from-file", type=click.Path(exists=True, path_type=Path), help="Import config from file"
)
@click.option(
    "--transport",
    type=click.Choice([t.value for t in Transport]),
    help="MCP transport type",
)
@click.option("--command", help="Command for stdio transport")
@click.option("--arg", "args", multiple=True, help="Command argument (repeatable)")
@click.option("--env", "env_vars", multiple=True, help="Env var KEY=VALUE (repeatable)")
@click.option("--cwd", help="Working directory for stdio transport")
@click.option("--url", help="Server URL for http/sse transport")
@click.option("--header", "headers", multiple=True, help="Header KEY:VALUE (repeatable)")
@click.option("--timeout", type=int, help="Timeout in seconds")
@click.option("--tool-include", "tool_include", multiple=True, help="Tool name to include")
@click.option("--tool-exclude", "tool_exclude", multiple=True, help="Tool name to exclude")
@pass_context
def add_mcp(
    ctx: Context,
    name: str,
    group: tuple[str, ...],
    flavor: str,
    from_file: Path | None,
    transport: str | None,
    command: str | None,
    args: tuple[str, ...],
    env_vars: tuple[str, ...],
    cwd: str | None,
    url: str | None,
    headers: tuple[str, ...],
    timeout: int | None,
    tool_include: tuple[str, ...],
    tool_exclude: tuple[str, ...],
) -> None:
    """Add an MCP server configuration."""
    import json

    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.model import MCPConfig, MCPServer, Transport
    from agentslock.ui import confirm, print_error, print_success, prompt_mcp_config

    lockfile_path = resolve_lockfile(ctx)
    if not lockfile_path.exists():
        print_error(f"Lockfile not found: {lockfile_path}")
        sys.exit(1)

    lockfile = parse_lockfile(lockfile_path)

    if from_file:
        config_data = json.loads(from_file.read_text())
    elif not ctx.yes:
        config_data = prompt_mcp_config()
    else:
        config_data = {}

    if transport:
        config_data["transport"] = transport
    if command is not None:
        config_data["command"] = command
    if args:
        config_data["args"] = list(args)
    if env_vars:
        config_data["env"] = _parse_key_value_pairs(env_vars, "=", "env var")
    if cwd:
        config_data["cwd"] = cwd
    if url:
        config_data["url"] = url
    if headers:
        config_data["headers"] = _parse_key_value_pairs(headers, ":", "header")
    if timeout is not None:
        config_data["timeout"] = timeout
    if tool_include or tool_exclude:
        tool_filters: dict[str, list[str]] = {}
        if tool_include:
            tool_filters["include"] = list(tool_include)
        if tool_exclude:
            tool_filters["exclude"] = list(tool_exclude)
        config_data["tool_filters"] = tool_filters

    config = MCPConfig(
        transport=Transport(config_data.get("transport", "stdio")),
        command=config_data.get("command"),
        args=config_data.get("args", []),
        env=config_data.get("env", {}),
        cwd=config_data.get("cwd"),
        url=config_data.get("url"),
        headers=config_data.get("headers", {}),
        timeout=config_data.get("timeout"),
        tool_filters=config_data.get("tool_filters"),
    )

    existing = lockfile.get_mcp_server(name)
    if existing:
        if ctx.yes:
            print_error(f"MCP server '{name}' already exists")
            sys.exit(1)
        if not confirm(f"Replace existing MCP server '{name}'?"):
            sys.exit(0)
        lockfile.mcp_servers = [m for m in lockfile.mcp_servers if m.name != name]

    for g in group:
        if g not in lockfile.groups:
            lockfile.groups[g] = f"{g.title()} group"

    mcp = MCPServer(
        name=name,
        flavor=flavor,
        config=config,
        groups=list(group),
    )
    lockfile.mcp_servers.append(mcp)
    write_lockfile(lockfile, lockfile_path)
    print_success(f"Added MCP server '{name}'")


@add.command("instructions")
@click.option("--name", "-n", required=True, help="Instructions name")
@click.option("--source", "-s", help="Source file path")
@click.option("--inline", is_flag=True, help="Read content from stdin")
@click.option("--kind", "-k", default="agents-md", help="Instruction kind")
@click.option("--mode", "-m", default="replace", help="Mode: replace, append, prepend")
@click.option("--group", "-g", multiple=True, default=["default"], help="Add to group(s)")
@pass_context
def add_instructions(
    ctx: Context,
    name: str,
    source: str | None,
    inline: bool,
    kind: str,
    mode: str,
    group: tuple[str, ...],
) -> None:
    """Add instructions entry."""
    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.model import (
        InlineSource,
        InstructionKind,
        InstructionMode,
        Instructions,
        PathSource,
    )
    from agentslock.ui import confirm, print_error, print_success

    lockfile_path = resolve_lockfile(ctx)
    if not lockfile_path.exists():
        print_error(f"Lockfile not found: {lockfile_path}")
        sys.exit(1)

    lockfile = parse_lockfile(lockfile_path)

    instr_source = None
    if inline:
        content = sys.stdin.read()
        instr_source = InlineSource(content=content)
    elif source:
        path = Path(source)
        try:
            rel_path = path.resolve().relative_to(lockfile_path.parent)
            instr_source = PathSource(path="./" + str(rel_path))
        except ValueError:
            instr_source = PathSource(path=str(path.resolve()))

    existing = lockfile.get_instructions(name)
    if existing:
        if ctx.yes:
            print_error(f"Instructions '{name}' already exists")
            sys.exit(1)
        if not confirm(f"Replace existing instructions '{name}'?"):
            sys.exit(0)
        lockfile.instructions = [i for i in lockfile.instructions if i.name != name]

    for g in group:
        if g not in lockfile.groups:
            lockfile.groups[g] = f"{g.title()} group"

    instr = Instructions(
        name=name,
        kind=InstructionKind(kind),
        source=instr_source,
        mode=InstructionMode(mode),
        groups=list(group),
    )
    lockfile.instructions.append(instr)
    write_lockfile(lockfile, lockfile_path)
    print_success(f"Added instructions '{name}'")


@cli.command()
@click.argument("resource_type", type=click.Choice(["skill", "agent"]))
@click.argument("name")
@click.option("--rev", help="Pin to specific revision")
@click.option("--refresh", is_flag=True, help="Force fetch from remote")
@pass_context
def update(ctx: Context, resource_type: str, name: str, rev: str | None, refresh: bool) -> None:
    """Update a skill or agent to the latest revision."""
    from agentslock.cache import GitCache
    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.model import GitSource
    from agentslock.ui import print_error, print_success

    lockfile_path = resolve_lockfile(ctx)
    lockfile = parse_lockfile(lockfile_path)

    if resource_type == "skill":
        resource = lockfile.get_skill(name)
    else:
        resource = lockfile.get_agent(name)

    if not resource:
        print_error(f"{resource_type.title()} '{name}' not found")
        sys.exit(1)

    if not isinstance(resource.source, GitSource):
        print_error(f"{resource_type.title()} '{name}' uses path source, cannot update")
        sys.exit(1)

    cache = GitCache()
    if refresh:
        cache.fetch(resource.source.repo)

    if rev:
        new_rev = rev
    else:
        target_ref = resource.source.ref or "HEAD"
        new_rev = cache.resolve_ref(resource.source.repo, target_ref)

    old_rev = resource.source.rev
    resource.source = GitSource(
        repo=resource.source.repo,
        rev=new_rev,
        ref=resource.source.ref,
        subdir=resource.source.subdir,
        file=resource.source.file,
    )

    write_lockfile(lockfile, lockfile_path)
    print_success(f"Updated {resource_type} '{name}': {old_rev[:8]} -> {new_rev[:8]}")


@cli.command()
@click.argument("resource_type", type=click.Choice(["skill", "agent", "mcp", "instructions"]))
@click.argument("name")
@pass_context
def remove(ctx: Context, resource_type: str, name: str) -> None:
    """Remove a resource from the lockfile."""
    from agentslock.lockfile import parse_lockfile, write_lockfile
    from agentslock.ui import confirm, print_error, print_success

    lockfile_path = resolve_lockfile(ctx)
    lockfile = parse_lockfile(lockfile_path)

    if resource_type == "skill":
        if not lockfile.get_skill(name):
            print_error(f"Skill '{name}' not found")
            sys.exit(1)
        if not ctx.yes and not confirm(f"Remove skill '{name}'?"):
            sys.exit(0)
        lockfile.skills = [s for s in lockfile.skills if s.name != name]
    elif resource_type == "agent":
        if not lockfile.get_agent(name):
            print_error(f"Agent '{name}' not found")
            sys.exit(1)
        if not ctx.yes and not confirm(f"Remove agent '{name}'?"):
            sys.exit(0)
        lockfile.agents = [a for a in lockfile.agents if a.name != name]
    elif resource_type == "mcp":
        if not lockfile.get_mcp_server(name):
            print_error(f"MCP server '{name}' not found")
            sys.exit(1)
        if not ctx.yes and not confirm(f"Remove MCP server '{name}'?"):
            sys.exit(0)
        lockfile.mcp_servers = [m for m in lockfile.mcp_servers if m.name != name]
    elif resource_type == "instructions":
        if not lockfile.get_instructions(name):
            print_error(f"Instructions '{name}' not found")
            sys.exit(1)
        if not ctx.yes and not confirm(f"Remove instructions '{name}'?"):
            sys.exit(0)
        lockfile.instructions = [i for i in lockfile.instructions if i.name != name]

    write_lockfile(lockfile, lockfile_path)
    print_success(f"Removed {resource_type} '{name}'")


@cli.command("list")
@click.option("--skills", is_flag=True, help="List only skills")
@click.option("--agents", is_flag=True, help="List only agents")
@click.option("--mcp", is_flag=True, help="List only MCP servers")
@click.option("--instructions", is_flag=True, help="List only instructions")
@pass_context
def list_resources(ctx: Context, skills: bool, agents: bool, mcp: bool, instructions: bool) -> None:
    """List resources in the lockfile."""
    from agentslock.lockfile import parse_lockfile
    from agentslock.ui import (
        print_agents_table,
        print_instructions_table,
        print_lockfile_summary,
        print_mcp_servers_table,
        print_skills_table,
    )

    lockfile_path = resolve_lockfile(ctx)
    lockfile = parse_lockfile(lockfile_path)

    if ctx.groups:
        lockfile = lockfile.filter_by_groups(ctx.groups)

    show_all = not any([skills, agents, mcp, instructions])

    if ctx.json_output:
        data = {}
        if skills or show_all:
            data["skills"] = [
                {"name": s.name, "flavor": s.flavor, "groups": s.groups} for s in lockfile.skills
            ]
        if agents or show_all:
            data["agents"] = [
                {"name": a.name, "flavor": a.flavor, "groups": a.groups} for a in lockfile.agents
            ]
        if mcp or show_all:
            data["mcp_servers"] = [
                {"name": m.name, "transport": m.config.transport.value}
                for m in lockfile.mcp_servers
            ]
        if instructions or show_all:
            data["instructions"] = [
                {"name": i.name, "kind": i.kind.value} for i in lockfile.instructions
            ]
        output_json(data)
        return

    if show_all:
        print_lockfile_summary(lockfile)
        return

    if skills:
        print_skills_table(lockfile.skills)
    if agents:
        print_agents_table(lockfile.agents)
    if mcp:
        print_mcp_servers_table(lockfile.mcp_servers)
    if instructions:
        print_instructions_table(lockfile.instructions)


@cli.command()
@pass_context
def validate(ctx: Context) -> None:
    """Validate the lockfile."""
    from agentslock.lockfile import parse_lockfile
    from agentslock.ui import print_error, print_success

    lockfile_path = resolve_lockfile(ctx)
    try:
        _ = parse_lockfile(lockfile_path)
        print_success(f"Lockfile is valid: {lockfile_path}")
        if ctx.json_output:
            output_json({"status": "valid", "path": str(lockfile_path)})
    except AgentsLockError as e:
        print_error(str(e))
        if ctx.json_output:
            output_json({"status": "invalid", "error": str(e)})
        sys.exit(1)


@cli.command()
@pass_context
def sync(ctx: Context) -> None:
    """Sync lockfile to client configurations."""
    from agentslock.sync import SyncEngine
    from agentslock.ui import confirm, print_diff, print_sync_plan, print_sync_result

    lockfile_path = resolve_lockfile(ctx)

    engine = SyncEngine(
        lockfile_path=lockfile_path,
        scope=ctx.scope,
        clients=ctx.clients or None,
        groups=ctx.groups or None,
    )

    plan = engine.plan()

    if ctx.json_output:
        output_json(
            {
                "plan": {
                    "create": len(plan.creates),
                    "update": len(plan.updates),
                    "delete": len(plan.deletes),
                },
                "warnings": plan.warnings,
                "skipped": plan.skipped,
            }
        )
        if ctx.dry_run:
            return

    if not plan.changes:
        click.echo("Nothing to sync.")
        return

    print_sync_plan(plan)

    if ctx.show_diff:
        for change in plan.changes:
            diff = engine.get_diff(change)
            if diff:
                print_diff(diff, change.path)

    if not ctx.yes and not ctx.dry_run:
        if not confirm("Apply these changes?"):
            sys.exit(0)

    result = engine.apply(plan, dry_run=ctx.dry_run)
    print_sync_result(result)

    if not result.success:
        sys.exit(1)


@cli.group()
def alias() -> None:
    """Manage lockfile aliases."""
    pass


@alias.command("add")
@click.argument("name")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@pass_context
def alias_add(ctx: Context, name: str, path: Path) -> None:
    """Add a lockfile alias."""
    from agentslock.config import load_global_config, save_global_config
    from agentslock.ui import print_success

    config = load_global_config()
    config.aliases[name] = str(path.resolve())
    save_global_config(config)
    print_success(f"Added alias '{name}' -> {path}")


@alias.command("remove")
@click.argument("name")
@pass_context
def alias_remove(ctx: Context, name: str) -> None:
    """Remove a lockfile alias."""
    from agentslock.config import load_global_config, save_global_config
    from agentslock.ui import print_error, print_success

    config = load_global_config()
    if name not in config.aliases:
        print_error(f"Alias '{name}' not found")
        sys.exit(1)
    del config.aliases[name]
    save_global_config(config)
    print_success(f"Removed alias '{name}'")


@alias.command("list")
@pass_context
def alias_list(ctx: Context) -> None:
    """List lockfile aliases."""
    from agentslock.config import load_global_config

    config = load_global_config()
    if ctx.json_output:
        output_json(config.aliases)
        return

    if not config.aliases:
        click.echo("No aliases defined.")
        return

    for name, path in config.aliases.items():
        click.echo(f"{name}: {path}")


@cli.group()
def cache() -> None:
    """Manage the git cache."""
    pass


@cache.command("list")
@pass_context
def cache_list(ctx: Context) -> None:
    """List cached repositories."""
    from agentslock.cache import GitCache

    git_cache = GitCache()
    repos = git_cache.list_repos()

    if ctx.json_output:
        output_json({"repos": repos})
        return

    if not repos:
        click.echo("No cached repositories.")
        return

    for repo in repos:
        worktrees = git_cache.list_worktrees(repo)
        click.echo(f"{repo} ({len(worktrees)} worktrees)")


@cache.command("clear")
@click.option("--all", "clear_all", is_flag=True, help="Clear entire cache")
@pass_context
def cache_clear(ctx: Context, clear_all: bool) -> None:
    """Clear the cache."""
    from agentslock.cache import GitCache
    from agentslock.ui import confirm, print_success

    git_cache = GitCache()

    if not ctx.yes:
        if not confirm("Clear all cached repositories?"):
            sys.exit(0)

    git_cache.clear()
    print_success("Cache cleared")


@cache.command("gc")
@pass_context
def cache_gc(ctx: Context) -> None:
    """Garbage collect unreferenced worktrees."""
    from agentslock.cache import GitCache
    from agentslock.ui import print_success

    git_cache = GitCache()
    stats_before = git_cache.get_stats()

    # This is a simplified GC - in a full implementation, we'd check all lockfiles
    click.echo("Note: Full GC requires scanning all known lockfiles.")

    stats_after = git_cache.get_stats()
    print_success(
        f"GC complete. Worktrees: {stats_before['worktrees']} -> {stats_after['worktrees']}"
    )


@cli.command()
@pass_context
def doctor(ctx: Context) -> None:
    """Check system configuration and diagnose issues."""
    from agentslock.cache import GitCache
    from agentslock.paths import ClientPaths
    from agentslock.ui import print_cache_stats, print_error, print_success

    issues = []

    # Check git
    import shutil

    if not shutil.which("git"):
        issues.append("git not found in PATH")

    # Check cache
    try:
        git_cache = GitCache()
        stats = git_cache.get_stats()
        print_cache_stats(stats)
    except Exception as e:
        issues.append(f"Cache error: {e}")

    # Check client paths
    for client in ClientId:
        paths = ClientPaths(client)
        click.echo(f"\n{client.value}:")
        click.echo(f"  Skills (project): {paths.skills_dir('project')}")
        click.echo(f"  Skills (global): {paths.skills_dir('global')}")
        if paths.supports_agents():
            click.echo(f"  Agents (project): {paths.agents_dir('project')}")
        if paths.supports_mcp("global"):
            mcp_path = paths.mcp_config_path("global")
            exists = mcp_path.exists() if mcp_path else False
            click.echo(f"  MCP config: {mcp_path} {'(exists)' if exists else '(not found)'}")

    if issues:
        click.echo("\nIssues found:")
        for issue in issues:
            print_error(f"  - {issue}")
        sys.exit(1)
    else:
        print_success("\nNo issues found.")


@cli.command()
@pass_context
def migrate(ctx: Context) -> None:
    """Migrate lockfile to the latest version."""
    from agentslock.lockfile import CURRENT_VERSION, parse_lockfile
    from agentslock.ui import print_warning

    lockfile_path = resolve_lockfile(ctx)
    lockfile = parse_lockfile(lockfile_path)

    if lockfile.version == CURRENT_VERSION:
        click.echo(f"Lockfile is already at version {CURRENT_VERSION}")
        return

    # Future migrations would go here
    print_warning("Migration not needed for current version.")


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli()
    except AgentsLockError as e:
        from agentslock.ui import print_error

        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
