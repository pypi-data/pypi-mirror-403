"""Interactive UI flows for agents.lock CLI."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from agentslock.model import ClientId, InstructionKind, InstructionMode, Transport

if TYPE_CHECKING:
    from agentslock.model import Lockfile
    from agentslock.sync import SyncPlan, SyncResult

console = Console()


def print_error(message: str) -> None:
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def print_info(message: str) -> None:
    console.print(f"[blue]{message}[/blue]")


def confirm(message: str, default: bool = False) -> bool:
    return Confirm.ask(message, default=default)


def prompt_text(message: str, default: str = "") -> str:
    return Prompt.ask(message, default=default)


def select_one(message: str, choices: list[str], default: str | None = None) -> str:
    console.print(f"\n[bold]{message}[/bold]")
    for i, choice in enumerate(choices, 1):
        marker = "*" if choice == default else " "
        console.print(f"  {marker}[cyan]{i}.[/cyan] {choice}")

    while True:
        response = Prompt.ask("Enter number", default="1" if default else "")
        response = response or ""
        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print_error(f"Please enter a number between 1 and {len(choices)}")


def select_multiple(message: str, choices: list[str], defaults: list[str] | None = None) -> list[str]:
    defaults = defaults or []
    console.print(f"\n[bold]{message}[/bold] (comma-separated numbers, or 'all')")
    for i, choice in enumerate(choices, 1):
        marker = "[x]" if choice in defaults else "[ ]"
        console.print(f"  {marker} [cyan]{i}.[/cyan] {choice}")

    while True:
        response = Prompt.ask("Enter numbers", default="all" if not defaults else "")
        response = response or ""
        if response.lower() == "all":
            return choices
        try:
            indices = [int(x.strip()) - 1 for x in response.split(",")]
            selected = [choices[i] for i in indices if 0 <= i < len(choices)]
            if selected:
                return selected
        except ValueError:
            pass
        print_error("Please enter comma-separated numbers or 'all'")


def select_clients(default: list[ClientId] | None = None) -> list[ClientId]:
    choices = [c.value for c in ClientId]
    defaults = [c.value for c in (default or [])]
    selected = select_multiple("Select target clients:", choices, defaults)
    return [ClientId.from_str(s) for s in selected]


def select_groups(available: list[str], default: list[str] | None = None) -> list[str]:
    return select_multiple("Select groups:", available, default)


def prompt_mcp_config() -> dict[str, Any]:
    transport = select_one(
        "Select transport type:",
        [t.value for t in Transport],
        Transport.STDIO.value,
    )

    config: dict[str, Any] = {"transport": transport}

    if transport == Transport.STDIO.value:
        config["command"] = prompt_text("Command to execute")
        args_str = prompt_text("Arguments (space-separated)", "")
        if args_str:
            config["args"] = args_str.split()

        env_str = prompt_text("Environment variables (KEY=VALUE, comma-separated)", "")
        if env_str:
            env = {}
            for pair in env_str.split(","):
                if "=" in pair:
                    k, v = pair.strip().split("=", 1)
                    env[k.strip()] = v.strip()
            config["env"] = env

        cwd = prompt_text("Working directory (optional)", "")
        if cwd:
            config["cwd"] = cwd
    else:
        config["url"] = prompt_text("Server URL")
        headers_str = prompt_text("Headers (KEY:VALUE, comma-separated)", "")
        if headers_str:
            headers = {}
            for pair in headers_str.split(","):
                if ":" in pair:
                    k, v = pair.strip().split(":", 1)
                    headers[k.strip()] = v.strip()
            config["headers"] = headers

    timeout_str = prompt_text("Timeout in seconds (optional)", "")
    if timeout_str:
        try:
            config["timeout"] = int(timeout_str)
        except ValueError:
            pass

    include_str = prompt_text("Tool include list (comma-separated, optional)", "")
    exclude_str = prompt_text("Tool exclude list (comma-separated, optional)", "")
    include = [item.strip() for item in include_str.split(",") if item.strip()]
    exclude = [item.strip() for item in exclude_str.split(",") if item.strip()]
    if include or exclude:
        tool_filters: dict[str, list[str]] = {}
        if include:
            tool_filters["include"] = include
        if exclude:
            tool_filters["exclude"] = exclude
        config["tool_filters"] = tool_filters

    return config


def prompt_instructions_config() -> dict[str, Any]:
    kind = select_one(
        "Select instruction kind:",
        [k.value for k in InstructionKind],
        InstructionKind.AGENTS_MD.value,
    )

    config: dict[str, Any] = {"kind": kind}

    if kind == InstructionKind.CUSTOM.value:
        config["output_path"] = prompt_text("Output path (relative to project root)")

    mode = select_one(
        "Select mode:",
        [m.value for m in InstructionMode],
        InstructionMode.REPLACE.value,
    )
    config["mode"] = mode

    return config


def print_sync_plan(plan: SyncPlan) -> None:
    summary = plan.summary()

    table = Table(title="Sync Plan Summary", show_header=True)
    table.add_column("Action", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Create", str(summary["create"]), style="green")
    table.add_row("Update", str(summary["update"]), style="yellow")
    table.add_row("Delete", str(summary["delete"]), style="red")

    console.print(table)

    if plan.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in plan.warnings:
            console.print(f"  - {warning}")

    if plan.skipped:
        console.print("\n[dim]Skipped:[/dim]")
        for skipped in plan.skipped[:5]:
            console.print(f"  - {skipped}")
        if len(plan.skipped) > 5:
            console.print(f"  ... and {len(plan.skipped) - 5} more")


def print_diff(diff: str, path: Path) -> None:
    console.print(f"\n[bold]Changes to {path}:[/bold]")
    syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, border_style="dim"))


def print_sync_result(result: SyncResult) -> None:
    if result.success:
        print_success(f"Sync completed: {len(result.applied)} changes applied")
    else:
        print_error(f"Sync failed: {len(result.failed)} errors")
        for change, error in result.failed:
            console.print(f"  - {change.path}: {error}")

    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")


def print_lockfile_summary(lockfile: Lockfile) -> None:
    table = Table(title=f"Lockfile: {lockfile.project.name}", show_header=True)
    table.add_column("Resource", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Skills", str(len(lockfile.skills)))
    table.add_row("Agents", str(len(lockfile.agents)))
    table.add_row("MCP Servers", str(len(lockfile.mcp_servers)))
    table.add_row("Instructions", str(len(lockfile.instructions)))

    console.print(table)

    console.print(f"\n[dim]Clients:[/dim] {', '.join(c.value for c in lockfile.defaults.clients)}")
    console.print(f"[dim]Groups:[/dim] {', '.join(lockfile.groups.keys())}")


def print_resource_table(
    resources: list[Any],
    resource_type: str,
    columns: list[tuple[str, str]],
) -> None:
    if not resources:
        console.print(f"[dim]No {resource_type} found.[/dim]")
        return

    table = Table(title=resource_type.title(), show_header=True)
    for name, style in columns:
        table.add_column(name, style=style)

    for r in resources:
        row = []
        for col_name, _ in columns:
            attr = col_name.lower().replace(" ", "_")
            value = getattr(r, attr, None)
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif isinstance(value, Enum):
                value = value.value
            elif value is None:
                value = ""
            row.append(str(value))
        table.add_row(*row)

    console.print(table)


def print_skills_table(skills: list) -> None:
    print_resource_table(
        skills,
        "skills",
        [
            ("Name", "cyan"),
            ("Flavor", ""),
            ("Groups", "dim"),
            ("Enabled", ""),
        ],
    )


def print_agents_table(agents: list) -> None:
    print_resource_table(
        agents,
        "agents",
        [
            ("Name", "cyan"),
            ("Flavor", ""),
            ("Groups", "dim"),
            ("Enabled", ""),
        ],
    )


def print_mcp_servers_table(mcp_servers: list) -> None:
    table = Table(title="MCP Servers", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Transport", style="")
    table.add_column("Groups", style="dim")
    table.add_column("Enabled", style="")

    for mcp in mcp_servers:
        table.add_row(
            mcp.name,
            mcp.config.transport.value,
            ", ".join(mcp.groups),
            str(mcp.enabled),
        )

    console.print(table)


def print_instructions_table(instructions: list) -> None:
    table = Table(title="Instructions", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Kind", style="")
    table.add_column("Mode", style="")
    table.add_column("Groups", style="dim")

    for instr in instructions:
        table.add_row(
            instr.name,
            instr.kind.value,
            instr.mode.value,
            ", ".join(instr.groups),
        )

    console.print(table)


def print_cache_stats(stats: dict[str, Any]) -> None:
    table = Table(title="Cache Statistics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Cache Directory", str(stats["cache_dir"]))
    table.add_row("Repositories", str(stats["repos"]))
    table.add_row("Worktrees", str(stats["worktrees"]))

    console.print(table)
