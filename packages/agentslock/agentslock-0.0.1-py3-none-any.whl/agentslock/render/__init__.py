"""Client configuration renderers for agents.lock."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from agentslock.model import ClientId
from agentslock.render.base import BaseRenderer, RenderResult
from agentslock.render.claude import ClaudeRenderer
from agentslock.render.codex import CodexRenderer
from agentslock.render.copilot import CopilotRenderer
from agentslock.render.gemini import GeminiRenderer

if TYPE_CHECKING:
    from agentslock.model import Lockfile
    from agentslock.paths import Scope
    from agentslock.resolve import SourceResolver

__all__ = [
    "BaseRenderer",
    "RenderResult",
    "ClaudeRenderer",
    "CodexRenderer",
    "GeminiRenderer",
    "CopilotRenderer",
    "get_renderer",
    "render_all",
]


def get_renderer(
    client: ClientId,
    lockfile: "Lockfile",
    resolver: "SourceResolver",
    scope: "Scope",
    project_root: Path | None = None,
) -> BaseRenderer:
    renderer_cls = {
        ClientId.CLAUDE: ClaudeRenderer,
        ClientId.CODEX: CodexRenderer,
        ClientId.GEMINI: GeminiRenderer,
        ClientId.COPILOT: CopilotRenderer,
    }.get(client)

    if renderer_cls is None:
        raise ValueError(f"No renderer for client: {client}")

    return renderer_cls(lockfile, resolver, scope, project_root)


def render_all(
    lockfile: "Lockfile",
    resolver: "SourceResolver",
    scope: "Scope",
    clients: list[ClientId] | None = None,
    project_root: Path | None = None,
) -> dict[ClientId, RenderResult]:
    if clients is None:
        clients = lockfile.defaults.clients

    results = {}
    for client in clients:
        renderer = get_renderer(client, lockfile, resolver, scope, project_root)
        results[client] = renderer.render()

    return results
